"""
Midtrans Snap client factory.

Builds a `midtransclient.Snap` instance from Flask app config. Keeping this in
one place means the payment service can be unit-tested by mocking
`get_snap_client` (no real network calls in tests).

Config keys (set in app/__init__.py from environment):
    MIDTRANS_SERVER_KEY   - server key (SB-Mid-server-... for sandbox)
    MIDTRANS_CLIENT_KEY   - client key (SB-Mid-client-... for sandbox)
    MIDTRANS_IS_PRODUCTION - bool; False -> sandbox endpoints
"""
import midtransclient
from flask import current_app


def get_snap_client():
    """Return a configured Snap client. Raises if server key is missing."""
    server_key = current_app.config.get("MIDTRANS_SERVER_KEY")
    client_key = current_app.config.get("MIDTRANS_CLIENT_KEY")

    if not server_key:
        raise RuntimeError("MIDTRANS_SERVER_KEY is not configured")

    return midtransclient.Snap(
        is_production=current_app.config.get("MIDTRANS_IS_PRODUCTION", False),
        server_key=server_key,
        client_key=client_key,
    )
