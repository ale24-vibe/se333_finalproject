import re
from typing import Any, Dict


def _safe_eval(expr: str) -> str:
    """Evaluate a numeric expression consisting only of digits and basic operators.

    Returns a string result or raises a ValueError on invalid input.
    """
    if not re.match(r"^[0-9+\-*/(). \t%]+$", expr):
        raise ValueError("invalid expression")
    try:
        value = eval(expr, {"__builtins__": None}, {})
    except Exception as e:
        raise ValueError(str(e))
    return str(value)


def _nlp_normalize(text: str) -> str:
    """Normalize common natural-language math phrases into symbol-based expressions.

    Conservative replacements only; preserves numeric tokens and operator symbols.
    """
    if not isinstance(text, str):
        return ""
    s = text.lower()
    replacements = [
        (r"\bmultiplied by\b", " * "),
        (r"\btimes\b", " * "),
        (r"\bdivided by\b", " / "),
        (r"\bover\b", " / "),
        (r"\bto the power of\b", " ** "),
        (r"\bpower of\b", " ** "),
        (r"\bplus\b", " + "),
        (r"\bminus\b", " - "),
        (r"\bmod\b", " % "),
    ]
    for patt, repl in replacements:
        s = re.sub(patt, repl, s)

    s = re.sub(r"\b(calculate|compute|what is|what's|please|answer|=)\b", "", s)
    s = re.sub(r"\s+", " ", s)
    # Convert common number words to digits (one..nineteen, tens, hundred)
    number_map = {
        'zero': '0', 'one': '1', 'two': '2', 'three': '3', 'four': '4',
        'five': '5', 'six': '6', 'seven': '7', 'eight': '8', 'nine': '9',
        'ten': '10', 'eleven': '11', 'twelve': '12', 'thirteen': '13', 'fourteen': '14',
        'fifteen': '15', 'sixteen': '16', 'seventeen': '17', 'eighteen': '18', 'nineteen': '19',
        'twenty': '20', 'thirty': '30', 'forty': '40', 'fifty': '50', 'sixty': '60',
        'seventy': '70', 'eighty': '80', 'ninety': '90', 'hundred': '100'
    }
    def _replace_number_words(match):
        w = match.group(0)
        return number_map.get(w, w)

    s = re.sub(r"\b(" + "|".join(number_map.keys()) + r")\b", _replace_number_words, s)
    return s.strip()


def _extract_expression(text: str) -> str:
    """Extract a numeric expression from a user-style prompt.

    Examples handled: "what is 1+2?", "What is 1 + 2?", or just "1+2".
    Returns the cleaned expression string or empty string if none.
    """
    if not isinstance(text, str):
        return ""
    s = _nlp_normalize(text)
    s = s.strip()
    m = re.search(r"what is\s+(.+)$", s, re.I)
    if m:
        expr = m.group(1)
    else:
        expr = s
    expr = expr.strip()
    expr = re.sub(r"[?!.]+$", "", expr)
    return expr.strip()


def _make_rpc_response(req_body: Dict[str, Any], result_obj: Any) -> Any:
    if isinstance(req_body, dict) and req_body.get("jsonrpc") and "id" in req_body:
        return {"jsonrpc": "2.0", "id": req_body.get("id"), "result": result_obj}
    return {"result": result_obj}
