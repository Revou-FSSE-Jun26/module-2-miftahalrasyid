[![Review Assignment Due Date](https://classroom.github.com/assets/deadline-readme-button-22041afd0340ce965d47ae6ef1cefeee28c7c493a6346c4f15d667ab976d596c.svg)](https://classroom.github.com/a/wGq_UtnU)

# RevoShop (Backend) 
> A secure and scalable RESTful online store API e-commerce platform, built with Flask and PostgreSQL  — designed for teams that track work without heavy project management overhead.

## Overview

RevoShop is an intuitive e-commerce ecosystem that simplifies online transactions for buyers and sellers alike. Our secure database backed by PostgreSQL allows customers to track history and plan future purchases, while robust inventory management tools empower sellers to dynamically adjust stock levels to meet customer demand.

## Features

- Users can register on RevoShop.
- Users receive an email confirmation after registering.
- Users can log in using their registered email and password.
- Users can have buyer and seller features.
- Users can Create, Update, and Delete a `products`
- Users can Create, Update, and Delete a `categories`
- Users can group their `products` into `categories`
- Users can place an order through junction table of `order_items` 

## Tech Stack

- *Core Backend & Framework*
    - **Language:** Python 3.13.7
    - **Framework:** Flask 3.0
    - **Configuration:** python-dotenv
- *Database & ORM*
    - **Database Engine:** PostgreSQL 16
    - **ORM:** SQLAlchemy (Flask-SQLAlchemy)
    - **Migrations:** Flask-Migrate
    - **Database Management:** pgAdmin 4
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

## Installation
```bash
# 1. Clone the repository
git clone https://github.com/Revou-FSSE-Jun26/module-2-miftahalrasyid.git
cd module-2-miftahalrasyid
# 2. Create and activate a virtual environment
python -m venv venv
source venv/bin/activate        # Windows: venvScriptsactivate
# 3. Install dependencies
pip install -r requirements.txt
# install postgresql dari homebrew
brew install postgresql
# nyalakan postgres
brew services start postgresql
# masuk terminal postgres
psql postgres
# alter user posgres
ALTER USER postgres WITH PASSWORD 'root';
# jika error lakukan yang dibawah
# set login superuser for postgres
CREATE ROLE postgres WITH LOGIN SUPERUSER PASSWORD 'root';
# keluar postgres
\q
# buat database revoshop_db
createdb -U postgres revoshop_db

# 4. Set environment variables
export DATABASE_URL=postgresql://postgres:root@localhost/revoshop_db
export SECRET_KEY=root

# Build the tables using manual postgresql file
psql -U postgres -d revoshop_db -f docs/schema.sql
# Insert seed data into the newly created tables
psql -U postgres -d revoshop_db -f docs/seed.sql
```

## Usage
Start the development server:
```bash
flask run
```
The API will be available at `http://localhost:5000`.
Example request — create a new task:
```bash
curl -X POST http://localhost:5000/tasks \
  -H "Authorization: Bearer <your-token>" \
  -H "Content-Type: application/json" \
  -d '{"title": "Write unit tests", "priority": "high"}'
```

## API Reference

### 🧑 User Module

| Method | Path | Description | Authentication |
| :--- | :--- | :--- | :---: |
| <kbd>POST</kbd> | `/api/v1/auth/login` | Authenticate user & get token | None |
| <kbd>GET</kbd> | `/api/v1/users` | Get list of all users | `Bearer Token` |
| <kbd>POST</kbd> | `/api/v1/users` | Register a new user | `Bearer Token` |

### 📦 Product Module

| Method | Path | Description | Authentication |
| :--- | :--- | :--- | :---: |
| <kbd>POST</kbd> | `/api/v1/products` | Create a new product | `Bearer Token` |
| <kbd>GET</kbd> | `/api/v1/products` | List all products | None |
| <kbd>GET</kbd> | `/api/v1/products/{id}` | Get product details by ID | None |
| <kbd>PUT</kbd> | `/api/v1/products/{id}` | Update product details | `Bearer Token` |
| <kbd>DELETE</kbd> | `/api/v1/products/{id}` | Remove a product | `Bearer Token` |

### 📦 Category Module

| Method | Path | Description | Authentication |
| :--- | :--- | :--- | :---: |
| <kbd>POST</kbd> | `/api/v1/categories` | Create a new category | `Bearer Token` |
| <kbd>GET</kbd> | `/api/v1/categories` | List all category | None |
| <kbd>GET</kbd> | `/api/v1/categories/{id}` | Get a specific category along with its products| None |
| <kbd>PUT</kbd> | `/api/v1/categories/{id}` | Update category  | `Bearer Token` |
| <kbd>DELETE</kbd> | `/api/v1/categories/{id}` | Remove a category | `Bearer Token` |

### 📦 Order Module

| Method | Path | Description | Authentication |
| :--- | :--- | :--- | :---: |
| <kbd>POST</kbd> | `/api/v1/orders` | Place a new order linked to the logged-in user | `Bearer Token` |
| <kbd>GET</kbd> | `/api/v1/orders` | List all orders for the current user | None |
| <kbd>GET</kbd> | `/api/v1/orders/{id}` | View a specific order with its order items and product details | None |
| <kbd>PUT</kbd> | `/api/v1/orders/{id}` | Update category  | `Bearer Token` |
| <kbd>DELETE</kbd> | `/api/v1/orders/{id}` | Delete an order | `Bearer Token` |


> **Note:** All protected endpoints require a Bearer token in the `Authorization` header. Obtain a token via `POST /auth/login`.

## Contributing
Read [CONTRIBUTING.md](./CONTRIBUTING.md) for our pull request process, coding standards, and commit message format.
## License
[MIT](./LICENSE) © 2026 RevoShop Team

