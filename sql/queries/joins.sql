-- ============================================================
-- SQL Join Queries — Multi-table relationship queries
-- ============================================================

-- ──────────────────────────────────────────────────────────
-- 1. Complete order receipt (user + order + items + products)
-- ──────────────────────────────────────────────────────────
SELECT
    o.order_id,
    o.created_at AS order_date,
    o.status,
    u.full_name AS customer,
    u.email,
    a.street || ', ' || a.city AS shipping_address,
    p.name AS product_name,
    p.sku,
    oi.quantity,
    oi.unit_price,
    ROUND(oi.quantity * oi.unit_price * (1 - oi.discount_pct/100), 2) AS line_total,
    o.total_amount,
    o.payment_method
FROM orders o
JOIN users u ON u.user_id = o.user_id
LEFT JOIN addresses a ON a.address_id = o.address_id
JOIN order_items oi ON oi.order_id = o.order_id
JOIN products p ON p.product_id = oi.product_id
WHERE o.order_id = '00000000-0000-0000-0000-000000000004'
ORDER BY oi.item_id;

-- ──────────────────────────────────────────────────────────
-- 2. Products with their category path + avg rating
-- ──────────────────────────────────────────────────────────
WITH RECURSIVE category_tree AS (
    -- Base: top-level categories
    SELECT category_id, name, parent_id, name::TEXT AS full_path
    FROM categories
    WHERE parent_id IS NULL

    UNION ALL

    -- Recursive: append children
    SELECT c.category_id, c.name, c.parent_id,
           ct.full_path || ' > ' || c.name
    FROM categories c
    JOIN category_tree ct ON ct.category_id = c.parent_id
)
SELECT
    p.product_id,
    p.name AS product,
    ct.full_path AS category_path,
    p.price,
    p.stock,
    COALESCE(ROUND(AVG(r.rating), 2), 0) AS avg_rating,
    COUNT(r.review_id) AS reviews
FROM products p
JOIN category_tree ct ON ct.category_id = p.category_id
LEFT JOIN reviews r ON r.product_id = p.product_id
WHERE p.is_active = TRUE
GROUP BY p.product_id, ct.full_path
ORDER BY avg_rating DESC, reviews DESC;

-- ──────────────────────────────────────────────────────────
-- 3. Cross-sell: products frequently bought together
-- ──────────────────────────────────────────────────────────
SELECT
    p1.name AS product_a,
    p2.name AS product_b,
    COUNT(*) AS co_purchase_count
FROM order_items oi1
JOIN order_items oi2
    ON oi1.order_id = oi2.order_id
    AND oi1.product_id < oi2.product_id   -- avoid duplicates
JOIN products p1 ON p1.product_id = oi1.product_id
JOIN products p2 ON p2.product_id = oi2.product_id
GROUP BY p1.name, p2.name
ORDER BY co_purchase_count DESC
LIMIT 20;

-- ──────────────────────────────────────────────────────────
-- 4. Users who have never placed an order (LEFT JOIN anti-pattern)
-- ──────────────────────────────────────────────────────────
SELECT
    u.user_id,
    u.email,
    u.username,
    u.created_at AS registered_at
FROM users u
LEFT JOIN orders o ON o.user_id = u.user_id
WHERE o.order_id IS NULL
  AND u.is_active = TRUE
ORDER BY u.created_at DESC;
