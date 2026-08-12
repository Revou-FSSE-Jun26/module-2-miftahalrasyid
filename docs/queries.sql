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
    description VARCHAR(1000),
    price numeric(10,2) DEFAULT 0 NOT NULL,  
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
    total integer DEFAULT 1 NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE order_items (
    id SERIAL PRIMARY KEY,
    orders_id INTEGER REFERENCES orders(id) ON DELETE CASCADE, -- Cukup ini untuk tahu siapa pembelinya
    product_id INTEGER REFERENCES products(id) ON DELETE CASCADE,
    quantity INTEGER NOT NULL DEFAULT 1,
    created_at TIMESTAMPTZ DEFAULT now()
);



INSERT INTO users (
    email,age,provider_key
) values (
    'budi@gmail.com', 27,
    -- admin
    '8c6976e5b5410415bde908bd4dee15dfb167a9c873fc4bb8a81f6f2ab448a918'
),(
    'arini@gmail.com', 27,
    -- root
    '4813494d137e1631bba301d5acab6e7bb7aa74ce1185d456565ef51d737677b2'
),(
    'husni@gmail.com', 27,
    -- 123456
    'e10adc3949ba59abbe56e057f20f883e28b4b4dbd33b58c4886d22698e7341ea'
);

INSERT INTO products (
    name,quantity,brand,description
) values (
    'laptop asus', 50,'asus',
    'laptop dengan batre cepat rusak'
),(
    'laptop lenovo', 150,'lenovo',
    'terkenal dengan laptop gaming murahnya'
),(
    'laptop surface', 30,'microsoft',
    'laptop dari sang pembuat os dengan harga lebih mahal dari yang lain'
),(
    'laptop macbook', 50,'apple',
    'laptop dengan prioritas keamanan yang tinggi'
);

INSERT INTO categories (
    name
) values (
    'livestyle'
),(
    'gaming'
),(
    'apple'
),(
    'komputer'
);

INSERT INTO category_items (
    category_id,product_id
) values (
    1,1
),(
    2,2
),(
    3,4
),(
    4,4
);


INSERT INTO orders (
    user_id,name
) values (
    1,
    'inv-4229435'
),(
    2,
    'inv-3245435'
),(
    3,
    'inv-4374343'
),(
    2,
    'inv-2938673'
);

INSERT INTO order_items (
    orders_id, product_id, quantity 
) VALUES (
    1, 4, 35
),(
    2, 2, 28
),(
    3, 2, 100
),(
    1, 3, 1
);

SELECT * FROM products
WHERE quantity > 30
ORDER BY quantity DESC
LIMIT 2;