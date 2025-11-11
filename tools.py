from typing import Any, Dict, Callable
from utils import _extract_expression, _safe_eval


TOOLS: Dict[str, Dict[str, Any]] = {}


def mcp(name: str = None):
    """Decorator to register a function as an MCP tool.

    Usage:
      @mcp('tool_name')
      def handler(text): ...
    """
    def _decorator(fn: Callable):
        key = name or fn.__name__
        TOOLS[key] = {"doc": fn.__doc__ or "", "func": fn}
        return fn

    return _decorator


@mcp("aple_calculator")
def aple_calculator(text: str) -> str:
    """Simple calculator tool that evaluates numeric expressions from 'text'."""
    expr = _extract_expression(text)
    return _safe_eval(expr)
