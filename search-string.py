#!/usr/bin/env python3
"""search-string.py

Simple, robust command-line search utility.

Features:
- substring search (default) or regex search (-r)
- case-insensitive (-i)
- show line numbers (-n)
- show counts only (-c)
- show context lines (-C N)
- read from one or more files or from stdin (use '-' or omit files)

Examples:
  python3 search-string.py "TODO" notes.txt
  python3 search-string.py -i -n "fixme" file1.txt file2.txt
  echo "hello" | python3 search-string.py "hello"
"""

import argparse
import re
import sys
from collections import deque


def search_stream(stream, name, pattern, show_numbers, show_counts, context):
    """Search an open text stream line-by-line.

    Args:
        stream: file-like object to read lines from.
        name: display name for the stream (filename or '-')
        pattern: compiled regex pattern to search with.
        show_numbers: include line numbers in output.
        show_counts: if True, don't print lines, only return match count.
        context: number of context lines to show before and after a match.
    Returns:
        match_count (int)
    """
    before = deque(maxlen=context)
    after = 0
    match_count = 0
    lineno = 0

    for raw_line in stream:
        lineno += 1
        line = raw_line.rstrip('\n')

        if after > 0:
            # we're in the tail context of a previous match
            if not show_counts:
                prefix = f"{name}:" if name not in (None, "-") else ""
                num = f"{lineno}:" if show_numbers else ""
                print(f"{prefix}{num}{line}")
            after -= 1
            continue

        m = pattern.search(line)
        if m:
            match_count += 1
            if show_counts:
                # if only counting, skip printing lines
                # still continue to compute further matches
                after = 0
            else:
                # print before context
                for i, ctx_line in enumerate(before, start=lineno - len(before)):
                    prefix = f"{name}:" if name not in (None, "-") else ""
                    num = f"{i}:" if show_numbers else ""
                    print(f"{prefix}{num}{ctx_line}")

                # print matching line
                prefix = f"{name}:" if name not in (None, "-") else ""
                num = f"{lineno}:" if show_numbers else ""
                print(f"{prefix}{num}{line}")

                # set after-context counter
                after = context

            # clear before-context buffer after a match
            before.clear()
        else:
            before.append(line)

    return match_count


def compile_pattern(search_string, use_regex, ignore_case):
    flags = re.MULTILINE
    if ignore_case:
        flags |= re.IGNORECASE
    if use_regex:
        return re.compile(search_string, flags)
    else:
        return re.compile(re.escape(search_string), flags)


def main(argv=None):
    parser = argparse.ArgumentParser(description="Search for a string (or regex) in one or more files.")
    parser.add_argument("search", help="search string or regex pattern")
    parser.add_argument("files", nargs="*", default=["-"], help="files to search (use '-' or omit to read stdin)")
    parser.add_argument("-r", "--regex", action="store_true", help="treat search string as a regular expression")
    parser.add_argument("-i", "--ignore-case", action="store_true", help="case-insensitive search")
    parser.add_argument("-n", "--line-numbers", action="store_true", help="show line numbers")
    parser.add_argument("-c", "--count", action="store_true", help="only print the count of matching lines per file")
    parser.add_argument("-C", "--context", type=int, default=0, help="number of context lines to show before and after each match")

    args = parser.parse_args(argv)

    pattern = compile_pattern(args.search, args.regex, args.ignore_case)

    total_matches = 0
    first = True
    multiple_files = len(args.files) > 1

    for file_path in args.files:
        name = file_path
        try:
            if file_path == "-":
                # read from stdin
                stream = sys.stdin
                match_count = search_stream(stream, name if multiple_files else None, pattern, args.line_numbers, args.count, args.context)
            else:
                with open(file_path, 'r', encoding='utf-8', errors='replace') as fh:
                    match_count = search_stream(fh, name if multiple_files else file_path, pattern, args.line_numbers, args.count, args.context)

        except FileNotFoundError:
            print(f"Error: file not found: {file_path}", file=sys.stderr)
            continue
        except PermissionError:
            print(f"Error: permission denied: {file_path}", file=sys.stderr)
            continue
        except Exception as e:
            print(f"Error reading {file_path}: {e}", file=sys.stderr)
            continue

        total_matches += match_count
        if args.count:
            print(f"{file_path}: {match_count}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
