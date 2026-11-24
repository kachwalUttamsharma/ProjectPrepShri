"""Project 4: tool-calling agent. Read lesson.md first.

Protocol (the model's reply is ALWAYS one JSON object as text):
    {"tool": "<name>", "args": {...}}     -> call a tool
    {"final": "<answer for the customer>"} -> finish

`llm` is any callable: llm(messages: list[dict]) -> str, where each message is
{"role": "user" | "assistant", "content": str}. Tests pass a FakeLLM; no network.
"""
from dataclasses import dataclass, field
import json
import re
import sqlite3
from typing import Any, Callable


class ToolError(Exception):
    """Raised for any problem the MODEL should be told about (bad args, unknown tool...)."""


@dataclass
class Tool:
    name: str
    description: str
    parameters: dict  # {"arg": {"type": "string"|"integer"|"number"|"boolean", "required": bool, "default": any}}
    func: Callable[..., Any]


@dataclass
class AgentResult:
    answer: str | None
    steps: int  # number of LLM calls made
    stopped_reason: str  # "final" or "max_steps"
    trace: list = field(default_factory=list)  # list of (tool_name, args, observation_dict)


def seed_crm_db() -> sqlite3.Connection:
    """PROVIDED. In-memory CRM with customers and orders."""
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.executescript(
        """
        CREATE TABLE customers (id INTEGER PRIMARY KEY, name TEXT, email TEXT UNIQUE, plan TEXT);
        CREATE TABLE orders (id INTEGER PRIMARY KEY, customer_id INTEGER, total_cents INTEGER,
                             status TEXT, created TEXT);
        INSERT INTO customers VALUES (1, 'Ada Lovelace', 'ada@example.com', 'pro');
        INSERT INTO customers VALUES (2, 'Grace Hopper', 'grace@example.com', 'free');
        INSERT INTO orders VALUES (10, 1, 5000, 'shipped', '2026-01-03');
        INSERT INTO orders VALUES (11, 1, 1200, 'refunded', '2026-02-10');
        INSERT INTO orders VALUES (12, 1, 9900, 'pending', '2026-03-01');
        INSERT INTO orders VALUES (13, 2, 700, 'shipped', '2026-02-20');
        """
    )
    return conn


# ---------------------------------------------------------------- 1
def validate_args(schema: dict, args: dict) -> dict:
    """Validate `args` against `schema` and return a cleaned copy.

    schema: {"arg": {"type": "string", "required": True, "default": ...}}
    Rules:
    - unknown arg -> ToolError mentioning the arg name
    - missing required arg (required defaults to False) -> ToolError mentioning the name
    - missing optional arg with a "default" -> filled in; without default -> omitted
    - wrong type -> ToolError. "integer" must be int and NOT bool; "number" is int or
      float (not bool); "string" str; "boolean" bool.
    - args that is not a dict -> ToolError
    Hint: isinstance(True, int) is True in Python!
    """
    ...


# ---------------------------------------------------------------- 2
class ToolRegistry:
    """Holds tools by name."""

    def __init__(self):
        ...

    def register(self, tool: Tool) -> None:
        """Add a tool. Duplicate name -> ValueError."""
        ...

    def get(self, name: str) -> Tool:
        """Return the tool or raise ToolError(f"unknown tool: {name}")."""
        ...

    def names(self) -> list[str]:
        """Sorted tool names."""
        ...

    def describe(self) -> str:
        """Prompt-ready text, one line per tool (sorted by name):
        '- name(arg1: type, arg2: type?): description'
        Optional args (not required) get a trailing '?'. Hint: join with newlines.
        """
        ...


# ---------------------------------------------------------------- 3
def parse_action(text: str) -> tuple[str, Any]:
    """Parse the model reply. Return ("final", answer_str) or ("tool", (name, args_dict)).

    - Replies may be wrapped in ```json fences; strip them.
    - Invalid JSON, non-object, or neither "final" nor "tool" key -> ToolError.
    - "args" defaults to {}. "tool" must be a str and args a dict, else ToolError.
    Hint: strip text, remove a leading ```json / ``` and trailing ``` then json.loads.
    """
    ...


# ---------------------------------------------------------------- 4
def run_tool(registry: ToolRegistry, name: str, args: dict, allowed: set[str] | None = None) -> dict:
    """Execute one tool call and NEVER raise. Return an observation dict:
    {"ok": True, "result": <value>} or {"ok": False, "error": "<message>"}.
    - allowed (allow-list): if not None and name not in it -> error containing "not allowed"
    - unknown tool, bad args (validate_args) -> error with the ToolError message
    - any exception inside the tool -> error like "tool failed: <ExcType>: <msg>"
    The model sees these errors and can self-correct.
    """
    ...


# ---------------------------------------------------------------- 5
def is_read_only_sql(sql: str) -> bool:
    """True only for a single SELECT statement.
    - strip whitespace, allow one trailing ';'
    - must start with SELECT (case-insensitive)
    - no other ';' (no stacked statements)
    - must not contain write keywords as whole words: insert update delete drop alter
      create replace attach pragma (case-insensitive)
    Hint: re.search(r"\\b(insert|update|...)\\b", sql, re.I)
    """
    ...


# ---------------------------------------------------------------- 6
def lookup_customer(conn: sqlite3.Connection, email: str) -> dict | None:
    """Return {"id","name","email","plan"} for the email (case-insensitive) or None.
    Use a parameterized query (?), never f-strings in SQL."""
    ...


def list_orders(conn: sqlite3.Connection, customer_id: int, status: str | None = None,
                limit: int = 10) -> list[dict]:
    """Orders of a customer, newest first (ORDER BY created DESC, id DESC), optional
    status filter, at most `limit` rows. Each dict: id, total_cents, status, created."""
    ...


def run_readonly_query(conn: sqlite3.Connection, sql: str, max_rows: int = 20) -> list[dict]:
    """Run a model-written SELECT. If not is_read_only_sql -> raise ToolError("only
    single SELECT statements are allowed"). Return at most max_rows rows as dicts
    (use cursor.fetchmany)."""
    ...


# ---------------------------------------------------------------- 7
def build_crm_registry(conn: sqlite3.Connection) -> ToolRegistry:
    """Registry with three tools wrapping the functions above:
    - lookup_customer(email: string, required)
    - list_orders(customer_id: integer required, status: string optional, limit: integer optional default 10)
    - run_query(sql: string required)  -> run_readonly_query
    Each needs a one-line description. Hint: use lambda/closures to bind `conn`.
    """
    ...


# ---------------------------------------------------------------- 8
def run_agent(llm: Callable[[list], str], registry: ToolRegistry, question: str,
              max_steps: int = 5, allowed: set[str] | None = None) -> AgentResult:
    """The agent loop.

    messages starts as [{"role": "user", "content": <question>}]. Each step (up to
    max_steps):
      1. reply = llm(messages); append {"role": "assistant", "content": reply}
      2. parse_action(reply). On ToolError: append a user message
         "ERROR: <msg>" and continue (the bad reply still counts as a step).
      3. "final" -> return AgentResult(answer, steps, "final", trace)
      4. "tool"  -> obs = run_tool(...); trace.append((name, args, obs));
         append {"role": "user", "content": "TOOL_RESULT: " + json.dumps(obs)}
    If the loop ends without a final: AgentResult(None, max_steps, "max_steps", trace).
    `steps` = number of llm calls made. Hint: json.dumps(obs, default=str).
    """
    ...
