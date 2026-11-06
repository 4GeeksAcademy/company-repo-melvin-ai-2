"""OAuth-protected tools for Brasaland incidents and read-only inventory."""

PORT = 8765
JWKS_PORT = 8766
AUDIENCE = "brasaland-mcp"
SCOPES = ("incidents:read", "incidents:write", "inventory:read")
