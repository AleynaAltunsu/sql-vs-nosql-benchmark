-- ============================================================
-- seed.sql — Small fixed dataset for smoke-testing the schema
-- For large datasets, use: python scripts/generate_data.py
-- ============================================================

-- Categories
INSERT INTO categories (name, slug, parent_id) VALUES
  ('Electronics',      'electronics',      NULL),
  ('Headphones',       'headphones',       1),
  ('Smartphones',      'smartphones',      1),
  ('Clothing',         'clothing',         NULL),
  ('Books',            'books',            NULL),
  ('Sports',           'sports',           NULL)
ON CONFLICT (slug) DO NOTHING;

-- Users
INSERT INTO users (user_id, email, username, full_name) VALUES
  ('00000000-0000-0000-0001-000000000001', 'alice@example.com', 'alice', 'Alice Smith'),
  ('00000000-0000-0000-0001-000000000002', 'bob@example.com',   'bob',   'Bob Jones')
ON CONFLICT DO NOTHING;

-- Addresses
INSERT INTO addresses (address_id, user_id, label, street, city, country, is_default) VALUES
  ('00000000-0000-0000-0002-000000000001', '00000000-0000-0000-0001-000000000001', 'home', '123 Main St', 'Istanbul', 'Turkey', TRUE),
  ('00000000-0000-0000-0002-000000000002', '00000000-0000-0000-0001-000000000002', 'home', '456 Oak Ave', 'Ankara',   'Turkey', TRUE)
ON CONFLICT DO NOTHING;

-- Products
INSERT INTO products (product_id, category_id, name, description, sku, price, stock, brand) VALUES
  ('00000000-0000-0000-0003-000000000001', 2, 'ProSound X1 Headphones', 'Over-ear wireless headphones', 'PSX1-BLK', 199.99, 50, 'ProSound'),
  ('00000000-0000-0000-0003-000000000002', 3, 'ZenPhone 15 Pro',        '6.7" AMOLED flagship',         'ZP15-256',  999.99, 30, 'Zen'),
  ('00000000-0000-0000-0003-000000000003', 5, 'Clean Code',             'R. Martin programming classic', 'CC-BOOK',    35.00, 200, 'Prentice Hall')
ON CONFLICT DO NOTHING;

-- Orders
INSERT INTO orders (order_id, user_id, address_id, status, total_amount, payment_method) VALUES
  ('00000000-0000-0000-0004-000000000001', '00000000-0000-0000-0001-000000000001', '00000000-0000-0000-0002-000000000001', 'delivered', 234.99, 'credit_card'),
  ('00000000-0000-0000-0004-000000000002', '00000000-0000-0000-0001-000000000002', '00000000-0000-0000-0002-000000000002', 'pending',   999.99, 'paypal')
ON CONFLICT DO NOTHING;

-- Order items
INSERT INTO order_items (order_id, product_id, quantity, unit_price) VALUES
  ('00000000-0000-0000-0004-000000000001', '00000000-0000-0000-0003-000000000001', 1, 199.99),
  ('00000000-0000-0000-0004-000000000001', '00000000-0000-0000-0003-000000000003', 1,  35.00),
  ('00000000-0000-0000-0004-000000000002', '00000000-0000-0000-0003-000000000002', 1, 999.99)
ON CONFLICT DO NOTHING;
