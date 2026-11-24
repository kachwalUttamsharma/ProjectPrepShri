import json

import pytest

from exercises import *


class FakeLLM:
    """Scripted model: returns replies in order and records the messages it saw."""

    def __init__(self, replies):
        self.replies = list(replies)
        self.calls = []

    def __call__(self, messages):
        self.calls.append([dict(m) for m in messages])
        return self.replies.pop(0)


def call(name, **args):
    return json.dumps({"tool": name, "args": args})


def final(text):
    return json.dumps({"final": text})


SCHEMA = {
    "email": {"type": "string", "required": True},
    "limit": {"type": "integer", "default": 10},
    "ratio": {"type": "number"},
    "flag": {"type": "boolean"},
}


# 1 validate_args
def test_validate_args_ok_and_defaults():
    assert validate_args(SCHEMA, {"email": "a@b.c"}) == {"email": "a@b.c", "limit": 10}
    out = validate_args(SCHEMA, {"email": "a", "limit": 3, "ratio": 1, "flag": False})
    assert out == {"email": "a", "limit": 3, "ratio": 1, "flag": False}


def test_validate_args_errors():
    with pytest.raises(ToolError, match="email"):
        validate_args(SCHEMA, {})
    with pytest.raises(ToolError, match="bogus"):
        validate_args(SCHEMA, {"email": "a", "bogus": 1})
    with pytest.raises(ToolError):
        validate_args(SCHEMA, {"email": 5})
    with pytest.raises(ToolError):
        validate_args(SCHEMA, {"email": "a", "limit": "3"})
    with pytest.raises(ToolError):
        validate_args(SCHEMA, "nope")


def test_validate_args_bool_is_not_int():
    with pytest.raises(ToolError):
        validate_args(SCHEMA, {"email": "a", "limit": True})
    with pytest.raises(ToolError):
        validate_args(SCHEMA, {"email": "a", "ratio": True})
    with pytest.raises(ToolError):
        validate_args(SCHEMA, {"email": "a", "flag": 1})
    assert validate_args(SCHEMA, {"email": "a", "ratio": 2.5})["ratio"] == 2.5


# 2 registry
def make_registry():
    reg = ToolRegistry()
    reg.register(Tool("zeta", "Last tool", {"x": {"type": "integer", "required": True},
                                            "y": {"type": "string"}}, lambda x, y="": x))
    reg.register(Tool("alpha", "First tool", {}, lambda: "hi"))
    return reg


def test_registry_basics():
    reg = make_registry()
    assert reg.names() == ["alpha", "zeta"]
    assert reg.get("alpha").description == "First tool"
    with pytest.raises(ToolError, match="unknown tool: nope"):
        reg.get("nope")
    with pytest.raises(ValueError):
        reg.register(Tool("alpha", "dup", {}, lambda: 1))


def test_registry_describe():
    assert make_registry().describe() == (
        "- alpha(): First tool\n"
        "- zeta(x: integer, y: string?): Last tool"
    )


# 3 parse_action
def test_parse_action_tool_and_final():
    assert parse_action('{"tool": "t", "args": {"a": 1}}') == ("tool", ("t", {"a": 1}))
    assert parse_action('{"tool": "t"}') == ("tool", ("t", {}))
    assert parse_action('{"final": "done"}') == ("final", "done")


def test_parse_action_fenced():
    text = '```json\n{"final": "ok"}\n```'
    assert parse_action(text) == ("final", "ok")
    assert parse_action('```\n{"tool": "t"}\n```') == ("tool", ("t", {}))


@pytest.mark.parametrize("bad", [
    "not json", "[1, 2]", '{"hello": 1}', '{"tool": 5}', '{"tool": "t", "args": [1]}', "",
])
def test_parse_action_bad(bad):
    with pytest.raises(ToolError):
        parse_action(bad)


# 4 run_tool
def test_run_tool_success_and_defaults():
    reg = make_registry()
    assert run_tool(reg, "zeta", {"x": 7}) == {"ok": True, "result": 7}
    assert run_tool(reg, "alpha", {}) == {"ok": True, "result": "hi"}


def test_run_tool_errors_never_raise():
    reg = make_registry()
    reg.register(Tool("boom", "explodes", {}, lambda: 1 / 0))
    r = run_tool(reg, "nope", {})
    assert r["ok"] is False and "unknown tool" in r["error"]
    r = run_tool(reg, "zeta", {"x": "bad"})
    assert r["ok"] is False and "x" in r["error"]
    r = run_tool(reg, "boom", {})
    assert r["ok"] is False and "tool failed" in r["error"] and "ZeroDivisionError" in r["error"]


def test_run_tool_allow_list():
    reg = make_registry()
    r = run_tool(reg, "zeta", {"x": 1}, allowed={"alpha"})
    assert r["ok"] is False and "not allowed" in r["error"]
    assert run_tool(reg, "alpha", {}, allowed={"alpha"})["ok"] is True


# 5 is_read_only_sql
@pytest.mark.parametrize("sql", [
    "SELECT * FROM customers",
    "  select id from orders where status = 'x';  ",
    "SELECT count(*) FROM orders\nWHERE total_cents > 5",
])
def test_read_only_true(sql):
    assert is_read_only_sql(sql) is True


@pytest.mark.parametrize("sql", [
    "DELETE FROM orders",
    "UPDATE customers SET plan='pro'",
    "SELECT 1; DROP TABLE orders",
    "DROP TABLE orders",
    "INSERT INTO orders VALUES (1,1,1,'x','y')",
    "SELECT 1; SELECT 2",
    "PRAGMA table_info(orders)",
    "WITH x AS (SELECT 1) DELETE FROM orders",
    "",
    "SELECT * FROM t WHERE a = 1 UNION SELECT 1 -- ; drop",
])
def test_read_only_false(sql):
    assert is_read_only_sql(sql) is False


def test_read_only_word_boundary():
    # 'updated_at' / 'created' are column names, not the write keywords
    assert is_read_only_sql("SELECT created, updated_at FROM orders") is True


# 6 data layer
def test_lookup_customer():
    conn = seed_crm_db()
    assert lookup_customer(conn, "ada@example.com") == {
        "id": 1, "name": "Ada Lovelace", "email": "ada@example.com", "plan": "pro"}
    assert lookup_customer(conn, "ADA@Example.com")["id"] == 1
    assert lookup_customer(conn, "nobody@example.com") is None


def test_lookup_customer_is_injection_safe():
    conn = seed_crm_db()
    assert lookup_customer(conn, "x' OR '1'='1") is None
    assert conn.execute("SELECT count(*) FROM customers").fetchone()[0] == 2


def test_list_orders():
    conn = seed_crm_db()
    rows = list_orders(conn, 1)
    assert [r["id"] for r in rows] == [12, 11, 10]
    assert set(rows[0]) == {"id", "total_cents", "status", "created"}
    assert [r["id"] for r in list_orders(conn, 1, status="shipped")] == [10]
    assert [r["id"] for r in list_orders(conn, 1, limit=2)] == [12, 11]
    assert list_orders(conn, 999) == []


def test_run_readonly_query():
    conn = seed_crm_db()
    rows = run_readonly_query(conn, "SELECT name FROM customers ORDER BY id")
    assert rows == [{"name": "Ada Lovelace"}, {"name": "Grace Hopper"}]
    assert len(run_readonly_query(conn, "SELECT * FROM orders", max_rows=2)) == 2
    with pytest.raises(ToolError, match="SELECT"):
        run_readonly_query(conn, "DELETE FROM orders")
    assert conn.execute("SELECT count(*) FROM orders").fetchone()[0] == 4


# 7 registry
def test_build_crm_registry():
    conn = seed_crm_db()
    reg = build_crm_registry(conn)
    assert reg.names() == ["list_orders", "lookup_customer", "run_query"]
    assert run_tool(reg, "lookup_customer", {"email": "grace@example.com"})["result"]["id"] == 2
    r = run_tool(reg, "list_orders", {"customer_id": 1, "status": "refunded"})
    assert [o["id"] for o in r["result"]] == [11]
    assert len(run_tool(reg, "list_orders", {"customer_id": 1})["result"]) == 3
    assert run_tool(reg, "list_orders", {"customer_id": "1"})["ok"] is False
    assert run_tool(reg, "run_query", {"sql": "SELECT count(*) AS n FROM orders"})["result"] == [{"n": 4}]
    assert run_tool(reg, "run_query", {"sql": "DROP TABLE orders"})["ok"] is False
    assert "lookup_customer(email: string)" in reg.describe()


# 8 agent loop
def test_agent_direct_final():
    llm = FakeLLM([final("Hello!")])
    res = run_agent(llm, make_registry(), "hi")
    assert (res.answer, res.steps, res.stopped_reason, res.trace) == ("Hello!", 1, "final", [])
    assert llm.calls[0] == [{"role": "user", "content": "hi"}]


def test_agent_multi_step_crm():
    reg = build_crm_registry(seed_crm_db())
    llm = FakeLLM([
        call("lookup_customer", email="ada@example.com"),
        call("list_orders", customer_id=1, status="pending"),
        final("Ada has 1 pending order (#12)."),
    ])
    res = run_agent(llm, reg, "Any pending orders for ada@example.com?")
    assert res.stopped_reason == "final" and res.steps == 3
    assert res.answer == "Ada has 1 pending order (#12)."
    assert [t[0] for t in res.trace] == ["lookup_customer", "list_orders"]
    assert res.trace[0][1] == {"email": "ada@example.com"}
    assert res.trace[1][2]["result"][0]["id"] == 12
    # model saw tool result as a user message on the next call
    last = llm.calls[1][-1]
    assert last["role"] == "user" and last["content"].startswith("TOOL_RESULT: ")
    assert json.loads(last["content"][len("TOOL_RESULT: "):])["result"]["id"] == 1
    assert [m["role"] for m in llm.calls[2]] == ["user", "assistant", "user", "assistant", "user"]


def test_agent_max_steps():
    llm = FakeLLM([call("alpha")] * 10)
    res = run_agent(llm, make_registry(), "loop forever", max_steps=3)
    assert res.answer is None and res.stopped_reason == "max_steps"
    assert res.steps == 3 and len(llm.calls) == 3 and len(res.trace) == 3


def test_agent_recovers_from_bad_json_and_tool_errors():
    llm = FakeLLM([
        "I think I should look it up",             # not JSON
        call("nope"),                               # unknown tool
        call("zeta", x="seven"),                    # bad arg type
        call("zeta", x=7),
        final("done"),
    ])
    res = run_agent(llm, make_registry(), "q")
    assert res.answer == "done" and res.steps == 5
    assert llm.calls[1][-1]["content"].startswith("ERROR: ")
    assert "unknown tool" in llm.calls[2][-1]["content"]
    assert "x" in llm.calls[3][-1]["content"]
    assert [t[2]["ok"] for t in res.trace] == [False, False, True]


def test_agent_respects_allow_list():
    llm = FakeLLM([call("zeta", x=1), final("sorry")])
    res = run_agent(llm, make_registry(), "q", allowed={"alpha"})
    assert res.trace[0][2]["ok"] is False
    assert "not allowed" in res.trace[0][2]["error"]
    assert res.answer == "sorry"


def test_agent_cannot_be_used_to_write_data():
    conn = seed_crm_db()
    reg = build_crm_registry(conn)
    llm = FakeLLM([call("run_query", sql="DELETE FROM orders"), final("cannot do that")])
    res = run_agent(llm, reg, "delete everything")
    assert res.trace[0][2]["ok"] is False
    assert conn.execute("SELECT count(*) FROM orders").fetchone()[0] == 4
