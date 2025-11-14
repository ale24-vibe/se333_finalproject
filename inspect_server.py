import server
import inspect

print('Type of server.git_status:', type(server.git_status))
print('repr:', repr(server.git_status))
print('\nDir(server.git_status):')
print(dir(server.git_status))

print('\nAttributes on mcp object:')
print([k for k in dir(server.mcp) if not k.startswith('_')][:200])

# Try to find tools registry
for name in ('tools', 'tool_registry', 'registered_tools', 'functions'):
    if hasattr(server.mcp, name):
        print(f"mcp.{name} exists ->", getattr(server.mcp, name))

# If the object has a .fn or .func attribute, show it
for attr in ('fn', 'func', '__wrapped__', 'callable', 'call'):
    if hasattr(server.git_status, attr):
        print(f"server.git_status.{attr}:", getattr(server.git_status, attr))

# Print source if available
try:
    src = inspect.getsource(server.git_status)
    print('\nSource for server.git_status:\n', src)
except Exception as e:
    print('Could not get source:', e)

# Try to find an underlying function in server module
if hasattr(server, 'git_status'):
    obj = server.git_status
    for name in dir(obj):
        if name.lower().startswith('fn') or name.lower().startswith('func'):
            print('Possible underlying attribute:', name, getattr(obj, name))

print('\nDone inspection')
