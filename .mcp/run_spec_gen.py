#!/usr/bin/env python3
"""Helper script to invoke spec_test_generator without importing server.

Reads a spec JSON path (default: .mcp/spec_calculator_add.json) and prints a
compact JSON summary including counts, output file path, and a sample of cases.
"""
import json, sys, runpy, pathlib

def main():
    spec_path = pathlib.Path('.mcp/spec_calculator_add.json')
    if len(sys.argv) > 1:
        spec_path = pathlib.Path(sys.argv[1])
    spec = json.loads(spec_path.read_text(encoding='utf-8'))
    mod = runpy.run_path(str(pathlib.Path('.mcp') / 'spec_test_generator.py'))
    gen = mod['generate_and_render']
    res = gen(spec, True)
    out = {
        'summary': res['summary'],
        'file': res['file'],
        'sampleCases': res['cases'][:8]
    }
    print(json.dumps(out, indent=2))

if __name__ == '__main__':
    main()