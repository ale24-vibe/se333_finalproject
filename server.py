from fastmcp import FastMCP

# Create MCP instance
mcp = FastMCP("Calculator MCP Server")

@mcp.tool(description="Adds two integers")
def add(a: int, b: int) -> int:
    return a + b

@mcp.tool(description="Subtracts b from a")
def subtract(a: int, b: int) -> int:
    return a - b

@mcp.tool(description="Multiplies two integers")
def multiply(a: int, b: int) -> int:
    return a * b

@mcp.tool(description="Divides a by b (returns float, inf if b=0)")
def divide(a: int, b: int) -> float:
    return a / b if b != 0 else float("inf")

# Run the server when executing this file
if __name__ == "__main__":
    mcp.run(transport="sse", host="127.0.0.1", port=8001)
