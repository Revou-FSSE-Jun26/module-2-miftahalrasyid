DROP DATABASE IF EXISTS revoshop_db;
CREATE DATABASE revoshop_db;
\c revoshop_db;

CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(150) UNIQUE NOT NULL,
    age INTEGER NOT NULL,
    is_active BOOLEAN DEFAULT FALSE,
    provider VARCHAR(50) DEFAULT 'password' NOT NULL,
    provider_key VARCHAR(255) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE products (
    id SERIAL PRIMARY KEY,
    name VARCHAR(150) NOT NULL,
    quantity INTEGER CHECK (quantity >= 0) DEFAULT 0,
    brand VARCHAR(150) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE categories (
    id SERIAL PRIMARY KEY,
    name VARCHAR(150) UNIQUE CHECK (lower(name) = name), 
    created_at TIMESTAMPTZ DEFAULT now()
);


CREATE TABLE category_items (
    category_id INTEGER REFERENCES categories(id) ON DELETE CASCADE,
    product_id INTEGER REFERENCES products(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ DEFAULT now(),
    -- Membuat kombinasi kedua ID ini menjadi unik agar tidak ada duplikasi produk di kategori yang sama
    PRIMARY KEY (category_id, product_id) 
);

CREATE TABLE orders (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(150) UNIQUE CHECK (lower(name) = name), 
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE order_items (
    id SERIAL PRIMARY KEY,
    orders_id INTEGER REFERENCES orders(id) ON DELETE CASCADE, -- Cukup ini untuk tahu siapa pembelinya
    product_id INTEGER REFERENCES products(id) ON DELETE CASCADE,
    quantity INTEGER NOT NULL DEFAULT 1,
    created_at TIMESTAMPTZ DEFAULT now()
);