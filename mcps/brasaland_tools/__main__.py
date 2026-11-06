"""Start the Brasaland MCP server on port 8765."""

import uvicorn

from mcps.brasaland_tools import PORT
from mcps.brasaland_tools.server import build_app

if __name__ == "__main__":
    uvicorn.run(build_app(), host="0.0.0.0", port=PORT)
