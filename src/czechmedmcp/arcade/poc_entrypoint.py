"""PoC entrypoint for Arcade Deploy — 5 representative tools.

Deploy with: arcade deploy -e src/czechmedmcp/arcade/poc_entrypoint.py
Local test:  python src/czechmedmcp/arcade/poc_entrypoint.py stdio
"""

import sys

import czechmedmcp.arcade.czech_tools

# Import wrapper modules to trigger @arcade_app.tool registration.
# PoC subset: article_searcher, article_getter, czechmed_search_medicine,
# think, get_performance_metrics
import czechmedmcp.arcade.individual_tools
import czechmedmcp.arcade.metrics_tool
import czechmedmcp.arcade.thinking_tool  # noqa: F401
from czechmedmcp.arcade import arcade_app

app = arcade_app

if __name__ == "__main__":
    transport = sys.argv[1] if len(sys.argv) > 1 else "stdio"
    app.run(transport=transport, host="127.0.0.1", port=8000)
