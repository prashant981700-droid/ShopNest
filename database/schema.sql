-- ShopNest DBMS schema
CREATE TABLE users(id INTEGER PRIMARY KEY AUTOINCREMENT,name TEXT NOT NULL,mobile TEXT UNIQUE NOT NULL);
CREATE TABLE products(id INTEGER PRIMARY KEY AUTOINCREMENT,name TEXT,category TEXT,price REAL,old_price REAL,rating REAL,image TEXT,description TEXT,stock INTEGER);
CREATE TABLE orders(id INTEGER PRIMARY KEY AUTOINCREMENT,user_id INTEGER,total REAL,status TEXT,customer_name TEXT,phone TEXT,address TEXT,city TEXT,pincode TEXT,payment_method TEXT,created_at TIMESTAMP);
CREATE TABLE order_items(id INTEGER PRIMARY KEY AUTOINCREMENT,order_id INTEGER,product_id INTEGER,quantity INTEGER,price REAL);
