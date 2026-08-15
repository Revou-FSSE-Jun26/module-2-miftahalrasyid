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

```mermaid
erDiagram
    categories {
        int id PK
        string name
        datetime created_at
    }

    category_items {
        int category_id FK
        int product_id FK
        datetime created_at
    }

    products {
        int id PK
        string name
        int quantity
        string brand
        datetime created_at
        string description
        int price
        int user_id FK
    }

    order_items {
        int order_id FK
        int product_id FK
        datetime created_at
    }

    orders {
        int id PK
        int user_id FK
        string name
        string status
        datetime created_at
        int total
    }

    users {
        int id PK
        string email
        int age
        boolean is_active
        string provider
        string provider_key
        datetime created_at
        string username
        string role
        datetime deleted_at
    }

    alembic_version {
        string version_num PK
    }

    categories ||--o{ category_items : "has"
    products ||--o{ category_items : "belongs to"
    products ||--o{ order_items : "included in"
    orders ||--o{ order_items : "contains"
    users ||--o{ products : "creates"
    users ||--o{ orders : "places"
```

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
pip install -r requirements.txt
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
SQLALCHEMY_DATABASE_URI=postgresql://postgres:root@localhost:5432/revoshop_db
SECRET_KEY=root_secret_key_anda
FLASK_APP=run.py
FLASK_DEBUG=1
```

### 4. Database Migration, & Seeding
Jalankan migrasi, *seeding*, dan server lokal:
```bash
flask db upgrade
python app/seeds/initial_seed.py
```

## Usage
Start the development server:
```bash
flask run --port=8000
```
The API will be available at `http://localhost:8000`.

Example request — Show welcome to Rovodev api:
```bash
curl -X POST http://localhost:8000/api \
  -H "Authorization: Bearer <your-token>" \
  -H "Content-Type: application/json" \
  -d '{"title": "Write unit tests", "priority": "high"}'
```

Akses dokumentasi Swagger UI di **[http://localhost:8000/swagger-ui](http://localhost:8000/swagger-ui)**.

## Seeding process

### Adding initial admin user

## Step-by-Step Guide: Implementing HTML Request Features in Isolation 
>Creating new feature (endpoint: GET,POST) steps using (Flask-Smorest x marsmallow x flask-sqlalchemy x marsmallow-sqlalchemy) route stack


```mermaid
flowchart TD
    %% Struktur luar diatur TD (Top-Down) agar kelompok Flask berada di bawah
    %% classDef step fill:#2d3748,stroke:#4a5568,stroke-width:2px,color:#fff;

    subgraph Isolation_Layer ["Isolation Layer"]
        direction LR
        A["<b>1. models.py</b><br>Create SQLAlchemy Models"]:::step 
        --> B["<b>2. schemas.py</b><br>Map Models to Marshmallow"]:::step
        --> C["<b>3. services.py</b><br>Write Pure Business Logic"]:::step
    end

    subgraph Flask_Registration ["Flask Registration"]
        direction LR
        D["<b>4. routes.py</b><br>Connect HTTP Routes to Services"]:::step 
        --> E["<b>5. __init__.py (App Factory)</b><br>Register Blueprints to Core API"]:::step
    end

    %% KUNCI: Hubungkan Subgraph langsung ke Subgraph agar panahnya vertikal ke bawah
    Isolation_Layer -->|Establish Connection to Flask| Flask_Registration

    %% Subgraph styling
    %% style Isolation_Layer fill:#202632,stroke:#4a5568,stroke-width:1px
    %% style Flask_Registration fill:#1a202c,stroke:#4a5568,stroke-width:1px

```

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
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── category_schema.py
│   │   ├── order_schema.py
│   │   ├── product_schema.py
│   │   └── user_schema.py
│   ├── seeds/
│   │   └── initial_seed.py
│   └── services/
│       ├── __init__.py
│       └── user_service.py
├── docs/
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
│       ├── e5dadb8947a1_convert_order_items_to_pure_many_to_.py
│       └── fb1b2de14c14_add_deleted_at_on_user.py
├── requirements.txt
└── run.py
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

