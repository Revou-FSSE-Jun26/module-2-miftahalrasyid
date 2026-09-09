[![Review Assignment Due Date](https://classroom.github.com/assets/deadline-readme-button-22041afd0340ce965d47ae6ef1cefeee28c7c493a6346c4f15d667ab976d596c.svg)](https://classroom.github.com/a/wGq_UtnU)

# RevoShop (Backend) 
> A secure and scalable RESTful online store API e-commerce platform, built with Flask and PostgreSQL  — designed for teams that track work without heavy project management overhead.

## Overview

RevoShop is an intuitive e-commerce ecosystem that simplifies online transactions for buyers and sellers alike. Our secure database backed by PostgreSQL allows customers to track history and plan future purchases, while robust inventory management tools empower sellers to dynamically adjust stock levels to meet customer demand.

## Features

### Authentication & Authorization
- JWT-based authentication with access tokens
- Role-based access control (RBAC) with 4 roles: BUYER, SELLER, ADMIN, SUPERADMIN
- Field-level permission filtering per role per operation
- OAuth (Google) login support
- Email verification required before login
- Gmail alias normalization (dots/plus-addressing) to prevent duplicate accounts
- OAuth users blocked from setting/updating password
- Soft-deleted users cannot login

### Roles & Permissions

#### BUYER
- Default role assigned on registration
- Can browse products (read-only, limited fields)
- Can browse categories (read-only)
- Can create orders with status `PENDING` (cart/checkout — stock NOT deducted yet, address can be null). Order items reference a specific seller listing (`seller_product_id`)
- Can proceed to payment via `/api/v1/payment` which validates address and transitions order to `PAID`
- Can soft-delete (cancel) own orders only when status is `COMPLETED` or `CANCELED`
- Cannot delete orders with `PAID` or `PENDING` status
- Cannot transition order status back to `PENDING`
- Can read own orders only
- Can update own profile (email, password, age)
- Cannot create/update/delete catalog products or listings
- Cannot manage categories
- Cannot manage other users

#### SELLER
- Opt-in via `/api/v1/users/become-seller` (blocked if already seller or account deactivated)
- Can create **listings** via `POST /api/v1/seller-products/` (own only, auto-assigned to their user_id). A listing carries the seller's own price/stock/status/sku/title/images and references a shared catalog product. If the catalog product does not exist yet it is created automatically (find-or-create by barcode) — sellers do not touch the catalog `products` table directly
- Can update own listings (title, stock, price, sku) via `PUT /api/v1/seller-products/<id>`
- Can soft-delete own listings when not linked to a `PAID` order
- Can switch own listing status between `ACTIVE` and `INACTIVE` in either direction (`ACTIVE → INACTIVE` when out of stock / supply issues, `INACTIVE → ACTIVE` when restocked). Cannot set any other status (`PENDING`, `SUSPENDED`, `REJECTED` are admin-controlled) and cannot self-approve a `PENDING` listing
- Can read orders that contain their listings
- Can update order status (only for orders containing their listings)
- Cannot transition order status back to `PENDING`
- Can upload/delete listing images (own listings only)
- Cannot order their own listings (self-purchase prevention)
- Cannot be soft-deleted when they have active orders with `PAID` status
- Can only read the catalog and categories; cannot create/update/delete catalog products or categories
- Cannot delete users
- Cannot hard-delete anything except own uploaded images.

#### ADMIN
- Can create, read, update, and soft-delete categories
- When deleting categories, associated `category_items` junction records are also deleted (no orphan relations)
- Can create, read, update, and soft-delete **catalog products** (the shared spec) via `/api/v1/products/`
- May review a `PENDING` **listing** and either approve it (`PENDING → ACTIVE`) or reject it (`PENDING → REJECTED`) via `PUT /api/v1/seller-products/<id>`. On rejection the listing is also soft-deleted (`deleted_at` set) so it never appears in browse; rejection is terminal (no revival — the seller must submit a new listing)
- May suspend or reinstate an `ACTIVE` listing in either direction (`ACTIVE → SUSPENDED` when facing an issue, `SUSPENDED → ACTIVE` to reinstate). Suspension is always allowed and takes effect immediately — it is NOT blocked by existing `PAID` orders
- Setting a listing to `INACTIVE` or `SUSPENDED` immediately stops all new orders and payments for it (the purchase gate only allows `ACTIVE` listings), and soft-deletes that listing's `order_items` from orders still in `PENDING` order-status (unpaid carts). Existing `PAID` orders are never touched — they are honored and resolved through the normal order lifecycle (`PAID → COMPLETED` or `PAID → CANCELED` with refund)
- Can create, read, update, and soft-delete orders
- Can create, read, update, and soft-delete users (including role and is_active management)
- Can manage user roles EXCEPT `SUPERADMIN` — only a superadmin can grant the `SUPERADMIN` role (privilege-escalation guard, returns 403)
- Can delete uploaded images with bypass ownership
- Cannot hard-delete any resource
- Cannot create uploads

#### SUPERADMIN
- Full CRUD on all resources: `users`, `products` (catalog), `seller_products` (listings), `orders`, `address`, `profile` and junction tables `order_items`, `category_items`
- Can hard-delete any resource (permanent removal from database)
- Can create catalog products / listings / orders on behalf of other users
- Can bypass upload ownership checks
- Can manage roles and is_active flag on all users
- Is the only role that can grant the `SUPERADMIN` role to another user

### Orders & Cart
- Orders created with `PENDING` status (acts as cart — stock not deducted, address can be null). Each order item references a specific seller **listing** (`seller_product_id`), so the exact seller and price bought are preserved
- Only listings with status `ACTIVE` (not soft-deleted, whose catalog product is not soft-deleted) can be added to an order or paid for. Adding or paying for a non-`ACTIVE` listing (e.g. `INACTIVE`, `SUSPENDED`, `PENDING`, `REJECTED`) returns 400 with a generic "unavailable" message
- Payment endpoint (`/api/v1/payment`) processes the order:
  - Validates address: if no default address is set and none specified, returns `"default address is not set"`
  - On success: transitions status to `PAID`, deducts the listing's stock, sets delivery address
- Order status transitions enforced: `PAID → COMPLETED` or `PAID → CANCELED` only
- Seller and Buyer cannot transition order status back to `PENDING`
- On cancellation (PAID → CANCELED): stock automatically restored to the listing
- Buyer can only soft-delete orders with `COMPLETED` or `CANCELED` status
- Duplicate listings within same order prevented
- Subtotal, discount, tax, and total calculated automatically
- Query params on `GET /api/v1/orders/`: `status` (`PENDING`/`PAID`/`COMPLETED`/`CANCELED`), `sort` (`total`/`created_at`, prefix `-` for descending), plus `page`/`per_page`. Ownership scoping (buyer=own, seller=their listings, admin=all) is always enforced and cannot be overridden

### Catalog & Listings (products / seller_products)

The product model is split into two tables so multiple sellers can offer the same
item at their own price:

- **`products` (catalog)** — the shared, canonical spec of an item: `brand`, `name`,
  `description`, `model`, `color`, `size`, `barcode`, `specifications` (JSONB), plus
  category links. It holds **no** price, stock, status, or owner. Admin-curated; write
  access (`POST`/`PUT`/`DELETE /api/v1/products/`) is ADMIN/SUPERADMIN only. Reads are public.
  `barcode` is partial-unique (unique only when not null).
- **`seller_products` (listing)** — one seller's offer for a catalog product:
  `title`, `slug`, `price`, `stock`, `status`, `sku`, `images`, `product_id`, `user_id`.
  A seller has at most one (non-deleted) listing per catalog product
  (`UNIQUE(product_id, user_id)`).

#### Creating a listing (seller submits catalog + offer together)
- `POST /api/v1/seller-products/` takes both catalog fields and listing fields. The
  service **find-or-creates** the catalog product: if a non-deleted product with the
  same `barcode` exists it is reused, otherwise a new catalog row is created. When no
  barcode is given, a new catalog row is always created.
- The new listing always starts as `PENDING` (client-supplied status is ignored); an
  admin approves it before it becomes buyer-visible.

#### Listing status lifecycle
Status lives on the **listing** (`seller_products.status`): `PENDING` | `ACTIVE` |
`INACTIVE` | `SUSPENDED` | `REJECTED`.
  - `PENDING`: newly created by a seller, awaiting admin review. Not publicly visible.
  - `ACTIVE`: approved and publicly visible / purchasable.
  - `INACTIVE`: temporarily hidden by the seller (out of stock / supply issue).
  - `SUSPENDED`: hidden by an admin due to an issue.
  - `REJECTED`: admin rejected the pending listing; also soft-deleted. Terminal.
- Status transition matrix (enforced server-side; invalid transitions return 400):
  - SELLER (owner only): `ACTIVE → INACTIVE`, `INACTIVE → ACTIVE`
  - ADMIN / SUPERADMIN: `PENDING → ACTIVE`, `PENDING → REJECTED`, `ACTIVE → SUSPENDED`, `SUSPENDED → ACTIVE`, `ACTIVE → INACTIVE`, `INACTIVE → ACTIVE`
  - `REJECTED` is terminal for everyone (no revival)
- Status changes go through `PUT /api/v1/seller-products/<id>` (the `status` field is validated against the matrix based on caller role + ownership); there is no separate status endpoint.

#### Purchasability & the two-gate rule
A listing is purchasable only when its `status = ACTIVE` **and** its own `deleted_at IS NULL`
**and** its catalog product's `deleted_at IS NULL`. Adding or paying for anything else
returns 400 "unavailable".
- Setting a listing to `INACTIVE` or `SUSPENDED` is always allowed and takes effect
  immediately. Its two effects:
  1. New sales stop instantly — the purchase gate rejects add/pay for a non-`ACTIVE` listing.
  2. Cart cleanup (per-listing, cross-seller safe): only that listing's own `order_items`
     are soft-deleted, and only in orders still in `PENDING` order-status (unpaid carts).
     Other sellers' items in the same cart are untouched, the order is NOT deleted, and
     affected order totals are recomputed from remaining live items.
- Existing `PAID` orders are never modified when a listing is suspended/deactivated —
  `order_items` stay intact (price is snapshotted on the `order_item`) and are resolved
  through the normal order lifecycle.
- Rejecting a listing (`PENDING → REJECTED`) sets both `status = REJECTED` and `deleted_at`.

#### Deletion guards
- Deleting a listing (`DELETE /api/v1/seller-products/<id>`) is blocked when it is linked
  to active `PAID` orders (409). Deleting a catalog product (`DELETE /api/v1/products/<id>`)
  is blocked when any of its listings is linked to a `PAID` order.

#### Browse / visibility
- `GET /api/v1/seller-products/` (public) is the storefront: it returns every `ACTIVE`,
  in-stock listing whose catalog product is live, each row joined to its catalog spec and
  tagged with `min_price` (the cheapest price across all listings of that same catalog
  product, via a `MIN() OVER (PARTITION BY product_id)` window). Sorted by price ascending
  by default.
- `GET /api/v1/seller-products/mine` (auth) returns the caller's own listings in any
  non-deleted status (admin sees all).
- `GET /api/v1/products/` (public) lists catalog products that have at least one `ACTIVE`
  in-stock listing; admin/superadmin see all non-deleted catalog rows.
- Order detail (`GET /api/v1/orders/<id>` items) always shows the purchased listing's
  title and paid price, even if the listing is later hidden — order history reads from the
  `order_items` snapshot.
- Listing slug auto-generated from the listing title; catalog `barcode` partial-unique;
  stock tracked with DB-level `CHECK (stock >= 0)` on `seller_products`.
- Listing images uploaded via the uploads endpoint (resource `seller_products`).
- Query params on `GET /api/v1/seller-products/`: `search` (matches catalog brand/name/model
  and listing title, case-insensitive), `category_id`, `min_price`, `max_price`,
  `sort` (`price`/`title`/`created_at`, prefix `-` for descending), plus `page`/`per_page`.
- Query params on `GET /api/v1/products/`: `search` (catalog name), `category_id`,
  `category_name`, `sort` (`name`/`created_at`), plus `page`/`per_page`.

### Orders
- Cannot be deleted when order has `PAID` in status
- Paid orders should be refunded when 

### Categories
- Only ADMIN and SUPERADMIN can create/update/delete categories
- Seller and Buyer have read-only access
- When deleting a category, associated `category_items` junction records are also deleted (no orphan relations)
- Query params on `GET /api/v1/categories/`: `search` (name, case-insensitive), `sort` (`name`/`created_at`, prefix `-` for descending), plus `page`/`per_page`

### Users & Profiles
- Seller cannot be soft-deleted when they have active orders with `PAID` status
- Seller cannot order their own listings
- Privilege-escalation guard: only a superadmin can grant the `SUPERADMIN` role (admin attempts return 403)
- Become Seller flow with guard checks (already seller, deactivated account)
- Profile and address management
- Default address used for payment processing
- Query params on `GET /api/v1/users/`: `search` (username or email, case-insensitive), `sort` (`username`/`created_at`, prefix `-` for descending), plus `page`/`per_page`. Privileged filters `role` and `is_active` are honored only for ADMIN/SUPERADMIN and silently ignored for other roles

### Stock Management
- Stock deducted only upon successful payment (not on order creation)
- Stock restored on order cancellation or deletion of PAID orders
- DB-level constraint prevents negative stock

### Uploads
- Listing image upload with ownership enforcement (resource `seller_products`, images stored on the listing)
- Admin/Superadmin bypass ownership for image management
- Seller can only manage images for own listings
- Buyer cannot upload

### Logging
- Environment-aware logging driven by `FLASK_ENV` (`local`, `development`, `production`)
- **local:** all logs (DEBUG and up) to the console, no file
- **development / production:** console output plus an ERROR-only log file for efficiency
- Daily-rotating error log (`logs/error.log`) — a new file each day, keeping up to 1 year of history (configurable via `LOG_BACKUP_DAYS`)
- Optional overrides: `LOG_LEVEL`, `LOG_DIR`, `LOG_BACKUP_DAYS`

### Platform-Wide
- Role-based access control (RBAC) with field-level permission filtering
- XSS protection via nh3 HTML sanitization on all inputs
- Gmail alias normalization prevents duplicate accounts
- Password hashing with Werkzeug PBKDF2-SHA256
- Pagination on all list endpoints (default 10, max 30 per page)
- Unified soft/hard delete strategy with proper HTTP status codes (200, 400, 403, 404, 409, 500)
- IntegrityError handling on hard delete (FK constraint violations)
- Phone validation in +62 international format
- Health check endpoint (`/health`) reporting app and database status


## Tech Stack

- *Core Backend & Framework*
    - **Language:** Python 3.13.7
    - **Framework:** Flask 3.0
    - **Configuration:** python-dotenv
- *Database & ORM*
    - **Database Engine:** PostgreSQL 16
    - **ORM:** SQLAlchemy (Flask-SQLAlchemy)
    - **Migrations:** Flask-Migrate
    - **Database Management:** Dbeaver 22.0.2
- *Testing & Performance*
    - **Unit & Integration Testing:** pytest + pytest-flask
    - **Load & Performance Testing:** Locust
- *Production & Deployment*
    - **WSGI HTTP Server:** gunicorn
    - **Deployment Platform:** AWS

## Prerequisites
- Python 3.13.7 or higher
- PostgreSQL running locally (or a connection string to a remote instance)
- pip and virtualenv

## ERD

![ERD Diagram](docs/screenshots/ERD.png)

## 🔁 Route Handling flow (Flask-Smorest + SQLAlchemy)

Below graph is the data flow (Request & Response) from when the client hit the API to 
the state when exchanging data with PostgreSql


```mermaid

graph TD
    A[Client Request] --> B[Flask framework]
    B --> C[Smorest Blueprint Route]
    C --> D[Marshmallow Schema]
    D <--> E[(SQLAlchemy Models)]
    D --> F[Routes / Gate Keeper]
    F <--> G[Services]
    G <--> E
    E <--> H[(PostgreSQL Database)]

    %% 🎨 dark and light theme strategy (VS CODE & GITHUB ALL OK)
    
    classDef pink fill:#be6057,stroke:#e0847d,color:#ffffff,stroke-width:2px;
    
    classDef green fill:#2e7d32,stroke:#4caf50,color:#ffffff,stroke-width:2px;
    
    classDef blue fill:#0969da,stroke:#58a6ff,color:#ffffff,stroke-width:2px;
    
    classDef gray fill:#4a5568,stroke:#718096,color:#ffffff,stroke-width:1px;

    %% Applied the color class to each element 
    class A pink;       
    class C green;      
    class D blue;     
    class E,H gray;     
```
## 🔁 migration flow (Flask-migrate + alembic)
model -> flask alchemy-> flask migrate-> alembic -> sqlalchemy core

### 📋 Task & Responsibility

| Layer Component | File location | Library | Main Task |
| :--- | :--- | :--- | :--- |
| **Smorest API Gate** | `app/routes/v1/*.py` | flask-smorest | Managing Routes, HTTP methods (`GET`/`POST`), and Swagger UI Documentation. |
| **Validation Schema** | `app/schemas/*.py` | marshmallow_sqlalchemy<br>marshmallow | validate input data type, filtering output data, and storing custom error message. |
| **Data Model & Property** | `app/models/*.py` | flask<br>flask_sqlalchemy<br>sqlachemy | define database table and storing virtual attribute (exp: raw password for *hashing*)|
| **Business Logic Service** | `app/services/*.py` | flask | Handle all the business related logic and execution to database. |
| **Manage database migration** | `app/migration/*.py` | flask<br>flask_sqlalchemy<br>sqlachemy | Handle all the database upgrade and downgrade the database. |


## Installation
### 1. Clone & Setup Environment
Clone repositori, buat dan aktifkan *virtual environment*, serta install dependencies:
```bash
git clone https://github.com
cd module-2-miftahalrasyid
python -m venv venv
source venv/bin/activate

# Runtime only (production)
pip install -r requirements.txt

# Or, for development (includes testing, load testing, and security tools)
pip install -r requirements-dev.txt
```

### install postgresql 
Skip install if you already have postgresql
```bash
brew install postgresql
brew services start postgresql
psql postgres
# alter user posgres
ALTER USER postgres WITH PASSWORD 'password';
# in case of error, run next code
CREATE ROLE postgres WITH LOGIN SUPERUSER PASSWORD 'password';
# quit postgres
\q
```
### 2. Configure Local PostgreSQL Database
Buat database baru di PostgreSQL:
```bash
# create revoshop_db
createdb -U postgres revoshop_db
```
*(Alternatif via psql: `psql -U postgres`, lalu ketik `CREATE DATABASE revoshop_db;` dan `\q`).*

### 3. Setup Environment Variables (.env)
Buat file `.env` di root direktori:
```env
SQLALCHEMY_DATABASE_URI=postgresql://postgres:your_password@localhost:5432/revoshop_db
secrets; print(secrets.token_hex(32))")
JWT_SECRET_KEY=your-secret-key-here


GOOGLE_CLIENT_ID=your-google-client-id.apps.googleusercontent.com

EMAIL_USER=your-email@gmail.com
EMAIL_PASS=your-app-password
BASE_URL=your-localhost-url:port

TAX_PERCENT=11
CURRENCY=IDR
```

### 4. Database Migration, & Seeding
run migrations and *seeding*:
```bash
flask db upgrade
PYTHONPATH=. python seeds/initial_seed.py
```

## Testing
Tests use a separate PostgreSQL database (auto-created as `{your_db_name}_test`). Your production data is never touched.

**Current status:** 304 tests passing · 85% code coverage

### Unit & Integration Tests
```bash
# Run all tests with coverage
pytest tests/ --cov=app --cov-report=term-missing

# Run a specific test file
pytest tests/routes/v1/test_category_routes.py -v
```

Prerequisites: PostgreSQL running + `.env` configured. The test database is auto-created on first run.

### Load Testing (Locust)
```bash
# Start the dev server first
flask run --debug --port=8000

# Run Locust (opens web UI at http://localhost:8089)
locust -f locustfile.py --host=http://localhost:8000
```

Open `http://localhost:8089` in your browser, set the number of users and spawn rate, then start the test.

![Locust Load Test Results](docs/screenshots/locust-results.png)

### Security Audit
`audit.sh` runs a suite of security checks. It's report-friendly locally (missing tools produce warnings, not errors) and runs automatically in CI before Swagger deployment (a failed audit blocks the deploy).

```bash
# Optional: install the scanners for full coverage
pip install pip-audit bandit
brew install gitleaks   # macOS

# Run the audit
./audit.sh
```

What it checks:
- **Secrets** — scans for hardcoded credentials, API keys, tokens, and private keys (`gitleaks`, with a `grep` fallback)
- **Dependencies** — flags known CVEs in `requirements.txt` (`pip-audit`)
- **Static analysis** — detects insecure code patterns in `app/` (`bandit`)
- **Env hygiene** — confirms `.env` is gitignored, untracked, and absent from git history

Exit code is `0` if all critical checks pass, `1` otherwise.

## Usage
Start the development server:
```bash
flask run --debug --port=8000
```
The API will be available at `http://localhost:8000`.

### Payments (Midtrans) — expose the webhook with ngrok

Payment is processed asynchronously through Midtrans Snap: an order becomes `PAID`
only after Midtrans calls the webhook `POST /api/v1/payment/notification`. Because
Midtrans cannot reach `localhost`, you must expose your local server with a tunnel
during development. **If ngrok is not running, payments will never settle locally.**

Run these in two terminals (both must stay open):
```bash
# terminal 1 — the API
flask run --debug --port=8000

# terminal 2 — public tunnel to port 8000
./ngrok_tunnel.sh        # or: ngrok http 8000
```
ngrok prints a public HTTPS URL (e.g. `https://abc123.ngrok-free.app`). Put it in the
Midtrans dashboard under **Settings → Configuration → Payment Notification URL** as:
```
https://<your-ngrok-subdomain>.ngrok-free.app/api/v1/payment/notification
```
The free ngrok URL changes on every restart, so re-paste it each session. First-time
setup requires `ngrok config add-authtoken <YOUR_NGROK_AUTHTOKEN>`.

Full buyer/seller walkthrough, refund flow, and the dev-vs-production switch-over are in
[payment_steps_with_midtrans.md](./payment_steps_with_midtrans.md).

### Example Requests

**Get all products:**
```bash
curl http://localhost:8000/api/v1/products/
```

**Get a single product:**
```bash
curl http://localhost:8000/api/v1/products/1
```

**Login (get token):**
```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "justin@gmail.com", "password": "Password1234"}'
```

**Browse listings (public storefront):**
```bash
curl "http://localhost:8000/api/v1/seller-products/?search=mouse"
```

**Create a listing (requires seller/admin token; find-or-creates the catalog product, starts PENDING):**
```bash
curl -X POST http://localhost:8000/api/v1/seller-products/ \
  -H "Authorization: Bearer <your-token>" \
  -H "Content-Type: application/json" \
  -d '{"brand": "Logitech", "name": "wireless_mouse", "description": "Ergonomic wireless mouse", "barcode": "LOGI-MX-001", "title": "Logitech MX Master 3S - BNIB", "price": 499000, "stock": 50, "category_ids": [1]}'
```

**Update a listing (price/stock, or status transition):**
```bash
curl -X PUT http://localhost:8000/api/v1/seller-products/1 \
  -H "Authorization: Bearer <your-token>" \
  -H "Content-Type: application/json" \
  -d '{"price": 19999000, "stock": 30}'
```

**Approve a listing (admin: PENDING -> ACTIVE):**
```bash
curl -X PUT http://localhost:8000/api/v1/seller-products/1 \
  -H "Authorization: Bearer <admin-token>" \
  -H "Content-Type: application/json" \
  -d '{"status": "ACTIVE"}'
```

**Delete a listing (soft delete):**
```bash
curl -X DELETE http://localhost:8000/api/v1/seller-products/1 \
  -H "Authorization: Bearer <your-token>" \
  -H "Content-Type: application/json" \
  -d '{"action": "soft"}'
```

Access Swagger UI documentation on **[http://localhost:8000/swagger-ui](http://localhost:8000/swagger-ui)**.

## Business Logic

- **Auto Slug Generation** — Listing slugs are auto-generated from the listing title on creation. Duplicates get a numeric suffix (`-1`, `-2`, etc.). Slug regenerates when the title is updated.
- **Catalog Find-or-Create** — When a seller submits a listing, the catalog product is reused if a non-deleted product with the same `barcode` exists, otherwise a new catalog row is created (Option B). A seller may have only one listing per catalog product.
- **Deletion Guard** — Listings linked to active (PAID) orders cannot be deleted; a catalog product with any such listing cannot be deleted either. The API returns 409 with a clear message.
- **Image Lifecycle** — On soft or hard delete of a listing, associated image files are removed from disk and the `images` column is nullified. Upload failures roll back the file if the DB commit fails — no orphaned files.
- **Order Pricing** — Orders auto-calculate subtotal, tax (11%), and total from listing prices and quantities. Stock is deducted on payment settlement and restored on cancellation.
- **Stock Validation** — Orders fail if requested quantity exceeds the listing's available stock.
- **Email Normalization** — Gmail dots and aliases are normalized to prevent duplicate accounts (e.g., `j.doe@gmail.com` → `jdoe@gmail.com`).
- **Soft/Hard Delete Strategy** — All resources support soft delete (sets `deleted_at`). Superadmin can hard delete permanently via `{"action": "hard"}`.

## Seeding Objective

Populate the database with realistic data for development and testing:
- 32 users (1 superadmin, 1 admin, 5 sellers, 23 buyers, 2 inactive)
- 32 profiles with bios
- 31 addresses across Indonesia
- 10 categories
- 33 catalog products (spec sheets) with real brand names
- 33 seller listings (one per catalog product) with IDR pricing, stock, and status
- 39 category-product mappings
- 33 orders with various statuses
- 36 order items (each referencing a seller listing)

All seeded users use password: `Password1234`

### Key Accounts
| Role | Email |
|------|-------|
| Superadmin | funnyclown1112@gmail.com |
| Admin | mike@gmail.com |
| Seller | justin@gmail.com, arini@gmail.com |
| Buyer | budi@gmail.com, siti.nurhaliza@gmail.com |

## Step-by-Step Guide: Implementing HTML Request Features in Isolation 
>Creating new feature (endpoint: GET,POST) steps using (Flask-Smorest x marsmallow x flask-sqlalchemy x marsmallow-sqlalchemy) route stack


```mermaid
flowchart TD
    %% Struktur luar diatur TD (Top-Down) agar kelompok Flask berada di bawah
    %% classDef step fill:#2d3748,stroke:#4a5568,stroke-width:2px,color:#fff;
    classDef pink fill:#be6057,stroke:#e0847d,color:#ffffff,stroke-width:2px;

    subgraph Isolation_Layer ["Isolation Layer"]
        direction LR
        B["<b>1. schemas.py</b><br>Map Models Column to Marshmallow"]:::step
        --> A["<b>2. models.py</b><br>Create SQLAlchemy Models"]:::step 
        --> C["<b>3. services.py</b><br>Write Pure Business Logic"]:::step
    end

    subgraph Flask_Registration ["Flask Registration"]
        direction LR
        D["<b>4. routes.py</b><br>Connect HTTP Routes to Services"]:::step 
        --> E["<b>5. __init__.py (App Factory)</b><br>Register Blueprints to Core API"]:::step
    end

    %% KUNCI: Hubungkan Subgraph langsung ke Subgraph agar panahnya vertikal ke bawah
    Client_Request:::pink --> Isolation_Layer -->|Establish Connection to Flask| Flask_Registration

    %% Subgraph styling

    %% style Isolation_Layer fill:#202632,stroke:#4a5568,stroke-width:1px
    %% style Flask_Registration fill:#1a202c,stroke:#4a5568,stroke-width:1px

```

### Project Structure

```text
./
├── README.md
├── audit.sh
├── .github/
│   └── workflows/
│       └── deploy-swagger.yml
├── app/
│   ├── __init__.py
│   ├── extensions.py
│   ├── middleware/
│   │   ├── __init__.py
│   │   └── auth.py
│   ├── models/
│   │   ├── __init__.py
│   │   ├── address_model.py
│   │   ├── category_items_model.py
│   │   ├── category_model.py
│   │   ├── order_items_model.py
│   │   ├── order_model.py
│   │   ├── product_model.py
│   │   ├── seller_product_model.py
│   │   ├── profile_model.py
│   │   └── user_model.py
│   ├── permissions/
│   │   ├── __init__.py
│   │   └── field_filter.py
│   ├── routes/
│   │   ├── __init__.py
│   │   └── v1/
│   │       ├── __init__.py
│   │       ├── admin_routes_v1.py
│   │       ├── auth_routes_v1.py
│   │       ├── category_routes_v1.py
│   │       ├── orders_routes_v1.py
│   │       ├── payment_routes_v1.py
│   │       ├── product_routes_v1.py
│   │       ├── seller_products_routes_v1.py
│   │       ├── upload_routes_v1.py
│   │       └── users_routes_v1.py
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── address_schema.py
│   │   ├── auth_schema.py
│   │   ├── category_schema.py
│   │   ├── order_item_schema.py
│   │   ├── order_schema.py
│   │   ├── payment_schema.py
│   │   ├── product_schema.py
│   │   ├── profile_schema.py
│   │   ├── query_schema.py
│   │   ├── seller_product_schema.py
│   │   └── user_schema.py
│   ├── services/
│   │   ├── __init__.py
│   │   ├── address_service.py
│   │   ├── auth_service.py
│   │   ├── category_service.py
│   │   ├── midtrans_client.py
│   │   ├── order_service.py
│   │   ├── payment_service.py
│   │   ├── product_service.py
│   │   ├── profile_service.py
│   │   ├── seller_product_service.py
│   │   ├── upload_service.py
│   │   └── user_service.py
│   └── utils/
│       ├── __init__.py
│       ├── logger.py
│       ├── pagination.py
│       └── sanitizer.py
├── audit.sh*
├── docs/
│   ├── payment_steps_with_midtrans.md
│   ├── queries.sql
│   ├── requirements.md
│   ├── schema.sql
│   ├── screenshots/
│   │   ├── ERD.png
│   │   ├── locust-results.png
│   │   ├── postman-delete.png
│   │   ├── postman-get.png
│   │   ├── postman-post.png
│   │   └── postman-put.png
│   └── seed.sql
├── folder_tree.sh*
├── instance/
│   ├── t.db
│   ├── temp.db
│   └── temp_check.db
├── locust_bash.sh
├── locustfile.py
├── migrations/
│   ├── README
│   ├── _archive_versions/
│   │   ├── 0268dfcb6edb_add_profiles_and_addresses_tables_.py
│   │   ├── 06c257caa915_add_uuid_column_to_products.py
│   │   ├── 1a42d12c6f44_rename_products_quantity_column_to_.py
│   │   ├── 29d20ad1e7a2_add_slug_images_updated_at_to_products.py
│   │   ├── 37490e1a0463_add_username_and_role_enum_to_users.py
│   │   ├── 3ce39395ca90_alter_orders_layout_and_data_types.py
│   │   ├── 503a9a24193e_add_deleted_at_and_change_all_to_server_.py
│   │   ├── 7633e2e310ef_convert_order_items_from_junction_table_.py
│   │   ├── 815a83d2ddfb_add_deleted_at_to_orders.py
│   │   ├── 9a575b777f47_change_provider_column_from_string_to_.py
│   │   ├── 9f84e4623f17_add_pricing_fields_to_orders.py
│   │   ├── bf1bb0ac101e_add_is_active_and_sku_to_products.py
│   │   ├── c00af829578d_fix_junction_mapping_to_string.py
│   │   ├── c7f2cbb27adc_change_role_to_roles_user_table.py
│   │   ├── d95589515a54_add_deleted_at_to_categories_and_server_.py
│   │   ├── e5dadb8947a1_convert_order_items_to_pure_many_to_.py
│   │   ├── e6f0237835c7_update_orderstatus_enum_values.py
│   │   └── fb1b2de14c14_add_deleted_at_on_user.py
│   ├── alembic.ini
│   ├── env.py
│   ├── script.py.mako
│   └── versions/
│       ├── 938979f6db37_baseline_schema.py
│       └── c4376e96a7c7_add_payment_ref_and_payment_status_to_.py
├── ngrok_tunnel.sh*
├── readme_japanese.md
├── requirements-dev.txt
├── requirements.txt
├── run.py
├── seeds/
│   └── initial_seed.py
├── test_upload.py
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   ├── middleware/
│   │   ├── __init__.py
│   │   └── test_auth.py
│   ├── permissions/
│   │   ├── __init__.py
│   │   └── test_field_filter.py
│   ├── routes/
│   │   ├── __init__.py
│   │   └── v1/
│   │       ├── __init__.py
│   │       ├── test_admin_routes.py
│   │       ├── test_auth_routes.py
│   │       ├── test_category_routes.py
│   │       ├── test_order_routes.py
│   │       ├── test_product_routes.py
│   │       ├── test_upload_routes.py
│   │       └── test_user_routes.py
│   ├── services/
│   │   ├── __init__.py
│   │   ├── test_address_service.py
│   │   ├── test_address_service_integration.py
│   │   ├── test_auth_service.py
│   │   ├── test_category_service.py
│   │   ├── test_order_service.py
│   │   ├── test_payment_service.py
│   │   ├── test_product_service.py
│   │   ├── test_profile_service.py
│   │   ├── test_upload_service.py
│   │   └── test_user_service.py
│   └── utils/
│       ├── __init__.py
│       ├── test_pagination.py
│       └── test_sanitizer.py
├── unit_test_and_integration.md
└── uploads/
    └── products/
```


## API Reference

Github Pages Swagger documentation available at **[https://revou-fsse-jun26.github.io/module-2-miftahalrasyid/](https://revou-fsse-jun26.github.io/module-2-miftahalrasyid/)**

Full interactive documentation available online at **[https://module-2-miftahalrasyid.onrender.com/swagger-ui](https://module-2-miftahalrasyid.onrender.com/swagger-ui)**.

### Auth

| Method | Endpoint | Description | Auth |
| :--- | :--- | :--- | :---: |
| `POST` | `/api/v1/auth/register` | Register new user | - |
| `POST` | `/api/v1/auth/login` | Login and get JWT | - |
| `POST` | `/api/v1/auth/oauth/google` | Google OAuth login | - |
| `GET` | `/api/v1/auth/email_confirmation` | Verify email | - |

### Users

| Method | Endpoint | Description | Auth |
| :--- | :--- | :--- | :---: |
| `GET` | `/api/v1/users/` | List users | Bearer |
| `POST` | `/api/v1/users/` | Create user | Bearer |
| `GET` | `/api/v1/users/<id>` | Get user | Bearer |
| `PUT` | `/api/v1/users/<id>` | Update user | Bearer |
| `DELETE` | `/api/v1/users/<id>` | Delete user | Bearer |
| `GET` | `/api/v1/users/me` | Get own profile | Bearer |
| `PUT` | `/api/v1/users/me/profile` | Update own profile | Bearer |
| `POST` | `/api/v1/users/become-seller` | Become seller | Bearer |
| `GET` | `/api/v1/users/me/addresses` | List addresses | Bearer |
| `POST` | `/api/v1/users/me/addresses` | Create address | Bearer |
| `GET` | `/api/v1/users/me/addresses/<id>` | Get address | Bearer |
| `PUT` | `/api/v1/users/me/addresses/<id>` | Update address | Bearer |
| `DELETE` | `/api/v1/users/me/addresses/<id>` | Delete address | Bearer |

### Products (catalog)

Catalog products are the shared spec. Reads are public; writes are ADMIN/SUPERADMIN only.

| Method | Endpoint | Description | Auth |
| :--- | :--- | :--- | :---: |
| `GET` | `/api/v1/products/` | List catalog products (with active listings) | - |
| `POST` | `/api/v1/products/` | Create catalog product (admin/superadmin) | Bearer |
| `GET` | `/api/v1/products/<id>` | Get catalog product | - |
| `PUT` | `/api/v1/products/<id>` | Update catalog product (admin/superadmin) | Bearer |
| `DELETE` | `/api/v1/products/<id>` | Delete catalog product (admin/superadmin) | Bearer |

### Seller Products (listings)

A seller's per-offer listing (price/stock/status/title/images) referencing a catalog product.

| Method | Endpoint | Description | Auth |
| :--- | :--- | :--- | :---: |
| `GET` | `/api/v1/seller-products/` | Browse listings (public storefront, tagged with `min_price`) | - |
| `POST` | `/api/v1/seller-products/` | Create a listing (find-or-creates catalog; starts `PENDING`) | Bearer |
| `GET` | `/api/v1/seller-products/mine` | List the caller's own listings (any status) | Bearer |
| `GET` | `/api/v1/seller-products/<id>` | Get a listing | - |
| `PUT` | `/api/v1/seller-products/<id>` | Update listing / status transition (seller or admin) | Bearer |
| `DELETE` | `/api/v1/seller-products/<id>` | Delete a listing (own, or admin) | Bearer |

### Categories

| Method | Endpoint | Description | Auth |
| :--- | :--- | :--- | :---: |
| `GET` | `/api/v1/categories/` | List categories | - |
| `POST` | `/api/v1/categories/` | Create category | Bearer |
| `GET` | `/api/v1/categories/<id>` | Get category | - |
| `PUT` | `/api/v1/categories/<id>` | Update category | Bearer |
| `DELETE` | `/api/v1/categories/<id>` | Delete category | Bearer |

### Orders

| Method | Endpoint | Description | Auth |
| :--- | :--- | :--- | :---: |
| `GET` | `/api/v1/orders/` | List orders | Bearer |
| `POST` | `/api/v1/orders/` | Create order | Bearer |
| `GET` | `/api/v1/orders/<id>` | Get order | Bearer |
| `PUT` | `/api/v1/orders/<id>` | Update order status | Bearer |
| `DELETE` | `/api/v1/orders/<id>` | Delete order | Bearer |
| `GET` | `/api/v1/orders/<id>/products` | Products in order | Bearer |

### Payment

| Method | Endpoint | Description | Auth |
| :--- | :--- | :--- | :---: |
| `POST` | `/api/v1/payment/` | Initiate Midtrans Snap payment for a PENDING order (returns snap_token + redirect_url) | Bearer |
| `POST` | `/api/v1/payment/notification` | Midtrans webhook — settlement transitions order to PAID. Called by Midtrans, not the client | - |

> Local development requires an ngrok tunnel so Midtrans can reach the webhook — see [Payments (Midtrans)](#payments-midtrans--expose-the-webhook-with-ngrok) under Usage and [payment_steps_with_midtrans.md](./payment_steps_with_midtrans.md).

### Uploads

| Method | Endpoint | Description | Auth |
| :--- | :--- | :--- | :---: |
| `POST` | `/api/v1/uploads/` | Upload image | Bearer |
| `DELETE` | `/api/v1/uploads/` | Delete image | Bearer |

### Admin

| Method | Endpoint | Description | Auth |
| :--- | :--- | :--- | :---: |
| `GET` | `/api/v1/admin/products` | All products (inc. deleted/inactive) | Bearer |
| `GET` | `/api/v1/admin/users/<id>/orders` | User's order history | Bearer |
| `GET` | `/api/v1/admin/orders/<id>/products` | Products in any order | Bearer |

### System

Infrastructure endpoints (not versioned, not in Swagger).

| Method | Endpoint | Description | Auth |
| :--- | :--- | :--- | :---: |
| `GET` | `/api` | API root — returns name, version, and links | - |
| `GET` | `/health` | Health check (app + database status) | - |
| `GET` | `/uploads/<filepath>` | Serve uploaded image file | - |

### Postman Examples

#### GET
![GET Request](docs/screenshots/postman-get.png)

#### POST
![POST Request](docs/screenshots/postman-post.png)

#### PUT
![PUT Request](docs/screenshots/postman-put.png)

#### DELETE
![DELETE Request](docs/screenshots/postman-delete.png)

> All protected endpoints require a Bearer token in the `Authorization` header. Obtain a token via `POST /api/v1/auth/login` or `POST /api/v1/auth/register`.

## Contributing
Read [CONTRIBUTING.md](./CONTRIBUTING.md) for our pull request process, coding standards, and commit message format.
## License
[MIT](./LICENSE) © 2026 RevoShop Team

