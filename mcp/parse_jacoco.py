# Wrapper duplicate to satisfy previously staged path 'mcp/parse_jacoco.py'.
# The authoritative version lives in '.mcp/parse_jacoco.py'. This file allows
# committing without altering tooling expectations.
from pathlib import Path
import sys

ORIGINAL = Path(__file__).parent.parent / '.mcp' / 'parse_jacoco.py'
if __name__ == '__main__':
    if ORIGINAL.exists():
        code = ORIGINAL.read_text(encoding='utf-8', errors='ignore')
        # Execute in a fresh globals dict.
        exec(compile(code, str(ORIGINAL), 'exec'), {})
    else:
        print('Original .mcp/parse_jacoco.py missing.')
        sys.exit(1)
