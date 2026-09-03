#!/usr/bin/env bash
#
# Expose the local Flask app to the public internet so Midtrans can reach the
# payment webhook (POST /api/v1/payment/notification).
#
# Usage:
#   ./ngrok_tunnel.sh          # tunnels port 8000 (default)
#   ./ngrok_tunnel.sh 5000     # tunnels a custom port
#
# Prerequisites:
#   brew install ngrok
#   ngrok config add-authtoken <YOUR_NGROK_AUTHTOKEN>
#
# After it starts, copy the printed https URL and set it in the Midtrans dashboard:
#   Settings -> Configuration -> Payment Notification URL
#   https://<subdomain>.ngrok-free.app/api/v1/payment/notification
#
set -euo pipefail

PORT="${1:-8000}"

if ! command -v ngrok >/dev/null 2>&1; then
  echo "ngrok is not installed. Install it with: brew install ngrok" >&2
  echo "Then authenticate once: ngrok config add-authtoken <YOUR_NGROK_AUTHTOKEN>" >&2
  exit 1
fi

echo "Starting ngrok tunnel to http://localhost:${PORT}"
echo "Webhook path to register in Midtrans: /api/v1/payment/notification"
echo

exec ngrok http "${PORT}"
