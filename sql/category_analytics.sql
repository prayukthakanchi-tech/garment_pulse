-- ============================================================================
-- GarmentPulse — Category Analytics SQL
-- Performance, growth, momentum, concentration and attribute queries.
-- ============================================================================

-- 1. Category Performance Overview (Configurable level)
-- Computes volume, customers, catalog breadth, volume share, avg price index
SELECT
    a.department_name AS category_name,
    COUNT(*) AS purchase_volume,
    COUNT(DISTINCT t.customer_id) AS unique_customers,
    COUNT(DISTINCT t.article_id) AS active_articles,
    AVG(t.price) AS avg_price_index,
    SUM(t.price) AS total_price_contribution,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 2) AS volume_share_pct
FROM transactions t
JOIN articles a ON t.article_id = a.article_id
GROUP BY a.department_name
HAVING COUNT(*) >= 100
ORDER BY purchase_volume DESC;

-- 2. Category Period-over-Period Growth & Momentum (Recent 4 weeks vs Previous 4 weeks)
WITH date_bounds AS (
    SELECT MAX(t_dat) AS max_date FROM transactions
),
periods AS (
    SELECT
        max_date,
        max_date - INTERVAL 28 DAYS AS recent_start,
        max_date - INTERVAL 56 DAYS AS prev_start
    FROM date_bounds
),
period_volumes AS (
    SELECT
        a.department_name AS category_name,
        COUNT(CASE WHEN t.t_dat > p.recent_start AND t.t_dat <= p.max_date THEN 1 END) AS recent_volume,
        COUNT(CASE WHEN t.t_dat > p.prev_start AND t.t_dat <= p.recent_start THEN 1 END) AS prev_volume,
        COUNT(DISTINCT CASE WHEN t.t_dat > p.recent_start AND t.t_dat <= p.max_date THEN t.customer_id END) AS recent_customers,
        COUNT(DISTINCT CASE WHEN t.t_dat > p.prev_start AND t.t_dat <= p.recent_start THEN t.customer_id END) AS prev_customers
    FROM transactions t
    JOIN articles a ON t.article_id = a.article_id
    CROSS JOIN periods p
    WHERE t.t_dat > p.prev_start AND t.t_dat <= p.max_date
    GROUP BY a.department_name
)
SELECT
    category_name,
    recent_volume,
    prev_volume,
    recent_customers,
    prev_customers,
    CASE
        WHEN prev_volume > 0 THEN ROUND((recent_volume - prev_volume) * 1.0 / prev_volume, 4)
        ELSE NULL
    END AS volume_growth_rate,
    CASE
        WHEN prev_customers > 0 THEN ROUND((recent_customers - prev_customers) * 1.0 / prev_customers, 4)
        ELSE NULL
    END AS customer_growth_rate
FROM period_volumes
WHERE (recent_volume + prev_volume) >= 100
ORDER BY volume_growth_rate DESC NULLS LAST;

-- 3. Product Concentration within Categories (Herfindahl-Hirschman Index / HHI)
-- HHI = sum of squared shares of articles within category (scaled 0 to 10,000)
WITH article_shares AS (
    SELECT
        a.department_name AS category_name,
        t.article_id,
        COUNT(*) AS article_volume,
        COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (PARTITION BY a.department_name) AS share_pct
    FROM transactions t
    JOIN articles a ON t.article_id = a.article_id
    GROUP BY a.department_name, t.article_id
)
SELECT
    category_name,
    COUNT(DISTINCT article_id) AS active_articles,
    ROUND(SUM(share_pct * share_pct), 1) AS hhi_concentration,
    CASE
        WHEN SUM(share_pct * share_pct) > 2500 THEN 'Highly Concentrated'
        WHEN SUM(share_pct * share_pct) > 1500 THEN 'Moderately Concentrated'
        ELSE 'Diversified Demand'
    END AS concentration_tier
FROM article_shares
GROUP BY category_name
HAVING COUNT(DISTINCT article_id) >= 5
ORDER BY hhi_concentration DESC;
