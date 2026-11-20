-- ============================================================================
-- GarmentPulse — Customer Lifecycle & RFM Analytics SQL
-- Measurable segmentation rules and repeat-purchase metrics.
-- ============================================================================

-- 1. Customer Activity & RFM Summary Base
WITH customer_activity AS (
    SELECT
        customer_id,
        MIN(t_dat) AS first_purchase_date,
        MAX(t_dat) AS last_purchase_date,
        COUNT(DISTINCT t_dat) AS distinct_purchase_days,
        COUNT(*) AS total_purchase_lines,
        SUM(price) AS total_price_contribution,
        AVG(price) AS avg_item_price_index
    FROM transactions
    GROUP BY customer_id
),
ref_date AS (
    SELECT MAX(t_dat) AS max_dataset_date FROM transactions
),
customer_rfm AS (
    SELECT
        ca.customer_id,
        ca.first_purchase_date,
        ca.last_purchase_date,
        DATEDIFF('day', ca.last_purchase_date, rd.max_dataset_date) AS recency_days,
        DATEDIFF('day', ca.first_purchase_date, rd.max_dataset_date) AS customer_age_days,
        ca.distinct_purchase_days,
        ca.total_purchase_lines,
        ca.total_price_contribution,
        ca.avg_item_price_index
    FROM customer_activity ca
    CROSS JOIN ref_date rd
)
-- 2. Customer Segmentation Classification
SELECT
    customer_id,
    recency_days,
    distinct_purchase_days,
    total_purchase_lines,
    total_price_contribution,
    CASE
        -- Frequent Buyers: high frequency and recently active
        WHEN distinct_purchase_days >= 10 AND recency_days <= 30 THEN 'Frequent Buyers'
        -- Emerging Customers: new within 90 days, returning at least once
        WHEN customer_age_days <= 90 AND distinct_purchase_days >= 2 THEN 'Emerging Customers'
        -- Recently Active: active in last 30 days
        WHEN recency_days <= 30 THEN 'Recently Active'
        -- Cooling Customers: 31-90 days since last purchase
        WHEN recency_days BETWEEN 31 AND 90 THEN 'Cooling Customers'
        -- At-Risk Customers: 91-180 days since last purchase
        WHEN recency_days BETWEEN 91 AND 180 THEN 'At-Risk Customers'
        -- Dormant Customers: >180 days since last purchase
        ELSE 'Dormant Customers'
    END AS customer_segment
FROM customer_rfm;
