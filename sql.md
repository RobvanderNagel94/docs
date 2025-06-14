---
layout: default
title: SQL
---

This document provides examples of common SQL statements and queries.

- [Creating Tables](#creating-tables)
- [Inserting Data](#inserting-data)
- [Selecting Data](#selecting-data)
- [Updating Data](#updating-data)
- [Deleting Data](#deleting-data)
- [Joining Tables](#joining-tables)

---

## Creating Tables

```sql
CREATE TABLE users (
    id INT PRIMARY KEY,
    name VARCHAR(100),
    email VARCHAR(100) UNIQUE
);

CREATE TABLE orders (
    id INT PRIMARY KEY,
    user_id INT,
    amount DECIMAL(10, 2),
    order_date DATE,
    FOREIGN KEY (user_id) REFERENCES users(id)
);
```

## Inserting Data

```sql
INSERT INTO users (id, name, email)
VALUES 
    (1, 'Alice', 'alice@example.com'),
    (2, 'Bob', 'bob@example.com');

INSERT INTO orders (id, user_id, amount, order_date)
VALUES
    (1, 1, 99.99, '2025-06-01'),
    (2, 1, 25.00, '2025-06-05'),
    (3, 2, 50.50, '2025-06-07');
```

## Selecting Data

```sql
-- Select all columns for all users
SELECT * FROM users;
-- Select specific columns for user with id=1
SELECT name, email FROM users WHERE id = 1;
-- Select orders placed after a specific date
SELECT * FROM orders WHERE order_date > '2025-06-03';
```

## Updating Data

```sql
UPDATE users
SET email = 'alice@newdomain.com'
WHERE id = 1;
```

## Deleting Data

```sql
-- Delete user with id=2
DELETE FROM users WHERE id = 2;
-- Delete all orders below 30
DELETE FROM orders WHERE amount < 30;
```

## Joining Tables

```sql
-- Inner join: users who have placed orders
SELECT users.name, orders.amount, orders.order_date
FROM users
JOIN orders ON users.id = orders.user_id;

-- Left join: all users, including those without orders
SELECT users.name, orders.amount
FROM users
LEFT JOIN orders ON users.id = orders.user_id;

-- Right join: all orders, including those without matching users (if allowed)
SELECT users.name, orders.amount
FROM users
RIGHT JOIN orders ON users.id = orders.user_id;
```

## Distinct
```sql
-- Get distinct user names (remove duplicates)
SELECT DISTINCT name FROM users;
-- Get distinct order amounts
SELECT DISTINCT amount FROM orders;
```

## Advanced Joins & Queries
```sql
-- Count total orders per user
SELECT users.name, COUNT(orders.id) AS total_orders
FROM users
LEFT JOIN orders ON users.id = orders.user_id
GROUP BY users.name;

-- Get total amount spent per user for orders after a date
SELECT users.name, SUM(orders.amount) AS total_spent
FROM users
JOIN orders ON users.id = orders.user_id
WHERE orders.order_date > '2025-06-01'
GROUP BY users.name;

-- Get users with no orders (using NOT EXISTS)
SELECT name FROM users u
WHERE NOT EXISTS (
    SELECT 1 FROM orders o WHERE o.user_id = u.id
);
```

### psql
PostgreSQL CLI

```bash
-- Connect to a database with user and password prompt:
psql -h <host> -p <port> -U <username> -d <database>
# psql -h localhost -p 5432 -U myuser -d mydb #as example
\c <database>             # Connect to a database
\dt                       # List tables in current database
\d <table_name>           # Describe table schema
\l                        # List all databases
\du                       # List all roles/users
\q                        # Quit psql shell
```

### Python
pip install psycopg2-binary

```python
import psycopg2

# Connection parameters
conn = psycopg2.connect(
    host="localhost",
    database="mydb",
    user="myuser",
    password="mypassword"
)

cur = conn.cursor()

# Create a table
cur.execute("""
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100),
    email VARCHAR(100) UNIQUE
);
""")
conn.commit()

# Insert data
cur.execute("INSERT INTO users (name, email) VALUES (%s, %s)", ("Alice", "alice@example.com"))
conn.commit()

# Select data
cur.execute("SELECT id, name, email FROM users")
rows = cur.fetchall()
for row in rows:
    print(row)

# Close connections
cur.close()
conn.close()
```