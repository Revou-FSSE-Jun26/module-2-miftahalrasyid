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

![ERD_picture](./docs/ERD.png)

### Project Structure

```text
./
├── README.md
├── app/
│   ├── __init__.py
│   ├── models/
│   │   ├── __init__.py
│   │   ├── category_items_model.py
│   │   ├── category_model.py
│   │   ├── order_items_model.py
│   │   ├── order_model.py
│   │   ├── product_model.py
│   │   └── user_model.py
│   ├── routes/
│   │   ├── __init__.py
│   │   └── v1/
│   │       ├── __init__.py
│   │       ├── auth_routes_v1.py
│   │       ├── orders_routes_v1.py
│   │       ├── product_routes_v1.py
│   │       └── users_routes_v1.py
│   └── services/
│       ├── __init__.py
│       └── user_service.py
├── docs/
│   ├── ERD.png
│   ├── queries.sql
│   ├── requirements.md
│   ├── schema.sql
│   └── seed.sql
├── migrations/
│   ├── README
│   ├── alembic.ini
│   ├── env.py
│   ├── script.py.mako
│   └── versions/
│       ├── 37490e1a0463_add_username_and_role_enum_to_users.py
│       ├── 3ce39395ca90_alter_orders_layout_and_data_types.py
│       ├── c00af829578d_fix_junction_mapping_to_string.py
│       └── e5dadb8947a1_convert_order_items_to_pure_many_to_.py
├── requirements.txt
└── run.py
```

## Installation
```bash
# 1. Clone the repository
git clone https://github.com/Revou-FSSE-Jun26/module-2-miftahalrasyid.git
cd module-2-miftahalrasyid

# 2. Create and activate a virtual environment
python -m venv venv
source venv/bin/activate       
 # Windows: venvScriptsactivate

# 3. Install dependencies
pip install -r requirements.txt
# install postgresql 
brew install postgresql
# turn on postgres service
brew services start postgresql
# enter postgres terminal
psql postgres
# alter user posgres
ALTER USER postgres WITH PASSWORD 'root';
# in case of error, run next code
# set login superuser for postgres
CREATE ROLE postgres WITH LOGIN SUPERUSER PASSWORD 'root';
# quit postgres
\q
# create revoshop_db
createdb -U postgres revoshop_db

# 4. Set environment variables
export DATABASE_URL=postgresql://postgres:root@localhost/revoshop_db
export SECRET_KEY=root

# Build the tables using manual postgresql file
psql -U postgres -d revoshop_db -f docs/schema.sql
# Insert seed data into the newly created tables
psql -U postgres -d revoshop_db -f docs/seed.sql

# 1. Create the migrations folder structure
flask db init

# 2. Let Alembic scan your files and auto-generate the script
flask db migrate -m "complete baseline architecture"

# 3. Mark the database as up-to-date WITHOUT running any raw SQL on your Postgres server
flask db stamp head
```

## Usage
Start the development server:
```bash
flask run --port=8000
```
The API will be available at `http://localhost:8000`.
Example request — create a new task:
```bash
curl -X POST http://localhost:8000 \
  -H "Authorization: Bearer <your-token>" \
  -H "Content-Type: application/json" \
  -d '{"title": "Write unit tests", "priority": "high"}'
```

## API Reference

### 🧑 User Module

#### 1. _Get All Users_

| Method | Path | Description | Authentication |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/v1/users` | Get list of all users | None |
 
##### Response
> **Body**
> ```json
> {
>     "data": [
>         {
>             "age": 27,
>             "created_at": "2026-08-01T20:11:02.118738+07:00",
>             "email": "budi@gmail.com",
>             "id": 1,
>             "is_active": false,
>             "provider": "password_hash",
>             "provider_key": "8c6976e5b5410415bde908bd4dee15dfb167a9c873fc4bb8a81f6f2ab448a918",
>             "role": ["BUYER"],
>             "username": "budi"
>         },
>         {
>             "age": 27,
>             "created_at": "2026-08-01T20:11:02.118738+07:00",
>             "email": "husni@gmail.com",
>             "id": 3,
>             "is_active": false,
>             "provider": "password_hash",
>             "provider_key": "e10adc3949ba59abbe56e057f20f883e28b4b4dbd33b58c4886d22698e7341ea",
>             "role": ["BUYER"],
>             "username": "husni"
>         },
>         {
>
>             "age": 18,
>             "created_at": "2026-08-12T01:02:44.353652+07:00",
>             "email": "mike@gmail.com",
>             "id": 10,
>             "is_active": false,
>             "provider": "password_hash",
>             "provider_key": "1fb0ab1378099448c8800dd96f25409ec10e9ea802c0bcadbf8d322b3e9f94ec",
>             "role": ["BUYER"],
>             "username": "mike"
>         }
>     ],
>     "message": "Users retrieved successfully.",
>     "success": true
> }
> ```

---

#### 2. _Get User Detail By ID_

| Method | Path | Description | Authentication |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/v1/users/<int:id>` | Get user detail by ID | None |

##### Success Response 
>**Body**
>```json
>{
>    "data": {
>        "age": 27,
>        "created_at": "2026-08-01T20:11:02.118738+07:00",
>        "email": "budi@gmail.com",
>        "id": 1,
>        "is_active": false,
>        "provider": "password_hash",
>        "provider_key": "8c6976e5b5410415bde908bd4dee15dfb167a9c873fc4bb8a81f6f2ab448a918",
>        "role": [
>            "BUYER"
>        ],
>        "username": "budi"
>    },
>    "message": "User with id=1 is found",
>    "success": true
>}
>```
##### Error Response 
>**Body**
>```json
>{
>    "error": "Not Found",
>    "message": "User is not found",
>    "status_code": 404,
>    "success": false
>}
>```

---

#### 3. _Create New User_

| Method | Path | Description | Authentication |
| :--- | :--- | :--- | :--- |
| `POST` | `/api/v1/users` | Create new user | None |

##### Request 
> [!note]
> _This endpoint expects a multipart form._
>
> **Parameters**
> * `email` ( _string_ ) — __Required__
> * `age` ( _string_ ) — __Required__
> * `password` ( _string_ ) — __Required__
> 
>  **Fetch Example**
>  ```javascript
>  const formdata = new FormData();
>  formdata.append("email", "adriana@gmail.com");
>  formdata.append("age", "35");
>  formdata.append("password", "adriana948");
>  
>  const requestOptions = {
>    method: "GET",
>    body: formdata,
>    redirect: "follow"
>  };
>  
>  fetch("http://127.0.0.1:8000/api/v1/users", requestOptions)
>    .then((response) => response.text())
>    .then((result) => console.log(result))
>    .catch((error) => console.error(error));
>  ```

#### Success Response
>**Body**
>```json
>{
>    "data": {
>        "age": 35,
>        "created_at": "2026-08-12T16:33:27.012421+07:00",
>        "email": "adriana@gmail.com",
>        "id": 12,
>        "is_active": false,
>        "provider": "password_hash",
>        "provider_key": "f96354dd9b0cb206ba156f52be94e4cdfebad293e834fd8276643942d9e6b83f",
>        "role": [
>            "BUYER"
>        ],
>        "username": "adriana"
>    },
>    "message": " New user has been created.",
>    "success": true
>}
>```
#### Error Response
>**Body**
>
>_Age is not a number_
>```json
>{
>    "message": "'age' must be a valid number",
>    "success": false
>}
>```
>_Required parameters are not statisfied_
>```json
>{
>    "message": "'email','age',or 'password' is not provided",
>    "success": false
>}
>```
>_Wrong email format_
>```json
>{
>    "message": "Email format is wrong",
>    "success": false
>}
>```

<!-- | Method | Path | Description | Authentication |Authentication |
| :--- | :--- | :--- | :---: | :---: |
| <kbd>POST</kbd> | `/api/v1/auth/login` | Authenticate user & get token | None | <pre>code</pre> |
| <kbd>GET</kbd> | `/api/v1/users` | Get list of all users | None |
| <kbd>GET</kbd> | `/api/v1/users/<int:id>` | Get list of all users | None |
| <kbd>POST</kbd> | `/api/v1/users` | Register a new user | None | -->

### 📦 Product Module

| Method | Path | Description | Authentication |
| :--- | :--- | :--- | :---: |
| <kbd>POST</kbd> | `/api/v1/products` | Create a new product | `Bearer Token` |
| <kbd>GET</kbd> | `/api/v1/products` | List all products | None |
| <kbd>GET</kbd> | `/api/v1/products/<int:id>` | Get product details by ID | None |
| <kbd>PUT</kbd> | `/api/v1/products/<int:id>` | Update product details | `Bearer Token` |
| <kbd>DELETE</kbd> | `/api/v1/products/<int:id>` | Remove a product | `Bearer Token` |

### 📦 Category Module

| Method | Path | Description | Authentication |
| :--- | :--- | :--- | :---: |
| <kbd>POST</kbd> | `/api/v1/categories` | Create a new category | `Bearer Token` |
| <kbd>GET</kbd> | `/api/v1/categories` | List all category | None |
| <kbd>GET</kbd> | `/api/v1/categories/<int:id>` | Get a specific category along with its products| None |
| <kbd>PUT</kbd> | `/api/v1/categories/<int:id>` | Update category  | `Bearer Token` |
| <kbd>DELETE</kbd> | `/api/v1/categories/<int:id>` | Remove a category | `Bearer Token` |

### 📦 Order Module

| Method | Path | Description | Authentication |
| :--- | :--- | :--- | :---: |
| <kbd>POST</kbd> | `/api/v1/orders` | Place a new order linked to the logged-in user | `Bearer Token` |
| <kbd>GET</kbd> | `/api/v1/orders` | List all orders for the current user | `Bearer Token` |
| <kbd>GET</kbd> | `/api/v1/orders/<int:id>` | View a specific order with its order items and product details | `Bearer Token` |
| <kbd>PUT</kbd> | `/api/v1/orders/<int:id>` | Update category  | `Bearer Token` |
| <kbd>DELETE</kbd> | `/api/v1/orders/<int:id>` | Delete an order | `Bearer Token` |


> **Note:** All protected endpoints require a Bearer token in the `Authorization` header. Obtain a token via `POST /auth/login`.

## Contributing
Read [CONTRIBUTING.md](./CONTRIBUTING.md) for our pull request process, coding standards, and commit message format.
## License
[MIT](./LICENSE) © 2026 RevoShop Team

