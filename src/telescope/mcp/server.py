"""MCP server for django-telescope — exposes telemetry to AI assistants."""

import json


def create_server():
    """Create and configure the MCP server with telescope tools."""
    try:
        from mcp.server import Server
        from mcp.server.stdio import stdio_server
        from mcp.types import TextContent, Tool
    except ImportError:
        raise ImportError(
            "MCP support requires the 'mcp' package. "
            "Install it with: pip install django-scope[mcp]"
        )

    server = Server("django-telescope")

    @server.list_tools()
    async def list_tools():
        return [
            Tool(
                name="get_recent_requests",
                description="Get recent HTTP request entries from the Django application",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "limit": {"type": "integer", "default": 20, "description": "Max results"},
                        "status_code": {"type": "integer", "description": "Filter by status code"},
                    },
                },
            ),
            Tool(
                name="get_slow_queries",
                description="Get slow database queries above a threshold",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "threshold_ms": {"type": "number", "description": "Duration threshold in ms"},
                        "limit": {"type": "integer", "default": 20},
                    },
                },
            ),
            Tool(
                name="get_exceptions",
                description="Get recent unhandled exceptions from the Django application",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "limit": {"type": "integer", "default": 20},
                    },
                },
            ),
            Tool(
                name="get_n1_patterns",
                description="Get N+1 query patterns — repeated similar queries within requests",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "limit": {"type": "integer", "default": 10},
                    },
                },
            ),
            Tool(
                name="search_entries",
                description="Search telescope entries by content or tag keywords",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Search query"},
                        "entry_type": {"type": "string", "description": "Entry type slug (e.g. 'query', 'request')"},
                        "limit": {"type": "integer", "default": 20},
                    },
                    "required": ["query"],
                },
            ),
            Tool(
                name="get_stats_summary",
                description="Get overall application stats: request counts, error rates, cache hits, N+1 patterns",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "range_hours": {"type": "integer", "default": 24, "description": "Time range in hours"},
                    },
                },
            ),
        ]

    @server.call_tool()
    async def call_tool(name, arguments):
        from . import tools

        tool_map = {
            "get_recent_requests": tools.get_recent_requests,
            "get_slow_queries": tools.get_slow_queries,
            "get_exceptions": tools.get_exceptions,
            "get_n1_patterns": tools.get_n1_patterns,
            "search_entries": tools.search_entries,
            "get_stats_summary": tools.get_stats_summary,
        }

        func = tool_map.get(name)
        if not func:
            return [TextContent(type="text", text=f"Unknown tool: {name}")]

        result = func(**arguments)
        return [TextContent(type="text", text=json.dumps(result, indent=2, default=str))]

    return server, stdio_server
