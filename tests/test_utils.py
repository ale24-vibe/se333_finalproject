from utils import _nlp_normalize, _extract_expression, _safe_eval


def test_nlp_normalize():
    s = "Calculate 2 times 3 plus 4"
    norm = _nlp_normalize(s)
    assert "*" in norm and "+" in norm


def test_extract_expression():
    assert _extract_expression("What is 1 + 2?") == "1 + 2"
    assert _extract_expression("2 times 3") == "2 * 3"


def test_safe_eval():
    assert _safe_eval("1+2") == "3"
    assert _safe_eval("2 * 3 + 4") == "10"
