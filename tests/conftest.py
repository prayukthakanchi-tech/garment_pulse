"""
GarmentPulse — Pytest Fixtures & In-Memory Test Database
Creates small, self-contained, independent test datasets for unit and integration testing.
"""

import duckdb
import pytest
from pathlib import Path


@pytest.fixture
def test_db():
    """Provides an isolated in-memory DuckDB database loaded with realistic mock fashion data."""
    conn = duckdb.connect(":memory:")

    # 1. Create Tables
    conn.execute("""
    CREATE TABLE articles (
        article_id                   VARCHAR PRIMARY KEY,
        product_code                 VARCHAR,
        prod_name                    VARCHAR,
        product_type_no              INTEGER,
        product_type_name            VARCHAR,
        product_group_name           VARCHAR,
        graphical_appearance_no      INTEGER,
        graphical_appearance_name    VARCHAR,
        colour_group_code            INTEGER,
        colour_group_name            VARCHAR,
        perceived_colour_value_id    INTEGER,
        perceived_colour_value_name  VARCHAR,
        perceived_colour_master_id   INTEGER,
        perceived_colour_master_name VARCHAR,
        department_no                INTEGER,
        department_name              VARCHAR,
        index_code                   VARCHAR,
        index_name                   VARCHAR,
        index_group_no               INTEGER,
        index_group_name             VARCHAR,
        section_no                   INTEGER,
        section_name                 VARCHAR,
        garment_group_no             INTEGER,
        garment_group_name           VARCHAR,
        detail_desc                  VARCHAR
    );

    CREATE TABLE customers (
        customer_id            VARCHAR PRIMARY KEY,
        fn                     DOUBLE,
        active                 DOUBLE,
        club_member_status     VARCHAR,
        fashion_news_frequency VARCHAR,
        age                    DOUBLE,
        postal_code            VARCHAR
    );

    CREATE TABLE transactions (
        t_dat            DATE,
        customer_id      VARCHAR,
        article_id       VARCHAR,
        price            DOUBLE,
        sales_channel_id INTEGER
    );
    """)

    # 2. Insert Mock Articles (5 distinct articles across departments and colours)
    conn.execute("""
    INSERT INTO articles VALUES
    ('0108775015', '0108775', 'Strap Top', 253, 'Vest top', 'Garment Upper body', 1010016, 'Solid', 9, 'Black', 4, 'Dark', 5, 'Black', 1676, 'Jersey Basic', 'A', 'Ladieswear', 1, 'Ladieswear', 16, 'Womens Everyday Basics', 1002, 'Jersey Basic', 'Top with straps.'),
    ('0108775044', '0108775', 'Strap Top', 253, 'Vest top', 'Garment Upper body', 1010016, 'Solid', 10, 'White', 3, 'Light', 9, 'White', 1676, 'Jersey Basic', 'A', 'Ladieswear', 1, 'Ladieswear', 16, 'Womens Everyday Basics', 1002, 'Jersey Basic', 'Top with straps.'),
    ('0505221004', '0505221', 'Slim Denim', 272, 'Trousers', 'Garment Lower body', 1010016, 'Solid', 9, 'Black', 4, 'Dark', 5, 'Black', 1722, 'Denim Trousers', 'A', 'Ladieswear', 1, 'Ladieswear', 16, 'Womens Everyday Basics', 1009, 'Trousers', 'Denim jeans.'),
    ('0685687003', '0685687', 'Linen Shirt', 259, 'Shirt', 'Garment Upper body', 1010017, 'Stripe', 11, 'Off White', 1, 'Dusty Light', 9, 'White', 1676, 'Jersey Basic', 'A', 'Ladieswear', 1, 'Ladieswear', 16, 'Womens Everyday Basics', 1002, 'Jersey Basic', 'Linen shirt.'),
    ('0706016001', '0706016', 'Summer Dress', 265, 'Dress', 'Garment Full body', 1010016, 'Solid', 10, 'White', 3, 'Light', 9, 'White', 1522, 'Dresses', 'A', 'Ladieswear', 1, 'Ladieswear', 16, 'Womens Everyday Basics', 1010, 'Dresses', 'Summer dress.');
    """)

    # 3. Insert Mock Customers (6 customers across lifecycle stages)
    conn.execute("""
    INSERT INTO customers VALUES
    ('cust_active_01', 1.0, 1.0, 'ACTIVE', 'Regularly', 28.0, 'post_01'),
    ('cust_active_02', 1.0, 1.0, 'ACTIVE', 'Regularly', 34.0, 'post_02'),
    ('cust_emerging', 0.0, 0.0, 'ACTIVE', 'NONE', 22.0, 'post_03'),
    ('cust_cooling', 1.0, 1.0, 'ACTIVE', 'Monthly', 45.0, 'post_04'),
    ('cust_at_risk', 0.0, 0.0, 'PRE-CREATE', 'NONE', 52.0, 'post_05'),
    ('cust_dormant', 0.0, 0.0, 'LEFT CLUB', 'NONE', 60.0, 'post_06');
    """)

    # 4. Insert Mock Transactions (spanning dates 2020-01-01 to 2020-09-20)
    # Reference date is 2020-09-20
    conn.execute("""
    INSERT INTO transactions VALUES
    -- cust_active_01: frequent buyer, last bought 2020-09-18 (recency 2d)
    ('2020-09-18', 'cust_active_01', '0108775015', 0.025, 2),
    ('2020-09-18', 'cust_active_01', '0505221004', 0.040, 2),
    ('2020-09-10', 'cust_active_01', '0108775044', 0.025, 1),
    ('2020-08-25', 'cust_active_01', '0685687003', 0.030, 2),
    ('2020-08-10', 'cust_active_01', '0108775015', 0.025, 2),
    ('2020-07-15', 'cust_active_01', '0706016001', 0.050, 1),
    ('2020-06-20', 'cust_active_01', '0108775015', 0.025, 2),
    ('2020-05-10', 'cust_active_01', '0505221004', 0.040, 2),
    ('2020-04-12', 'cust_active_01', '0685687003', 0.030, 1),
    ('2020-03-01', 'cust_active_01', '0108775015', 0.025, 2),
    ('2020-02-15', 'cust_active_01', '0108775044', 0.025, 2),
    ('2020-01-20', 'cust_active_01', '0505221004', 0.040, 1),

    -- cust_active_02: recently active (recency 5d), bought twice
    ('2020-09-15', 'cust_active_02', '0108775015', 0.025, 2),
    ('2020-08-01', 'cust_active_02', '0505221004', 0.040, 1),

    -- cust_emerging: first observed in August 2020 (<=90d ago), bought 2 times
    ('2020-09-12', 'cust_emerging', '0706016001', 0.050, 2),
    ('2020-08-15', 'cust_emerging', '0108775015', 0.025, 2),

    -- cust_cooling: last bought 2020-07-20 (~60d ago)
    ('2020-07-20', 'cust_cooling', '0108775044', 0.025, 1),
    ('2020-05-15', 'cust_cooling', '0505221004', 0.040, 1),

    -- cust_at_risk: last bought 2020-05-01 (~140d ago)
    ('2020-05-01', 'cust_at_risk', '0685687003', 0.030, 2),

    -- cust_dormant: last bought 2020-01-10 (>250d ago)
    ('2020-01-10', 'cust_dormant', '0108775015', 0.025, 1);
    """)

    yield conn
    conn.close()
