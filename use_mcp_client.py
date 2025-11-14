"""
Use MCP client registry to call git tools via `mcp.get_tool(...).run()`.
This script will try `.run()` on the tool; if that fails it will call `.fn()` as a fallback.
Non-destructive by default (automated_workflow called with create_pr=False).
"""
from pprint import pprint
import server
import asyncio


async def call_tool(name, *args, **kwargs):
    tool = None
    try:
        tool = await server.mcp.get_tool(name)
    except Exception as e:
        print(f"get_tool('{name}') failed (await): {e}")
        tool = getattr(server, name, None)

    if tool is None:
        print(f"Tool {name} not found on mcp or server")
        return None

    # Prefer run() on the FunctionTool, else call fn(), else try calling it directly
    try:
        if hasattr(tool, 'run'):
            print(f"Calling {name} via .run()")
            # run may be coroutine or regular; handle both
            result = tool.run(*args, **kwargs)
            if asyncio.iscoroutine(result):
                return await result
            return result
    except Exception as e:
        print(f"{name}.run() raised: {e}")

    try:
        if hasattr(tool, 'fn'):
            print(f"Calling {name} via .fn() (underlying function)")
            result = tool.fn(*args, **kwargs)
            if asyncio.iscoroutine(result):
                return await result
            return result
    except Exception as e:
        print(f"{name}.fn() raised: {e}")

    try:
        if callable(tool):
            print(f"Calling {name} directly as callable")
            result = tool(*args, **kwargs)
            if asyncio.iscoroutine(result):
                return await result
            return result
    except Exception as e:
        print(f"Direct call to {name} raised: {e}")

    print(f"Failed to invoke tool {name}")
    return None


async def main():
    print('--- git_status ---')
    res = await call_tool('git_status')
    pprint(res)

    print('\n--- git_add_all ---')
    res = await call_tool('git_add_all')
    pprint(res)

    print('\n--- git_commit (non-destructive intentional test) ---')
    res = await call_tool('git_commit', "chore: mcp-client test commit", {"line_coverage":"0%"})
    pprint(res)

    print('\n--- automated_workflow (create_pr=False) ---')
    res = await call_tool('automated_workflow', commit_message="mcp client workflow", push_remote="origin", create_pr=False, coverage_stats={"line_coverage":"0%"})
    pprint(res)


if __name__ == '__main__':
    asyncio.run(main())
