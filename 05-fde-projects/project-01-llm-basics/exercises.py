"""Project 1: LLM basics. Read lesson.md first.

Everything here takes an injected `llm` callable: llm(prompt: str) -> str.
No network or API key is needed for the tests. Replace each `...` with code.
"""
import json
import math
import re


class LLMOutputError(ValueError):
    """Raised when model output cannot be parsed or validated."""


def build_prompt(system, instructions, examples, user_input):
    """Assemble a prompt string. Exact layout (sections joined by a blank line, i.e. "\\n\\n"):

        <system>
        Instructions:
        <instructions>
        Examples:                      <- this whole section only if `examples` is non-empty
        Input: <ex_in>
        Output: <ex_out>
        <blank line between examples>
        Input: <user_input>
        Output:

    `examples` is a list of (input, output) tuples. Sections: [system, "Instructions:\\n"+instructions,
    ("Examples:\\n" + "\\n\\n".join("Input: i\\nOutput: o")) if examples, "Input: "+user_input+"\\nOutput:"].
    Strip leading/trailing whitespace of system, instructions and user_input.
    Hint: build a list of sections, then "\\n\\n".join(sections).
    """
    ...


def extract_json(text):
    """Return the parsed JSON object/array found in an LLM reply.

    Models often wrap JSON in ```json fences or add chatter ("Sure! Here you go: {...}").
    Order: (1) try json.loads(text.strip()); (2) if a ``` fenced block exists, try its content;
    (3) take the substring from the first '{' or '[' to the LAST matching closing '}' / ']' and parse it.
    Raise LLMOutputError (message mentions "JSON") if nothing parses.
    Hint: re.search(r"```(?:json)?\\s*(.*?)```", text, re.DOTALL)
    """
    ...


def validate_fields(data, schema):
    """Check `data` (a dict) against `schema` ({field_name: expected_type_or_tuple}).

    Return a list of human-readable error strings (empty list = valid), in schema order:
      - missing field      -> "missing field: <name>"
      - wrong type         -> "field <name> should be <type_name>, got <actual_type_name>"
    where type_name uses `.__name__` (for a tuple of types join the names with "|").
    Note: bool is NOT accepted where int/float is expected; int IS accepted where float is expected.
    If `data` is not a dict return ["expected a JSON object"]. Extra fields are allowed.
    """
    ...


def get_structured(llm, prompt, schema, max_retries=2):
    """Call llm(prompt), extract JSON, validate against schema; retry on failure.

    Total attempts = max_retries + 1. The first call uses `prompt` unchanged. After a failure the next
    prompt is:  prompt + "\\n\\nYour previous reply was invalid: " + <error text> + "\\nReturn only valid JSON."
    where <error text> is str(LLMOutputError) for parse errors, or "; ".join(validation errors).
    (Always rebuild from the ORIGINAL prompt, do not stack repair messages.)
    Return the validated dict. If all attempts fail raise LLMOutputError whose message contains
    "after <n> attempts" (n = total attempts).
    """
    ...


def collect_stream(chunks, on_chunk=None):
    """Consume an iterable of text chunks (a streaming response) and return the full string.

    Skip None and empty-string chunks. For every non-empty chunk call on_chunk(chunk) if on_chunk is given
    (this is how a UI would print tokens as they arrive). Must work with generators (single pass).
    """
    ...


def parse_sse_lines(lines):
    """Parse Server-Sent-Event style lines into text deltas.

    Each relevant line looks like:  'data: {"text": "Hel"}'.
    Rules: ignore blank lines and lines not starting with "data:"; stop (without error) at 'data: [DONE]';
    skip lines whose payload is not valid JSON or lacks a "text" key; return list of the "text" strings.
    """
    ...


def estimate_tokens(text):
    """Rough token estimate: ceil(len(text) / 4). Empty string -> 0. (Real tokenizers differ; this is
    for budgeting, not billing.)"""
    ...


def estimate_cost(input_tokens, output_tokens, price_in_per_mtok, price_out_per_mtok):
    """USD cost = input_tokens/1e6*price_in + output_tokens/1e6*price_out, rounded to 6 decimals.
    Raise ValueError if any argument is negative."""
    ...


class UsageTracker:
    """Track token usage and cost across many calls.

    UsageTracker(price_in_per_mtok, price_out_per_mtok)
      .record(prompt, response) -> None   adds estimate_tokens(prompt) to input and
                                          estimate_tokens(response) to output, increments calls
      .calls                -> int
      .input_tokens / .output_tokens -> int
      .total_tokens         -> property, input + output
      .total_cost           -> property, estimate_cost of the accumulated totals
      .wrap(llm)            -> returns a new callable llm2(prompt) that calls llm, records, returns response
    """

    def __init__(self, price_in_per_mtok, price_out_per_mtok):
        ...

    def record(self, prompt, response):
        ...

    @property
    def total_tokens(self):
        ...

    @property
    def total_cost(self):
        ...

    def wrap(self, llm):
        ...
