-- ============================================================
-- SQL CRUD Queries — E-Commerce PostgreSQL
-- ============================================================

-- ──────────────────────────────────────────────────────────
-- CREATE
-- ──────────────────────────────────────────────────────────

-- Insert a new user
INSERT INTO users (email, username, full_name, phone)
VALUES ('ayse.kaya@example.com', 'aysekaya', 'Ayşe Kaya', '+905551234567')
RETURNING user_id, email, created_at;

-- Insert a product
INSERT INTO products (category_id, name, description, sku, price, stock, brand)
VALUES (
    1,
    'Wireless Noise-Cancelling Headphones',
    'Over-ear Bluetooth headphones with 40hr battery and active noise cancellation.',
    'WH-1000XM5-BLK',
    349.99,
    120,
    'SoundMax'
)
RETURNING product_id, sku;

-- Place a new order
INSERT INTO orders (user_id, address_id, status, total_amount, payment_method)
VALUES (
    '00000000-0000-0000-0000-000000000001',  -- replace with real UUID
    '00000000-0000-0000-0000-000000000002',
    'pending',
    699.98,
    'credit_card'
)
RETURNING order_id, created_at;

-- ──────────────────────────────────────────────────────────
-- READ
-- ──────────────────────────────────────────────────────────

-- Get user by email
SELECT user_id, username, full_name, email, created_at
FROM users
WHERE email = 'ayse.kaya@example.com';

-- Get all orders for a user with status
SELECT
    o.order_id,
    o.status,
    o.total_amount,
    o.created_at,
    COUNT(oi.item_id) AS item_count
FROM orders o
JOIN order_items oi ON oi.order_id = o.order_id
WHERE o.user_id = '00000000-0000-0000-0000-000000000001'
GROUP BY o.order_id
ORDER BY o.created_at DESC;

-- Get product with category and average rating
SELECT
    p.product_id,
    p.name,
    p.price,
    p.stock,
    c.name AS category,
    ROUND(AVG(r.rating), 2) AS avg_rating,
    COUNT(r.review_id) AS review_count
FROM products p
JOIN categories c ON c.category_id = p.category_id
LEFT JOIN reviews r ON r.product_id = p.product_id
WHERE p.product_id = '00000000-0000-0000-0000-000000000003'
GROUP BY p.product_id, c.name;

-- Full-text search on product name/description
SELECT product_id, name, price, brand,
       ts_rank(fts_vector, query) AS rank
FROM products,
     to_tsquery('english', 'headphones & bluetooth') query
WHERE fts_vector @@ query
ORDER BY rank DESC
LIMIT 20;

-- ──────────────────────────────────────────────────────────
-- UPDATE
-- ──────────────────────────────────────────────────────────

-- Update order status
UPDATE orders
SET status = 'shipped'
WHERE order_id = '00000000-0000-0000-0000-000000000004'
  AND status = 'processing'   -- guard against double-update
RETURNING order_id, status, updated_at;

-- Decrease stock after purchase (atomic)
UPDATE products
SET stock = stock - 2
WHERE product_id = '00000000-0000-0000-0000-000000000003'
  AND stock >= 2          -- prevent negative stock
RETURNING product_id, stock;

-- ──────────────────────────────────────────────────────────
-- DELETE
-- ──────────────────────────────────────────────────────────

-- Soft-delete a user (preserve data integrity)
UPDATE users
SET is_active = FALSE, updated_at = NOW()
WHERE user_id = '00000000-0000-0000-0000-000000000001';

-- Hard-delete cancelled orders older than 1 year
DELETE FROM orders
WHERE status = 'cancelled'
  AND created_at < NOW() - INTERVAL '1 year';
