# Payment Steps with Midtrans (Snap)

How payments and refunds flow through the API using the Midtrans Snap gateway.
Payment is **asynchronous**: the API never marks an order `PAID` on its own — an
order only becomes `PAID` after Midtrans confirms settlement via a webhook.

- Buyer-facing endpoint: `POST /api/v1/payment/` (JWT required)
- Gateway webhook: `POST /api/v1/payment/notification` (no JWT, called by Midtrans)
- Cancellation + refund: `PUT /api/v1/orders/<id>` with `{"status": "CANCELED"}`

## Order status vs payment status

Two independent fields live on each order:

| Field | Meaning | Values |
| :--- | :--- | :--- |
| `status` | Business lifecycle | `PENDING`, `PAID`, `COMPLETED`, `CANCELED` |
| `payment_status` | Gateway state (mirrors Midtrans) | `pending`, `settlement`, `capture`, `refund`, `expire`, `deny`, `cancel` |

`payment_ref` holds the Midtrans transaction reference in the form
`ORDER-{order_id}-{unix_timestamp}` — this is the handle used for refunds.

## End-to-end flow

```
1. Buyer   -> POST /api/v1/payment/            -> API creates Snap tx, returns snap_token + redirect_url
                                                   (order stays PENDING, no stock deducted)
2. Buyer   -> opens redirect_url (Midtrans page) -> completes payment with a method
3. Midtrans-> POST /api/v1/payment/notification -> API verifies signature, deducts stock,
                                                   transitions PENDING -> PAID
4. Seller  -> PUT /api/v1/orders/<id>           -> PAID -> COMPLETED (fulfill)
             or PAID -> CANCELED                -> full refund + stock restored
```

---

## Buyer case

### 1. Create an order (cart / checkout)

`POST /api/v1/orders/` with items. Order is created as `PENDING`; stock is **not**
deducted yet and `address_id` may be null.

```bash
curl -X POST http://localhost:8000/api/v1/orders/ \
  -H "Authorization: Bearer <BUYER_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"name": "my order", "items": [{"product_id": 3, "quantity": 2}]}'
```

### 2. Initiate payment

`POST /api/v1/payment/`. Requires `order_id`; `address_id` is optional (falls back
to the buyer's default address). This creates the Midtrans Snap transaction.

```bash
curl -X POST http://localhost:8000/api/v1/payment/ \
  -H "Authorization: Bearer <BUYER_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"order_id": 1}'
```

Response (order still `PENDING`):

```json
{
  "success": true,
  "message": "Payment initiated. Complete payment via redirect_url.",
  "snap_token": "66e4fa55-fdac-4ef9-91b5-733b97d1b862",
  "redirect_url": "https://app.sandbox.midtrans.com/snap/v3/redirection/66e4fa55-...",
  "data": { "id": 1, "status": "PENDING", "payment_ref": "ORDER-1-1735900000", "payment_status": "pending", "...": "..." }
}
```

Validation errors returned here (order not found `404`, not the buyer's order `403`,
order not `PENDING` `400`, no default address `400`, insufficient stock `400`).

### 3. Complete payment on the Midtrans page

Open `redirect_url` in a browser. This is Midtrans's hosted Snap page (their frontend,
not ours). In **sandbox**, pay with Midtrans's published test credentials — for example
a test card such as `4811 1111 1111 1114`, any future expiry, CVV `123`, OTP `112233`
(full list below).

#### Sandbox test cards

Random card numbers are rejected by the sandbox — use Midtrans's published test
cards. For every card below: use **any future expiry** (e.g. `12/30`), **CVV `123`**,
and 3DS/OTP password **`112233`** when prompted. Values can change, so cross-check the
[Midtrans sandbox testing docs](https://docs.midtrans.com/docs/testing-payment-on-sandbox).

| Scenario | Card number | Resulting `transaction_status` | Order outcome |
| :--- | :--- | :--- | :--- |
| Success (Visa) | `4811 1111 1111 1114` | `capture` / `settlement` | `PENDING -> PAID`, stock deducted |
| Success (Mastercard) | `5211 1111 1111 1117` | `capture` / `settlement` | `PENDING -> PAID`, stock deducted |
| 3DS challenge (forces OTP) | `4411 1111 1111 1118` | `capture` after OTP `112233` | `PAID` once OTP passes |
| Deny / declined | `4911 1111 1111 1113` | `deny` | stays `PENDING`, stock untouched |
| Insufficient funds | `4111 1111 1111 1112` | `deny` | stays `PENDING`, stock untouched |

Notes:

- **Success** cards trigger the webhook path that flips the order to `PAID`
  (see step 4). CVV `123`, OTP `112233` are the standard sandbox values.
- **Deny** cards make Midtrans send `transaction_status = deny`; the webhook records
  it and the order stays `PENDING` — nothing is deducted.
- **Expire** is not a card: an order expires when it is left unpaid past the Snap
  window, or you can force it from the
  [transaction simulator](https://simulator.sandbox.midtrans.com/) (Card Payment ->
  set status to `expire`). The webhook then records `payment_status = expire`, order
  stays `PENDING`.
- Non-card methods (bank transfer / e-wallet) are settled/expired/denied from that
  same simulator rather than with a card number.
- These only work with **sandbox** keys (`SB-Mid-...`). In production, real cards are
  used and these numbers are invalid.

Content was rephrased for compliance with licensing restrictions.

In a real product, your web/mobile frontend would either redirect the user to
`redirect_url` or embed Snap.js using `snap_token`.

### 4. Settlement (automatic, via webhook)

When payment settles, Midtrans calls `POST /api/v1/payment/notification`. The API:

1. Verifies the signature: `sha512(order_id + status_code + gross_amount + server_key)`.
2. On `settlement` (or `capture` + `fraud_status=accept`): deducts stock and sets
   `status = PAID`, `payment_status = settlement`.
3. Is idempotent — repeated callbacks for an already-`PAID` order do nothing.
4. On `expire` / `deny` / `cancel`: records the status, leaves stock untouched, order stays `PENDING`.

The buyer does not call this endpoint; it is server-to-server.

### 5. Buyer cancellation

A buyer may cancel their own order only when it is `COMPLETED` or `CANCELED`
(per the RBAC rules in the main README). A `PAID` order canceled through the
status transition triggers a refund (see Refund below).

---

## Seller case

Sellers do not pay. Their involvement is fulfilling or cancelling orders that
contain their products.

### 1. Read incoming orders

`GET /api/v1/orders/` returns orders that contain the seller's products
(scoping is enforced server-side and cannot be widened by query params).

```bash
curl "http://localhost:8000/api/v1/orders/?status=PAID" \
  -H "Authorization: Bearer <SELLER_TOKEN>"
```

### 2. Fulfill: PAID -> COMPLETED

```bash
curl -X PUT http://localhost:8000/api/v1/orders/1 \
  -H "Authorization: Bearer <SELLER_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"status": "COMPLETED"}'
```

### 3. Cancel + refund: PAID -> CANCELED

When a seller (or buyer) transitions a `PAID` order to `CANCELED`, the API performs
both restorations in a safe order:

1. **Refund the buyer** — a full refund is requested from Midtrans using the stored
   `payment_ref`. On success `payment_status` becomes `refund`.
2. **Restore stock to the seller** — item quantities are added back to product stock.

```bash
curl -X PUT http://localhost:8000/api/v1/orders/1 \
  -H "Authorization: Bearer <SELLER_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"status": "CANCELED"}'
```

Safety rules:

- If the Midtrans refund **fails**, the whole cancellation is aborted (rolled back):
  the order stays `PAID` and stock is **not** restored, so money and inventory never
  diverge.
- Orders with **no `payment_ref`** (legacy/seeded orders never paid through Midtrans)
  skip the gateway call and simply restore stock — the pre-gateway behavior.
- Only settled payments (`payment_status = settlement`) are refunded; non-settled
  references are skipped rather than refunded incorrectly.

Allowed transitions: `PENDING -> PAID` (via webhook only), `PAID -> COMPLETED`,
`PAID -> CANCELED`. No transition back to `PENDING`.

---

## Local testing with ngrok

Midtrans's servers cannot reach `http://localhost:8000`, so to receive the webhook
locally you expose your port with a tunnel. Everything still runs on your machine and
against your **local** database.

### 1. Install ngrok

```bash
brew install ngrok            # macOS
# then authenticate once with your ngrok account token:
ngrok config add-authtoken <YOUR_NGROK_AUTHTOKEN>
```

### 2. Start the API and the tunnel

```bash
# terminal 1 — run the app
flask run --debug --port=8000

# terminal 2 — open the tunnel (or use the helper script below)
./ngrok_tunnel.sh
```

`ngrok` prints a public HTTPS URL, e.g. `https://abc123.ngrok-free.app`.

### 3. Point Midtrans at your tunnel

In the Midtrans dashboard: **Settings -> Configuration -> Payment Notification URL**,
set it to:

```
https://abc123.ngrok-free.app/api/v1/payment/notification
```

The free ngrok URL changes on every restart, so re-paste it each session.
Optionally set `BASE_URL` in `.env` to the ngrok URL for consistency.

### 4. Run a payment

1. `POST /api/v1/payment/` to get a `redirect_url`.
2. Open `redirect_url`, pay with sandbox test credentials.
3. Midtrans calls your tunnel -> `/notification` -> order becomes `PAID` in the local DB.

You can also skip the payment page and use the Midtrans sandbox
[transaction simulator](https://simulator.sandbox.midtrans.com/) to force
`settlement` / `expire` / `deny`, which sends the notification to your tunnel.

### About the dashboard "Test notification URL" button

The **Test notification URL** button in the dashboard is only a reachability probe.
It always sends a synthetic payload with a fake `order_id` like
`payment_notif_test_...`, which does not match any real order. The API correctly
returns `404` for it, and the dashboard then reports "Test failed". This does **not**
mean the integration is broken — it means the endpoint was reached but the dummy
reference has no matching order. Verify the real flow with an actual transaction
(step 4) or the transaction simulator, not this button. Delivered notifications
(real and test) are listed under **View notification history**.

### Alternative: no tunnel, no gateway

For fast logic checks, POST a correctly signed body straight to `/notification`:
`signature_key = sha512(order_id + status_code + gross_amount + MIDTRANS_SERVER_KEY)`.
This exercises the settlement path with no external setup.

---

## Going live: what changes vs local (ngrok)

ngrok is a **development-only** tunnel that gives your laptop a temporary public URL.
When the app is deployed, you stop using ngrok entirely and point Midtrans at the
deployed server's real domain. Nothing about the notification *path*
(`/api/v1/payment/notification`) changes — only the host in front of it.

| Item | Local (development) | Production (deployed) |
| :--- | :--- | :--- |
| Public host | ngrok tunnel URL, e.g. `https://abc123.ngrok-free.app` | Your deployed domain, e.g. `https://module-2-miftahalrasyid.onrender.com` |
| Notification URL (Midtrans dashboard) | `https://abc123.ngrok-free.app/api/v1/payment/notification` | `https://<your-domain>/api/v1/payment/notification` |
| ngrok | Required (run `./ngrok_tunnel.sh`) | Not used at all |
| Database read/written | Your **local** Postgres | The **deployed** server's Postgres |
| Midtrans environment | Sandbox | Production |
| `MIDTRANS_SERVER_KEY` / `MIDTRANS_CLIENT_KEY` | Sandbox keys | Production keys |
| `MIDTRANS_IS_PRODUCTION` | `false` | `true` |
| Midtrans dashboard | Sandbox dashboard | Production dashboard (set the notification URL there separately) |

Checklist when the web goes live:

1. Deploy the app so it has a stable public HTTPS domain.
2. In the **production** Midtrans dashboard, set Payment Notification URL to
   `https://<your-domain>/api/v1/payment/notification`.
3. On the server, set env vars: production `MIDTRANS_SERVER_KEY` + `MIDTRANS_CLIENT_KEY`
   and `MIDTRANS_IS_PRODUCTION=true` (change these together).
4. Stop pointing Midtrans at any ngrok URL. ngrok is no longer part of the flow.
5. Keep the sandbox config for local development — the two environments have separate
   keys, dashboards, and notification URLs.

Note: the free ngrok URL changes every restart, which is fine for dev but is exactly
why it must never be used as a production notification URL — a deployed domain is stable.

---

## Configuration reference

Set in `.env` (see `.env.example`):

```env
MIDTRANS_SERVER_KEY=SB-Mid-server-...   # sandbox server key (use production key when live)
MIDTRANS_CLIENT_KEY=SB-Mid-client-...   # sandbox client key (use production key when live)
MIDTRANS_IS_PRODUCTION=false            # false -> sandbox endpoints; true -> production
```

When going live, swap in production keys **and** set `MIDTRANS_IS_PRODUCTION=true` together.
