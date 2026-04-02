import sys


def get_mcp_server_config() -> dict:
    python = sys.executable
    return {
        "knowledge": {
            "command": python,
            "args": ["-m", "mcp_servers.knowledge_server"],
            "transport": "stdio",
        },
        "ticket": {
            "command": python,
            "args": ["-m", "mcp_servers.ticket_server"],
            "transport": "stdio",
        },
    }


async def get_mcp_tools() -> list:
    from langchain_mcp_adapters.client import MultiServerMCPClient

    config = get_mcp_server_config()
    client = MultiServerMCPClient(config)
    tools = await client.get_tools()
    return tools
