-- ============================================================================
-- GarmentPulse — DuckDB Schema
-- Generated: 2026-11-20
--
-- This file defines the core tables and analytics views for the GarmentPulse
-- retail fashion analytics platform.
-- ============================================================================

-- ============================================================================
-- 1. TABLES
-- ============================================================================

-- ----------------------------------------------------------------------------
-- transactions: Every purchase event (one row per article bought).
-- ----------------------------------------------------------------------------
DROP TABLE IF EXISTS transactions;

CREATE TABLE transactions (
    t_dat            DATE,              -- Transaction date
    customer_id      VARCHAR,           -- FK → customers.customer_id
    article_id       VARCHAR,           -- FK → articles.article_id
    price            DOUBLE,            -- Normalised purchase price (0‑1 range)
    sales_channel_id INTEGER            -- Channel 1 or Channel 2 pending verified mapping
);

-- ----------------------------------------------------------------------------
-- articles: Product catalogue — one row per unique article (SKU).
-- ----------------------------------------------------------------------------
DROP TABLE IF EXISTS articles;

CREATE TABLE articles (
    article_id                   VARCHAR PRIMARY KEY,  -- Unique article identifier
    product_code                 VARCHAR,              -- Parent product code
    prod_name                    VARCHAR,              -- Product display name
    product_type_no              INTEGER,              -- Product type numeric code
    product_type_name            VARCHAR,              -- Product type label
    product_group_name           VARCHAR,              -- High-level product group
    graphical_appearance_no      INTEGER,              -- Visual appearance numeric code
    graphical_appearance_name    VARCHAR,              -- Visual appearance label
    colour_group_code            INTEGER,              -- Colour group numeric code
    colour_group_name            VARCHAR,              -- Colour group label
    perceived_colour_value_id    INTEGER,              -- Perceived colour value numeric id
    perceived_colour_value_name  VARCHAR,              -- Perceived colour value label
    perceived_colour_master_id   INTEGER,              -- Perceived master colour numeric id
    perceived_colour_master_name VARCHAR,              -- Perceived master colour label
    department_no                INTEGER,              -- Department numeric code
    department_name              VARCHAR,              -- Department label
    index_code                   VARCHAR,              -- Index short code
    index_name                   VARCHAR,              -- Index (e.g. Ladieswear) label
    index_group_no               INTEGER,              -- Index group numeric code
    index_group_name             VARCHAR,              -- Index group label
    section_no                   INTEGER,              -- Section numeric code
    section_name                 VARCHAR,              -- Section label
    garment_group_no             INTEGER,              -- Garment group numeric code
    garment_group_name           VARCHAR,              -- Garment group label
    detail_desc                  VARCHAR               -- Free-text product description
);

-- ----------------------------------------------------------------------------
-- customers: Customer profile data.
-- ----------------------------------------------------------------------------
DROP TABLE IF EXISTS customers;

CREATE TABLE customers (
    customer_id            VARCHAR PRIMARY KEY,  -- Unique customer identifier
    fn                     DOUBLE,               -- Fashion-news opt-in flag (1/0/NULL)
    active                 DOUBLE,               -- Active-status flag (1/0/NULL)
    club_member_status     VARCHAR,              -- Club membership tier
    fashion_news_frequency VARCHAR,              -- Fashion news cadence (Regularly / Monthly / NONE)
    age                    DOUBLE,               -- Customer age
    postal_code            VARCHAR               -- Hashed postal code
);

-- ============================================================================
-- 2. VIEWS — Common Analytics
-- ============================================================================

-- ----------------------------------------------------------------------------
-- v_transactions_enriched
--   Denormalised fact table: every transaction row enriched with the full
--   article catalogue fields and customer profile fields.
-- ----------------------------------------------------------------------------
DROP VIEW IF EXISTS v_transactions_enriched;

CREATE VIEW v_transactions_enriched AS
SELECT
    t.t_dat,
    t.customer_id,
    t.article_id,
    t.price,
    t.sales_channel_id,

    -- Article dimensions
    a.product_code,
    a.prod_name,
    a.product_type_name,
    a.product_type_no,
    a.product_group_name,
    a.graphical_appearance_name,
    a.graphical_appearance_no,
    a.colour_group_name,
    a.colour_group_code,
    a.perceived_colour_value_name,
    a.perceived_colour_value_id,
    a.perceived_colour_master_name,
    a.perceived_colour_master_id,
    a.department_name,
    a.department_no,
    a.index_name,
    a.index_code,
    a.index_group_name,
    a.index_group_no,
    a.section_name,
    a.section_no,
    a.garment_group_name,
    a.garment_group_no,
    a.detail_desc,

    -- Customer dimensions
    c.fn,
    c.active,
    c.club_member_status,
    c.fashion_news_frequency,
    c.age,
    c.postal_code
FROM transactions AS t
LEFT JOIN articles   AS a ON t.article_id  = a.article_id
LEFT JOIN customers  AS c ON t.customer_id = c.customer_id;

-- ----------------------------------------------------------------------------
-- v_monthly_summary
--   Monthly aggregation by department: revenue, units sold, and unique
--   customer count.  Uses DuckDB's DATE_TRUNC for calendar-month bucketing.
-- ----------------------------------------------------------------------------
DROP VIEW IF EXISTS v_monthly_summary;

CREATE VIEW v_monthly_summary AS
SELECT
    DATE_TRUNC('month', t.t_dat)  AS month,
    a.department_name,
    COUNT(*)                      AS total_items_sold,
    SUM(t.price)                  AS price_contribution,
    COUNT(DISTINCT t.customer_id) AS unique_customers,
    AVG(t.price)                  AS avg_price
FROM transactions AS t
LEFT JOIN articles AS a ON t.article_id = a.article_id
GROUP BY
    DATE_TRUNC('month', t.t_dat),
    a.department_name
ORDER BY month, a.department_name;

-- ----------------------------------------------------------------------------
-- v_weekly_summary
--   Weekly aggregation by department: revenue, units sold, and unique
--   customer count.  Uses DuckDB's DATE_TRUNC for ISO-week bucketing.
-- ----------------------------------------------------------------------------
DROP VIEW IF EXISTS v_weekly_summary;

CREATE VIEW v_weekly_summary AS
SELECT
    DATE_TRUNC('week', t.t_dat)   AS week,
    a.department_name,
    COUNT(*)                      AS total_items_sold,
    SUM(t.price)                  AS price_contribution,
    COUNT(DISTINCT t.customer_id) AS unique_customers,
    AVG(t.price)                  AS avg_price
FROM transactions AS t
LEFT JOIN articles AS a ON t.article_id = a.article_id
GROUP BY
    DATE_TRUNC('week', t.t_dat),
    a.department_name
ORDER BY week, a.department_name;

-- ============================================================================
-- End of GarmentPulse schema
-- ============================================================================
