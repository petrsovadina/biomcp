"""Full entrypoint for Arcade Deploy — all 60 tools.

Deploy with: arcade deploy -e src/czechmedmcp/arcade/entrypoint.py
Local test:  python src/czechmedmcp/arcade/entrypoint.py stdio
"""

import sys

import czechmedmcp.arcade.czech_tools

# Import all wrapper modules to trigger @arcade_app.tool registration.
import czechmedmcp.arcade.individual_tools
import czechmedmcp.arcade.metrics_tool
import czechmedmcp.arcade.router_tools
import czechmedmcp.arcade.thinking_tool  # noqa: F401
from czechmedmcp.arcade import arcade_app

app = arcade_app

if __name__ == "__main__":
    transport = sys.argv[1] if len(sys.argv) > 1 else "stdio"
    app.run(transport=transport, host="127.0.0.1", port=8000)
