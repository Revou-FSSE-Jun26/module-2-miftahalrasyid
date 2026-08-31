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
- Can create orders with status `PENDING` (cart/checkout — stock NOT deducted yet, address can be null)
- Can proceed to payment via `/api/v1/payment` which validates address and transitions order to `PAID`
- Can soft-delete (cancel) own orders only when status is `COMPLETED` or `CANCELED`
- Cannot delete orders with `PAID` or `PENDING` status
- Cannot transition order status back to `PENDING`
- Can read own orders only
- Can update own profile (email, password, age)
- Cannot create/update/delete products
- Cannot manage categories
- Cannot manage other users

#### SELLER
- Opt-in via `/api/v1/users/become-seller` (blocked if already seller or account deactivated)
- Can create products (own only, auto-assigned to their user_id)
- Can update own products (name, stock, brand, description, price, sku, categories)
- Can soft-delete own products when status IS NOT `PAID` in orders
- Can read orders that contain their products
- Can update order status (only for orders containing their products)
- Cannot transition order status back to `PENDING`
- Can upload/delete product images (own products only)
- Cannot order their own products (self-purchase prevention)
- Cannot be soft-deleted when they have active orders with `PAID` status
- Can only read categories and assign them to their products
- Cannot create, update, or delete categories
- Cannot delete users
- Cannot hard-delete anything except own uploaded images.

#### ADMIN
- Can create, read, update, and soft-delete categories
- When deleting categories, associated `category_items` junction records are also deleted (no orphan relations)
- Can create, read, update, and soft-delete products (including on behalf of other users)
- Can create, read, update, and soft-delete orders
- Can create, read, update, and soft-delete users (including role and is_active management)
- Can manage user roles EXCEPT `SUPERADMIN` — only a superadmin can grant the `SUPERADMIN` role (privilege-escalation guard, returns 403)
- Can delete uploaded images with bypass ownership
- Cannot hard-delete any resource
- Cannot create uploads

#### SUPERADMIN
- Full CRUD on all resources: `users`, `products`, `orders`, `address`, `profile` and junction tables `order_items`, `category_items`
- Can hard-delete any resource (permanent removal from database)
- Can create products/orders on behalf of other users
- Can bypass upload ownership checks
- Can manage roles and is_active flag on all users
- Is the only role that can grant the `SUPERADMIN` role to another user

### Orders & Cart
- Orders created with `PENDING` status (acts as cart — stock not deducted, address can be null)
- Payment endpoint (`/api/v1/payment`) processes the order:
  - Validates address: if no default address is set and none specified, returns `"default address is not set"`
  - On success: transitions status to `PAID`, deducts product stock, sets delivery address
- Order status transitions enforced: `PAID → COMPLETED` or `PAID → CANCELED` only
- Seller and Buyer cannot transition order status back to `PENDING`
- On cancellation (PAID → CANCELED): stock automatically restored
- Buyer can only soft-delete orders with `COMPLETED` or `CANCELED` status
- Duplicate products within same order prevented
- Subtotal, discount, tax, and total calculated automatically

### Products
- CRUD with ownership enforcement (only owner or admin+ can update/delete)
- Cannot be deleted (soft or hard) when linked to active orders with `PAID` status (returns 409)
- Auto-generated slug from product name
- Stock tracked with DB-level `CHECK (stock >= 0)` constraint
- Category assignment via many-to-many relationship through `category_items` junction table
- Product image upload support

### Categories
- Only ADMIN and SUPERADMIN can create/update/delete categories
- Seller and Buyer have read-only access
- When deleting a category, associated `category_items` junction records are also deleted (no orphan relations)

### Users & Profiles
- Seller cannot be soft-deleted when they have active orders with `PAID` status
- Seller cannot order their own products
- Privilege-escalation guard: only a superadmin can grant the `SUPERADMIN` role (admin attempts return 403)
- Become Seller flow with guard checks (already seller, deactivated account)
- Profile and address management
- Default address used for payment processing

### Stock Management
- Stock deducted only upon successful payment (not on order creation)
- Stock restored on order cancellation or deletion of PAID orders
- DB-level constraint prevents negative stock

### Uploads
- Product image upload with ownership enforcement
- Admin/Superadmin bypass ownership for image management
- Seller can only manage images for own products
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

**Current status:** 292 tests passing · 84% code coverage

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

**Create a product (requires seller/admin token):**
```bash
curl -X POST http://localhost:8000/api/v1/products/ \
  -H "Authorization: Bearer <your-token>" \
  -H "Content-Type: application/json" \
  -d '{"name": "wireless_mouse", "brand": "Logitech", "description": "Ergonomic wireless mouse", "price": 499000, "stock": 50, "category_ids": [1]}'
```

**Update a product:**
```bash
curl -X PUT http://localhost:8000/api/v1/products/1 \
  -H "Authorization: Bearer <your-token>" \
  -H "Content-Type: application/json" \
  -d '{"price": 19999000, "stock": 30}'
```

**Delete a product (soft delete):**
```bash
curl -X DELETE http://localhost:8000/api/v1/products/1 \
  -H "Authorization: Bearer <your-token>" \
  -H "Content-Type: application/json" \
  -d '{"action": "soft"}'
```

Access Swagger UI documentation on **[http://localhost:8000/swagger-ui](http://localhost:8000/swagger-ui)**.

## Business Logic

- **Auto Slug Generation** — Product slugs are auto-generated from the product name on creation. Duplicates get a numeric suffix (`-1`, `-2`, etc.). Slug regenerates when name is updated.
- **Deletion Guard** — Products linked to active (PAID) orders cannot be deleted. The API returns a 409 with a clear message.
- **Image Lifecycle** — On soft or hard delete of a product, all associated image files are removed from disk and the `images` column is nullified. Upload failures roll back the file if the DB commit fails — no orphaned files.
- **Order Pricing** — Orders auto-calculate subtotal, tax (11%), and total from product prices and quantities. Stock is deducted on order creation and restored on cancellation.
- **Stock Validation** — Orders fail if requested quantity exceeds available stock.
- **Email Normalization** — Gmail dots and aliases are normalized to prevent duplicate accounts (e.g., `j.doe@gmail.com` → `jdoe@gmail.com`).
- **Soft/Hard Delete Strategy** — All resources support soft delete (sets `deleted_at`). Superadmin can hard delete permanently via `{"action": "hard"}`.

## Seeding Objective

Populate the database with realistic data for development and testing:
- 32 users (1 superadmin, 1 admin, 5 sellers, 23 buyers, 2 inactive)
- 32 profiles with bios
- 31 addresses across Indonesia
- 10 categories
- 32 products with real brand names and IDR pricing
- 39 category-product mappings
- 32 orders with various statuses
- 35 order items

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
│   │   └── user_schema.py
│   ├── services/
│   │   ├── __init__.py
│   │   ├── address_service.py
│   │   ├── auth_service.py
│   │   ├── category_service.py
│   │   ├── order_service.py
│   │   ├── payment_service.py
│   │   ├── product_service.py
│   │   ├── profile_service.py
│   │   ├── upload_service.py
│   │   └── user_service.py
│   └── utils/
│       ├── __init__.py
│       ├── pagination.py
│       └── sanitizer.py
├── docs/
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
├── locustfile.py
├── migrations/
│   ├── README
│   ├── alembic.ini
│   ├── env.py
│   ├── script.py.mako
│   └── versions/
│       ├── 0268dfcb6edb_add_profiles_and_addresses_tables_.py
│       ├── 06c257caa915_add_uuid_column_to_products.py
│       ├── 1a42d12c6f44_rename_products_quantity_column_to_.py
│       ├── 29d20ad1e7a2_add_slug_images_updated_at_to_products.py
│       ├── 37490e1a0463_add_username_and_role_enum_to_users.py
│       ├── 3ce39395ca90_alter_orders_layout_and_data_types.py
│       ├── 503a9a24193e_add_deleted_at_and_change_all_to_server_.py
│       ├── 7633e2e310ef_convert_order_items_from_junction_table_.py
│       ├── 815a83d2ddfb_add_deleted_at_to_orders.py
│       ├── 9a575b777f47_change_provider_column_from_string_to_.py
│       ├── 9f84e4623f17_add_pricing_fields_to_orders.py
│       ├── bf1bb0ac101e_add_is_active_and_sku_to_products.py
│       ├── c00af829578d_fix_junction_mapping_to_string.py
│       ├── c7f2cbb27adc_change_role_to_roles_user_table.py
│       ├── d95589515a54_add_deleted_at_to_categories_and_server_.py
│       ├── e5dadb8947a1_convert_order_items_to_pure_many_to_.py
│       ├── e6f0237835c7_update_orderstatus_enum_values.py
│       └── fb1b2de14c14_add_deleted_at_on_user.py
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

Full interactive documentation available at **[http://localhost:8000/swagger-ui](http://localhost:8000/swagger-ui)** when running locally.

Github Pages Swagger documentation available at **[https://revou-fsse-jun26.github.io/module-2-miftahalrasyid/](https://revou-fsse-jun26.github.io/module-2-miftahalrasyid/)**

Full interactive documentation available at **[https://module-2-miftahalrasyid.onrender.com/swagger-ui](https://module-2-miftahalrasyid.onrender.com/swagger-ui)** when running on render.

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

### Products

| Method | Endpoint | Description | Auth |
| :--- | :--- | :--- | :---: |
| `GET` | `/api/v1/products/` | List products | - |
| `POST` | `/api/v1/products/` | Create product | Bearer |
| `GET` | `/api/v1/products/<id>` | Get product | - |
| `PUT` | `/api/v1/products/<id>` | Update product | Bearer |
| `DELETE` | `/api/v1/products/<id>` | Delete product | Bearer |

### Categories

| Method | Endpoint | Description | Auth |
| :--- | :--- | :--- | :---: |
| `GET` | `/api/v1/categories/` | List categories | - |
| `POST` | `/api/v1/categories/` | Create category | Bearer |
| `GET` | `/api/v1/categories/<id>` | Get category | - |
| `PUT` | `/api/v1/categories/<id>` | Update category | Bearer |
| `DELETE` | `/api/v1/categories/<id>` | Delete category | Bearer |
| `GET` | `/api/v1/categories/<id>/products` | Products in category | - |

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
| `POST` | `/api/v1/payment/` | Process payment for PENDING order | Bearer |

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

