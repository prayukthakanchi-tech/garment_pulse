-- ============================================================================
-- GarmentPulse — Product Lifecycle Analytics SQL
-- Article-level velocity, observation periods, and lifecycle classifications.
-- Note: First observed purchase != launch date. Last observed != discontinuation.
-- ============================================================================

WITH date_bounds AS (
    SELECT MAX(t_dat) AS max_date FROM transactions
),
periods AS (
    SELECT
        max_date,
        max_date - INTERVAL 28 DAYS AS recent_start,
        max_date - INTERVAL 56 DAYS AS prev_start,
        max_date - INTERVAL 56 DAYS AS emerging_cutoff
    FROM date_bounds
),
article_activity AS (
    SELECT
        t.article_id,
        MIN(t.t_dat) AS first_observed_purchase,
        MAX(t.t_dat) AS last_observed_purchase,
        COUNT(DISTINCT DATE_TRUNC('week', t.t_dat)) AS active_weeks,
        COUNT(*) AS total_purchase_lines,
        COUNT(DISTINCT t.customer_id) AS unique_customers,
        AVG(t.price) AS avg_price_index,
        COUNT(CASE WHEN t.t_dat > p.recent_start AND t.t_dat <= p.max_date THEN 1 END) AS recent_4wk_volume,
        COUNT(CASE WHEN t.t_dat > p.prev_start AND t.t_dat <= p.recent_start THEN 1 END) AS prev_4wk_volume
    FROM transactions t
    CROSS JOIN periods p
    GROUP BY t.article_id
)
SELECT
    aa.article_id,
    a.prod_name,
    a.product_type_name,
    a.department_name,
    a.garment_group_name,
    a.colour_group_name,
    aa.first_observed_purchase,
    aa.last_observed_purchase,
    aa.active_weeks,
    aa.total_purchase_lines,
    aa.unique_customers,
    aa.avg_price_index,
    aa.recent_4wk_volume,
    aa.prev_4wk_volume,
    CASE
        WHEN aa.prev_4wk_volume > 0 THEN
            ROUND((aa.recent_4wk_volume - aa.prev_4wk_volume) * 1.0 / aa.prev_4wk_volume, 4)
        WHEN aa.recent_4wk_volume > 0 THEN 1.0
        ELSE 0.0
    END AS volume_growth_rate,
    -- Lifecycle Classification:
    CASE
        WHEN aa.total_purchase_lines < 5 THEN 'Low Activity'
        WHEN aa.first_observed_purchase > (SELECT emerging_cutoff FROM periods)
             AND aa.recent_4wk_volume >= 5 THEN 'Emerging'
        WHEN aa.prev_4wk_volume > 0
             AND ((aa.recent_4wk_volume - aa.prev_4wk_volume) * 1.0 / aa.prev_4wk_volume) > 0.20
             AND aa.recent_4wk_volume >= 5 THEN 'Accelerating'
        WHEN aa.prev_4wk_volume > 0
             AND ((aa.recent_4wk_volume - aa.prev_4wk_volume) * 1.0 / aa.prev_4wk_volume) < -0.20 THEN 'Slowing'
        ELSE 'Stable'
    END AS lifecycle_status
FROM article_activity aa
JOIN articles a ON aa.article_id = a.article_id;
