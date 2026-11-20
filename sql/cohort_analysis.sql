-- ============================================================================
-- GarmentPulse — Customer Monthly Cohort Retention SQL
-- Tracks repeat customer purchasing activity across subsequent calendar months.
-- Explicitly labeled: repeat purchasing activity, NOT platform/web retention.
-- ============================================================================

WITH customer_first_purchase AS (
    SELECT
        customer_id,
        DATE_TRUNC('month', MIN(t_dat)) AS cohort_month
    FROM transactions
    GROUP BY customer_id
),
customer_monthly_activity AS (
    SELECT DISTINCT
        t.customer_id,
        cfp.cohort_month,
        DATE_TRUNC('month', t.t_dat) AS activity_month,
        -- Month index: 0 = acquisition month, 1 = next month, etc.
        (YEAR(DATE_TRUNC('month', t.t_dat)) - YEAR(cfp.cohort_month)) * 12 +
        (MONTH(DATE_TRUNC('month', t.t_dat)) - MONTH(cfp.cohort_month)) AS period_number
    FROM transactions t
    JOIN customer_first_purchase cfp ON t.customer_id = cfp.customer_id
),
cohort_sizes AS (
    SELECT
        cohort_month,
        COUNT(DISTINCT customer_id) AS cohort_size
    FROM customer_first_purchase
    GROUP BY cohort_month
)
SELECT
    cma.cohort_month,
    cs.cohort_size,
    cma.period_number,
    COUNT(DISTINCT cma.customer_id) AS active_customers,
    ROUND(COUNT(DISTINCT cma.customer_id) * 100.0 / cs.cohort_size, 2) AS repeat_activity_rate_pct
FROM customer_monthly_activity cma
JOIN cohort_sizes cs ON cma.cohort_month = cs.cohort_month
GROUP BY cma.cohort_month, cs.cohort_size, cma.period_number
ORDER BY cma.cohort_month, cma.period_number;
