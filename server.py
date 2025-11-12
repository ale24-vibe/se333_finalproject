from fastmcp import FastMCP

# Create MCP instance
mcp = FastMCP("Calculator MCP Server")

# Example tool
@mcp.tool
def add(a: int, b: int) -> int:
    return a + b

# Run the server when executing this file
if __name__ == "__main__":
    mcp.run(transport="sse")
