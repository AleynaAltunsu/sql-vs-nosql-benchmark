-- ============================================================
-- E-Commerce SQL Schema (PostgreSQL 15)
-- Normalized to Third Normal Form (3NF)
-- ============================================================

-- Enable UUID generation
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
-- Enable full-text search
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- ============================================================
-- USERS
-- ============================================================
CREATE TABLE users (
    user_id     UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email       VARCHAR(255) UNIQUE NOT NULL,
    username    VARCHAR(100) NOT NULL,
    full_name   VARCHAR(200),
    phone       VARCHAR(20),
    created_at  TIMESTAMPTZ DEFAULT NOW(),
    updated_at  TIMESTAMPTZ DEFAULT NOW(),
    is_active   BOOLEAN DEFAULT TRUE
);

CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_created_at ON users(created_at);

-- ============================================================
-- ADDRESSES (separate table — a user can have many)
-- ============================================================
CREATE TABLE addresses (
    address_id  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id     UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    label       VARCHAR(50) DEFAULT 'home',  -- 'home', 'work', etc.
    street      VARCHAR(300) NOT NULL,
    city        VARCHAR(100) NOT NULL,
    country     VARCHAR(100) NOT NULL,
    postal_code VARCHAR(20),
    is_default  BOOLEAN DEFAULT FALSE
);

CREATE INDEX idx_addresses_user_id ON addresses(user_id);

-- ============================================================
-- CATEGORIES (self-referencing tree for nested categories)
-- ============================================================
CREATE TABLE categories (
    category_id   SERIAL PRIMARY KEY,
    name          VARCHAR(150) UNIQUE NOT NULL,
    parent_id     INT REFERENCES categories(category_id) ON DELETE SET NULL,
    slug          VARCHAR(150) UNIQUE NOT NULL,
    description   TEXT
);

-- ============================================================
-- PRODUCTS
-- ============================================================
CREATE TABLE products (
    product_id    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    category_id   INT NOT NULL REFERENCES categories(category_id),
    name          VARCHAR(300) NOT NULL,
    description   TEXT,
    sku           VARCHAR(100) UNIQUE NOT NULL,
    price         NUMERIC(12, 2) NOT NULL CHECK (price >= 0),
    stock         INT NOT NULL DEFAULT 0 CHECK (stock >= 0),
    brand         VARCHAR(150),
    is_active     BOOLEAN DEFAULT TRUE,
    created_at    TIMESTAMPTZ DEFAULT NOW(),
    updated_at    TIMESTAMPTZ DEFAULT NOW(),
    -- Full-text search vector (auto-maintained via trigger)
    fts_vector    TSVECTOR GENERATED ALWAYS AS (
                      to_tsvector('english', coalesce(name, '') || ' ' || coalesce(description, '') || ' ' || coalesce(brand, ''))
                  ) STORED
);

CREATE INDEX idx_products_category ON products(category_id);
CREATE INDEX idx_products_sku ON products(sku);
CREATE INDEX idx_products_price ON products(price);
CREATE INDEX idx_products_fts ON products USING GIN(fts_vector);
CREATE INDEX idx_products_name_trgm ON products USING GIN(name gin_trgm_ops);

-- ============================================================
-- PRODUCT ATTRIBUTES (EAV for flexible product specs)
-- ============================================================
CREATE TABLE product_attributes (
    attr_id     SERIAL PRIMARY KEY,
    product_id  UUID NOT NULL REFERENCES products(product_id) ON DELETE CASCADE,
    attr_key    VARCHAR(100) NOT NULL,
    attr_value  VARCHAR(500),
    UNIQUE(product_id, attr_key)
);

CREATE INDEX idx_product_attributes_product ON product_attributes(product_id);

-- ============================================================
-- ORDERS
-- ============================================================
CREATE TYPE order_status AS ENUM (
    'pending', 'confirmed', 'processing', 'shipped', 'delivered', 'cancelled', 'refunded'
);

CREATE TABLE orders (
    order_id        UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID NOT NULL REFERENCES users(user_id),
    address_id      UUID REFERENCES addresses(address_id),
    status          order_status NOT NULL DEFAULT 'pending',
    total_amount    NUMERIC(14, 2) NOT NULL CHECK (total_amount >= 0),
    discount_amount NUMERIC(14, 2) DEFAULT 0,
    shipping_fee    NUMERIC(10, 2) DEFAULT 0,
    payment_method  VARCHAR(50),
    notes           TEXT,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_orders_user_id ON orders(user_id);
CREATE INDEX idx_orders_status ON orders(status);
CREATE INDEX idx_orders_created_at ON orders(created_at);

-- ============================================================
-- ORDER ITEMS (junction table)
-- ============================================================
CREATE TABLE order_items (
    item_id         SERIAL PRIMARY KEY,
    order_id        UUID NOT NULL REFERENCES orders(order_id) ON DELETE CASCADE,
    product_id      UUID NOT NULL REFERENCES products(product_id),
    quantity        INT NOT NULL CHECK (quantity > 0),
    unit_price      NUMERIC(12, 2) NOT NULL,  -- price at time of purchase
    discount_pct    NUMERIC(5, 2) DEFAULT 0
);

CREATE INDEX idx_order_items_order ON order_items(order_id);
CREATE INDEX idx_order_items_product ON order_items(product_id);

-- ============================================================
-- REVIEWS
-- ============================================================
CREATE TABLE reviews (
    review_id   UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    product_id  UUID NOT NULL REFERENCES products(product_id) ON DELETE CASCADE,
    user_id     UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    rating      SMALLINT NOT NULL CHECK (rating BETWEEN 1 AND 5),
    title       VARCHAR(200),
    body        TEXT,
    created_at  TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(product_id, user_id)  -- one review per product per user
);

CREATE INDEX idx_reviews_product ON reviews(product_id);
CREATE INDEX idx_reviews_user ON reviews(user_id);

-- ============================================================
-- HELPER: auto-update updated_at on row changes
-- ============================================================
CREATE OR REPLACE FUNCTION set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TRIGGER trg_products_updated_at
    BEFORE UPDATE ON products
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TRIGGER trg_orders_updated_at
    BEFORE UPDATE ON orders
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();
