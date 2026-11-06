"""Serve a local JWKS and print a short-lived bearer token.

This is for MCP Playground when no paid identity provider is available.
The MCP server still checks the signature, issuer, audience, and scopes.
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import jwt
from cryptography.hazmat.primitives.asymmetric import rsa
from jwt.algorithms import RSAAlgorithm

from mcps.brasaland_tools import AUDIENCE, JWKS_PORT, SCOPES


def main() -> None:
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    public = json.loads(RSAAlgorithm.to_jwk(key.public_key()))
    public.update({"kid": "brasaland-dev", "use": "sig", "alg": "RS256"})
    body = json.dumps({"keys": [public]}).encode()
    issuer = f"http://127.0.0.1:{JWKS_PORT}"

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:  # noqa: N802
            if self.path != "/jwks":
                self.send_response(404)
                self.end_headers()
                return
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, _format: str, *_args) -> None:
            return

    server = ThreadingHTTPServer(("127.0.0.1", JWKS_PORT), Handler)
    token = jwt.encode(
        {
            "iss": issuer,
            "aud": AUDIENCE,
            "sub": "playground",
            "client_id": "mcp-playground",
            "scope": " ".join(SCOPES),
            "iat": datetime.now(timezone.utc),
            "exp": datetime.now(timezone.utc) + timedelta(hours=8),
        },
        key,
        algorithm="RS256",
        headers={"kid": "brasaland-dev"},
    )
    print("Leave this process running, then start the MCP server with:")
    print(f"export MCP_ISSUER={issuer}")
    print(f"export MCP_AUDIENCE={AUDIENCE}")
    print(f"export MCP_JWKS_URI={issuer}/jwks")
    print(f"export BRASALAND_MCP_TOKEN={token}")
    print("Bearer token for MCP Playground:")
    print(token)
    server.serve_forever()


if __name__ == "__main__":
    main()
