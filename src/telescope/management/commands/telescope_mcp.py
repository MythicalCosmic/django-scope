import asyncio

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Start the Telescope MCP server for AI assistant integration"

    def handle(self, *args, **options):
        try:
            from telescope.mcp.server import create_server
        except ImportError:
            self.stderr.write(
                "MCP support requires the 'mcp' package.\n"
                "Install it with: pip install django-scope[mcp]\n"
            )
            return

        server, stdio_server = create_server()

        async def run():
            async with stdio_server() as (read_stream, write_stream):
                await server.run(read_stream, write_stream)

        self.stdout.write("Starting Telescope MCP server...")
        asyncio.run(run())
