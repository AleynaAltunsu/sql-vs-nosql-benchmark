-- ============================================================
-- SQL Aggregation Queries — E-Commerce PostgreSQL
-- ============================================================

-- ──────────────────────────────────────────────────────────
-- 1. Total revenue by category (last 30 days)
-- ──────────────────────────────────────────────────────────
SELECT
    c.name AS category,
    COUNT(DISTINCT o.order_id) AS total_orders,
    SUM(oi.quantity) AS units_sold,
    ROUND(SUM(oi.quantity * oi.unit_price), 2) AS gross_revenue,
    ROUND(AVG(oi.unit_price), 2) AS avg_unit_price
FROM order_items oi
JOIN orders o ON o.order_id = oi.order_id
JOIN products p ON p.product_id = oi.product_id
JOIN categories c ON c.category_id = p.category_id
WHERE o.status NOT IN ('cancelled', 'refunded')
  AND o.created_at >= NOW() - INTERVAL '30 days'
GROUP BY c.category_id, c.name
ORDER BY gross_revenue DESC;

-- ──────────────────────────────────────────────────────────
-- 2. Monthly revenue trend (last 12 months)
-- ──────────────────────────────────────────────────────────
SELECT
    DATE_TRUNC('month', o.created_at) AS month,
    COUNT(DISTINCT o.order_id) AS order_count,
    COUNT(DISTINCT o.user_id) AS unique_buyers,
    ROUND(SUM(o.total_amount), 2) AS revenue
FROM orders o
WHERE o.status NOT IN ('cancelled', 'refunded')
  AND o.created_at >= NOW() - INTERVAL '12 months'
GROUP BY 1
ORDER BY 1;

-- ──────────────────────────────────────────────────────────
-- 3. Top 10 best-selling products
-- ──────────────────────────────────────────────────────────
SELECT
    p.product_id,
    p.name,
    p.brand,
    SUM(oi.quantity) AS units_sold,
    ROUND(SUM(oi.quantity * oi.unit_price), 2) AS revenue
FROM order_items oi
JOIN products p ON p.product_id = oi.product_id
JOIN orders o ON o.order_id = oi.order_id
WHERE o.status NOT IN ('cancelled', 'refunded')
GROUP BY p.product_id, p.name, p.brand
ORDER BY units_sold DESC
LIMIT 10;

-- ──────────────────────────────────────────────────────────
-- 4. Customer lifetime value (CLV) per user
-- ──────────────────────────────────────────────────────────
SELECT
    u.user_id,
    u.username,
    u.email,
    COUNT(o.order_id) AS total_orders,
    ROUND(SUM(o.total_amount), 2) AS lifetime_value,
    ROUND(AVG(o.total_amount), 2) AS avg_order_value,
    MIN(o.created_at) AS first_order,
    MAX(o.created_at) AS last_order
FROM users u
JOIN orders o ON o.user_id = u.user_id
WHERE o.status NOT IN ('cancelled', 'refunded')
GROUP BY u.user_id, u.username, u.email
ORDER BY lifetime_value DESC
LIMIT 50;

-- ──────────────────────────────────────────────────────────
-- 5. Window function: rank products by revenue within category
-- ──────────────────────────────────────────────────────────
WITH product_revenue AS (
    SELECT
        p.product_id,
        p.name AS product_name,
        c.name AS category_name,
        SUM(oi.quantity * oi.unit_price) AS revenue
    FROM order_items oi
    JOIN products p ON p.product_id = oi.product_id
    JOIN categories c ON c.category_id = p.category_id
    JOIN orders o ON o.order_id = oi.order_id
    WHERE o.status NOT IN ('cancelled', 'refunded')
    GROUP BY p.product_id, p.name, c.name
)
SELECT
    category_name,
    product_name,
    ROUND(revenue, 2) AS revenue,
    RANK() OVER (PARTITION BY category_name ORDER BY revenue DESC) AS rank_in_category
FROM product_revenue
ORDER BY category_name, rank_in_category;

-- ──────────────────────────────────────────────────────────
-- 6. Repeat vs. one-time buyer ratio
-- ──────────────────────────────────────────────────────────
SELECT
    CASE WHEN order_count = 1 THEN 'One-time' ELSE 'Repeat' END AS buyer_type,
    COUNT(*) AS user_count,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 2) AS percentage
FROM (
    SELECT user_id, COUNT(order_id) AS order_count
    FROM orders
    WHERE status NOT IN ('cancelled', 'refunded')
    GROUP BY user_id
) sub
GROUP BY buyer_type;

-- ──────────────────────────────────────────────────────────
-- 7. Products with low stock but high demand (restock alert)
-- ──────────────────────────────────────────────────────────
SELECT
    p.product_id,
    p.name,
    p.stock AS current_stock,
    SUM(oi.quantity) AS sold_last_30d,
    ROUND(SUM(oi.quantity) / 30.0, 1) AS daily_velocity,
    ROUND(p.stock / NULLIF(SUM(oi.quantity) / 30.0, 0), 0) AS days_until_stockout
FROM products p
JOIN order_items oi ON oi.product_id = p.product_id
JOIN orders o ON o.order_id = oi.order_id
WHERE o.status NOT IN ('cancelled', 'refunded')
  AND o.created_at >= NOW() - INTERVAL '30 days'
  AND p.stock < 50
GROUP BY p.product_id, p.name, p.stock
ORDER BY days_until_stockout ASC NULLS LAST;
