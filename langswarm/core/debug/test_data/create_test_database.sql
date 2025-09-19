-- SQL Database Debug Test Schema
-- This file creates sample tables and data for testing the SQL Database MCP tool

-- Create users table
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    active INTEGER DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    last_login DATETIME,
    department TEXT,
    salary DECIMAL(10,2)
);

-- Create orders table
CREATE TABLE IF NOT EXISTS orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    product_name TEXT NOT NULL,
    quantity INTEGER DEFAULT 1,
    price DECIMAL(10,2) NOT NULL,
    order_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    status TEXT DEFAULT 'pending',
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- Create products table
CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    category TEXT,
    price DECIMAL(10,2) NOT NULL,
    stock_quantity INTEGER DEFAULT 0,
    description TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Insert sample users
INSERT OR REPLACE INTO users (id, name, email, active, department, salary, last_login) VALUES
(1, 'Alice Johnson', 'alice@example.com', 1, 'Engineering', 75000.00, '2024-01-15 09:30:00'),
(2, 'Bob Smith', 'bob@example.com', 1, 'Sales', 60000.00, '2024-01-14 14:20:00'),
(3, 'Carol Brown', 'carol@example.com', 1, 'Marketing', 65000.00, '2024-01-13 11:45:00'),
(4, 'David Wilson', 'david@example.com', 0, 'Engineering', 80000.00, '2023-12-20 16:10:00'),
(5, 'Eve Davis', 'eve@example.com', 1, 'HR', 55000.00, '2024-01-12 08:15:00'),
(6, 'Frank Miller', 'frank@example.com', 1, 'Sales', 62000.00, '2024-01-11 13:25:00'),
(7, 'Grace Lee', 'grace@example.com', 1, 'Engineering', 78000.00, '2024-01-10 10:40:00'),
(8, 'Henry Taylor', 'henry@example.com', 1, 'Marketing', 58000.00, '2024-01-16 15:55:00');

-- Insert sample products
INSERT OR REPLACE INTO products (id, name, category, price, stock_quantity, description) VALUES
(1, 'Laptop Pro', 'Electronics', 1299.99, 25, 'High-performance laptop for professionals'),
(2, 'Wireless Mouse', 'Electronics', 29.99, 100, 'Ergonomic wireless mouse'),
(3, 'Office Chair', 'Furniture', 199.99, 15, 'Comfortable ergonomic office chair'),
(4, 'Standing Desk', 'Furniture', 299.99, 8, 'Adjustable height standing desk'),
(5, 'Monitor 27"', 'Electronics', 249.99, 20, '27-inch 4K monitor'),
(6, 'Keyboard Mechanical', 'Electronics', 89.99, 50, 'Mechanical keyboard with RGB lighting'),
(7, 'Webcam HD', 'Electronics', 79.99, 30, '1080p HD webcam for video calls'),
(8, 'Desk Lamp', 'Office', 39.99, 40, 'LED desk lamp with adjustable brightness');

-- Insert sample orders
INSERT OR REPLACE INTO orders (id, user_id, product_name, quantity, price, status, order_date) VALUES
(1, 1, 'Laptop Pro', 1, 1299.99, 'completed', '2024-01-10 14:30:00'),
(2, 2, 'Wireless Mouse', 2, 29.99, 'completed', '2024-01-11 09:15:00'),
(3, 3, 'Office Chair', 1, 199.99, 'shipped', '2024-01-12 16:20:00'),
(4, 1, 'Monitor 27"', 1, 249.99, 'completed', '2024-01-13 11:45:00'),
(5, 4, 'Standing Desk', 1, 299.99, 'pending', '2024-01-14 13:10:00'),
(6, 5, 'Keyboard Mechanical', 1, 89.99, 'completed', '2024-01-15 10:25:00'),
(7, 2, 'Webcam HD', 1, 79.99, 'shipped', '2024-01-16 15:40:00'),
(8, 6, 'Desk Lamp', 3, 39.99, 'completed', '2024-01-17 12:55:00');

-- Create some useful views for testing
CREATE VIEW IF NOT EXISTS active_users AS
SELECT id, name, email, department, salary, last_login
FROM users 
WHERE active = 1;

CREATE VIEW IF NOT EXISTS recent_orders AS
SELECT o.id, u.name as customer_name, o.product_name, o.quantity, o.price, o.status, o.order_date
FROM orders o
JOIN users u ON o.user_id = u.id
WHERE o.order_date >= date('now', '-30 days')
ORDER BY o.order_date DESC;

CREATE VIEW IF NOT EXISTS order_summary AS
SELECT 
    u.department,
    COUNT(o.id) as total_orders,
    SUM(o.price * o.quantity) as total_revenue,
    AVG(o.price * o.quantity) as avg_order_value
FROM users u
LEFT JOIN orders o ON u.id = o.user_id
GROUP BY u.department
ORDER BY total_revenue DESC;
