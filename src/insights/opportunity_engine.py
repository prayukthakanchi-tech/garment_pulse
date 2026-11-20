"""
GarmentPulse — Commercial Opportunity Engine (Module H)
Transparent multi-factor category opportunity scoring and structured 5-part business recommendations.
NOTE: Opportunity scores are relative heuristics, NOT scientifically validated commercial KPIs.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
import duckdb
import numpy as np
import pandas as pd

from config.settings import MIN_CATEGORY_TRANSACTIONS, OPPORTUNITY_WEIGHTS


class OpportunityEngine:
    """Computes relative opportunity scores and generates structured merchandising recommendations."""

    def __init__(
        self,
        conn: duckdb.DuckDBPyConnection,
        weights: Optional[Dict[str, float]] = None,
    ):
        self.conn = conn
        self.weights = weights or OPPORTUNITY_WEIGHTS

    def calculate_opportunity_scores(
        self,
        level: str = "department",
        min_volume: int = MIN_CATEGORY_TRANSACTIONS,
    ) -> pd.DataFrame:
        """Computes normalized components and composite opportunity scores across categories."""
        col = "department_name" if level == "department" else ("product_group_name" if "product" in level else "garment_group_name")

        sql = f"""
        WITH bounds AS (SELECT MAX(t_dat) AS max_date FROM transactions),
        periods AS (
            SELECT
                max_date,
                max_date - INTERVAL 28 DAYS AS recent_start,
                max_date - INTERVAL 56 DAYS AS prev_start
            FROM bounds
        ),
        category_metrics AS (
            SELECT
                a.{col} AS category_name,
                COUNT(*) AS total_volume,
                COUNT(CASE WHEN t.t_dat > p.recent_start THEN 1 END) AS recent_vol,
                COUNT(CASE WHEN t.t_dat <= p.recent_start AND t.t_dat > p.prev_start THEN 1 END) AS prev_vol,
                COUNT(DISTINCT CASE WHEN t.t_dat > p.recent_start THEN t.customer_id END) AS recent_custs,
                COUNT(DISTINCT CASE WHEN t.t_dat <= p.recent_start AND t.t_dat > p.prev_start THEN t.customer_id END) AS prev_custs,
                COUNT(DISTINCT t.article_id) AS active_articles,
                AVG(t.price) AS avg_price_index
            FROM transactions t
            JOIN articles a ON t.article_id = a.article_id
            CROSS JOIN periods p
            GROUP BY a.{col}
            HAVING COUNT(*) >= {min_volume}
        ),
        repeat_activity AS (
            SELECT
                cust_tx.category_name,
                COUNT(DISTINCT CASE WHEN cust_tx.tx_count > 1 THEN cust_tx.customer_id END) * 1.0 / 
                NULLIF(COUNT(DISTINCT cust_tx.customer_id), 0) AS repeat_rate
            FROM (
                SELECT t.customer_id, a.{col} AS category_name, COUNT(*) AS tx_count
                FROM transactions t
                JOIN articles a ON t.article_id = a.article_id
                CROSS JOIN periods p
                WHERE t.t_dat > p.prev_start
                GROUP BY t.customer_id, a.{col}
            ) cust_tx
            GROUP BY cust_tx.category_name
        ),
        article_agg AS (
            SELECT article_id, COUNT(*) AS art_vol
            FROM transactions
            GROUP BY article_id
        ),
        article_shares AS (
            SELECT
                a.{col} AS category_name,
                art.article_id,
                art.art_vol * 100.0 / SUM(art.art_vol) OVER (PARTITION BY a.{col}) AS art_share_pct
            FROM article_agg art
            JOIN articles a ON art.article_id = a.article_id
        ),
        concentration AS (
            SELECT
                category_name,
                SUM(art_share_pct * art_share_pct) AS hhi
            FROM article_shares
            GROUP BY category_name
        )
        SELECT
            cm.category_name,
            cm.total_volume,
            cm.recent_vol,
            cm.prev_vol,
            cm.recent_custs,
            cm.prev_custs,
            cm.active_articles,
            cm.avg_price_index,
            COALESCE(ra.repeat_rate, 0.0) AS repeat_rate,
            COALESCE(conc.hhi, 5000.0) AS hhi,
            CASE
                WHEN cm.prev_vol > 0 THEN (cm.recent_vol - cm.prev_vol) * 1.0 / cm.prev_vol
                ELSE 0.0
            END AS volume_growth,
            CASE
                WHEN cm.prev_custs > 0 THEN (cm.recent_custs - cm.prev_custs) * 1.0 / cm.prev_custs
                ELSE 0.0
            END AS customer_growth,
            cm.total_volume * 1.0 / SUM(cm.total_volume) OVER () AS category_contribution
        FROM category_metrics cm
        LEFT JOIN repeat_activity ra ON cm.category_name = ra.category_name
        LEFT JOIN concentration conc ON cm.category_name = conc.category_name
        """
        df = self.conn.execute(sql).fetchdf()
        if df.empty:
            return pd.DataFrame()

        # Min-max normalization helper
        def min_max_norm(series, invert: bool = False):
            s_min, s_max = series.min(), series.max()
            if s_max == s_min:
                return pd.Series(0.5, index=series.index)
            norm = (series - s_min) / (s_max - s_min)
            return (1.0 - norm) if invert else norm

        df["s_vol_growth"] = min_max_norm(df["volume_growth"].clip(-0.8, 1.5))
        df["s_cust_growth"] = min_max_norm(df["customer_growth"].clip(-0.8, 1.5))
        df["s_repeat"] = min_max_norm(df["repeat_rate"])
        df["s_contrib"] = min_max_norm(df["category_contribution"])
        # Invert HHI: lower concentration (broader demand) yields higher opportunity score
        df["s_concentration"] = min_max_norm(df["hhi"], invert=True)
        # Momentum signal proxy
        df["s_momentum"] = (df["s_vol_growth"] + df["s_cust_growth"]) / 2.0

        # Weighted Composite Opportunity Score (0 to 100)
        w = self.weights
        df["opportunity_score"] = (
            w["volume_growth"] * df["s_vol_growth"] +
            w["customer_growth"] * df["s_cust_growth"] +
            w["repeat_rate"] * df["s_repeat"] +
            w["category_contribution"] * df["s_contrib"] +
            w["product_concentration"] * df["s_concentration"] +
            w["attribute_momentum"] * df["s_momentum"]
        ) * 100.0

        df["opportunity_score"] = df["opportunity_score"].round(1)

        # Classifications
        def classify(row):
            if row["total_volume"] < min_volume:
                return "Insufficient Evidence"
            if row["opportunity_score"] >= 70.0:
                return "Strong Demand Signal"
            elif row["opportunity_score"] >= 52.0:
                return "Emerging Opportunity"
            elif row["opportunity_score"] >= 38.0:
                return "Stable Performer"
            else:
                return "Declining Demand Signal"

        df["classification"] = df.apply(classify, axis=1)
        df = df.sort_values(by="opportunity_score", ascending=False).reset_index(drop=True)
        return df

    def generate_recommendations(
        self,
        level: str = "department",
        min_volume: int = MIN_CATEGORY_TRANSACTIONS,
        top_n: int = 8,
        scores_df: Optional[pd.DataFrame] = None,
    ) -> List[Dict[str, Any]]:
        """Generates structured 5-part merchandising recommendation cards.
        
        Structure:
        - OBSERVATION: What happened in the data
        - EVIDENCE: Calculated metrics
        - BUSINESS IMPLICATION: Merchandising relevance
        - RECOMMENDED ACTION: Assortment investigation
        - LIMITATION: Missing inventory / cost context
        """
        df = scores_df if scores_df is not None else self.calculate_opportunity_scores(level=level, min_volume=min_volume)
        if df.empty:
            return []

        recs = []
        for _, row in df.head(top_n).iterrows():
            cat = row["category_name"]
            score = row["opportunity_score"]
            status = row["classification"]
            vol_growth = round(row["volume_growth"] * 100, 1)
            cust_growth = round(row["customer_growth"] * 100, 1)
            vol = int(row["total_volume"])
            recent = int(row["recent_vol"])
            prev = int(row["prev_vol"])
            repeat_pct = round(row["repeat_rate"] * 100, 1)

            if status == "Strong Demand Signal":
                implication = "Robust consumer pull with expanding customer participation indicates potential supply tailwinds."
                action = f"Investigate the possibility of expanding assortment exposure and merchandising feature space for {cat}."
            elif status == "Emerging Opportunity":
                implication = "Positive acceleration across both customer acquisition and purchase frequency signals emerging seasonal traction."
                action = f"Review top-performing articles within {cat} to explore targeted marketing campaigns."
            elif status == "Stable Performer":
                implication = "Steady purchase velocity provides predictable category foundation without signs of volatility."
                action = f"Maintain balanced assortment exposure for {cat} while monitoring margin indices."
            else:
                implication = "Cooling customer volume or decelerating velocity suggests shifting consumer preferences."
                action = f"Investigate potential markdown fatigue or style saturation in {cat}."

            recs.append({
                "category": cat,
                "opportunity_score": score,
                "classification": status,
                "observation": f"Recent 4-week purchase volume in '{cat}' shifted by {vol_growth}% ({recent:,} vs {prev:,} lines in previous window).",
                "evidence": f"Volume Growth: {vol_growth}%, Unique Customer Growth: {cust_growth}%, Repeat Buyer Ratio: {repeat_pct}%, Total Observed Lines: {vol:,}.",
                "business_implication": implication,
                "recommended_action": action,
                "limitation": "Inventory availability, stockout events, and promotional cost data are unavailable. Reassortment actions must be cross-checked with warehouse supply records before execution.",
            })

        return recs
