"""
GarmentPulse — Guarded AI Business Insights Assistant (Module I)
Answers executive merchandising questions using strictly pre-verified SQL metrics.
THE LLM NEVER EXECUTES ARBITRARY SQL AND NEVER FABRICATES METRICS.
"""

from __future__ import annotations

import os
from typing import Any, Dict, List, Optional
import duckdb

from config.settings import DATA_LIMITATIONS


class AIBusinessAssistant:
    """Guarded decision-support assistant grounding business explanations in verified SQL data."""

    def __init__(self, conn: duckdb.DuckDBPyConnection):
        self.conn = conn
        self.api_key = os.environ.get("GEMINI_API_KEY", "")
        self.ai_enabled = bool(self.api_key)
        self.analytical_registry = self._register_analytical_functions()

    def _register_analytical_functions(self) -> Dict[str, Any]:
        """Pre-approved analytical functions mapped to specific decision intents."""
        return {
            "department_momentum": self._calc_department_momentum,
            "declining_garments": self._calc_declining_garments,
            "repeat_segments": self._calc_repeat_segments,
            "attribute_shifts": self._calc_attribute_shifts,
            "channel_dynamics": self._calc_channel_dynamics,
            "top_products": self._calc_top_products,
        }

    def _identify_intent(self, question: str) -> str:
        """Rule-based intent classifier mapping executive query to verified analytical routine."""
        q = question.lower()
        if any(w in q for w in ["momentum", "growth", "fastest", "growing", "demand signal", "accelerating"]):
            return "department_momentum"
        elif any(w in q for w in ["decline", "slowing", "cooling", "drop", "down", "falling"]):
            return "declining_garments"
        elif any(w in q for w in ["repeat", "segment", "retention", "customer", "loyal", "dormant", "rfm"]):
            return "repeat_segments"
        elif any(w in q for w in ["color", "colour", "attribute", "style", "garment group", "pattern"]):
            return "attribute_shifts"
        elif any(w in q for w in ["channel", "online", "store", "channel 1", "channel 2"]):
            return "channel_dynamics"
        elif any(w in q for w in ["product", "article", "sku", "item", "best seller"]):
            return "top_products"
        return "department_momentum"

    def _calc_department_momentum(self) -> Dict[str, Any]:
        """Verified SQL: Top departments by 4-week growth and volume."""
        sql = """
        WITH bounds AS (SELECT MAX(t_dat) AS max_date FROM transactions),
        periods AS (
            SELECT max_date, max_date - INTERVAL 28 DAYS AS recent, max_date - INTERVAL 56 DAYS AS prev
            FROM bounds
        ),
        growth AS (
            SELECT
                a.department_name,
                COUNT(CASE WHEN t.t_dat > p.recent THEN 1 END) AS recent_vol,
                COUNT(CASE WHEN t.t_dat <= p.recent AND t.t_dat > p.prev THEN 1 END) AS prev_vol
            FROM transactions t
            JOIN articles a ON t.article_id = a.article_id
            CROSS JOIN periods p
            WHERE t.t_dat > p.prev
            GROUP BY a.department_name
            HAVING COUNT(CASE WHEN t.t_dat <= p.recent AND t.t_dat > p.prev THEN 1 END) >= 500
        )
        SELECT
            department_name,
            recent_vol,
            prev_vol,
            ROUND((recent_vol - prev_vol) * 100.0 / prev_vol, 2) AS growth_pct
        FROM growth
        ORDER BY growth_pct DESC
        LIMIT 3
        """
        rows = self.conn.execute(sql).fetchdf().to_dict(orient="records")
        return {
            "intent": "department_momentum",
            "period": "Recent 4-week window vs Previous 4-week window",
            "data": rows,
            "metric_type": "Purchase Volume Growth (%)",
        }

    def _calc_declining_garments(self) -> Dict[str, Any]:
        """Verified SQL: Garment groups showing deceleration."""
        sql = """
        WITH bounds AS (SELECT MAX(t_dat) AS max_date FROM transactions),
        periods AS (
            SELECT max_date, max_date - INTERVAL 28 DAYS AS recent, max_date - INTERVAL 56 DAYS AS prev
            FROM bounds
        ),
        vols AS (
            SELECT
                a.garment_group_name,
                COUNT(CASE WHEN t.t_dat > p.recent THEN 1 END) AS recent_vol,
                COUNT(CASE WHEN t.t_dat <= p.recent AND t.t_dat > p.prev THEN 1 END) AS prev_vol
            FROM transactions t
            JOIN articles a ON t.article_id = a.article_id
            CROSS JOIN periods p
            WHERE t.t_dat > p.prev
            GROUP BY a.garment_group_name
            HAVING COUNT(*) >= 1000
        )
        SELECT
            garment_group_name,
            recent_vol,
            prev_vol,
            ROUND((recent_vol - prev_vol) * 100.0 / prev_vol, 2) AS growth_pct
        FROM vols
        ORDER BY growth_pct ASC
        LIMIT 3
        """
        rows = self.conn.execute(sql).fetchdf().to_dict(orient="records")
        return {
            "intent": "declining_garments",
            "period": "Recent 4 weeks vs Previous 4 weeks",
            "data": rows,
            "metric_type": "Volume Contraction (%)",
        }

    def _calc_repeat_segments(self) -> Dict[str, Any]:
        """Verified SQL: Customer segments by size and repeat frequency."""
        from src.segmentation.customer_intelligence import CustomerIntelligence
        ci = CustomerIntelligence(self.conn)
        df = ci.get_customer_segments()
        return {
            "intent": "repeat_segments",
            "period": "Full Historical Observation Window",
            "data": df.to_dict(orient="records")[:4],
            "metric_type": "Customer Segment Share & Repeat Frequency",
        }

    def _calc_attribute_shifts(self) -> Dict[str, Any]:
        """Verified SQL: Top colour and garment combinations."""
        sql = """
        SELECT
            a.colour_group_name,
            a.garment_group_name,
            COUNT(*) AS purchase_volume,
            ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM transactions), 2) AS share_pct
        FROM transactions t
        JOIN articles a ON t.article_id = a.article_id
        GROUP BY a.colour_group_name, a.garment_group_name
        ORDER BY purchase_volume DESC
        LIMIT 3
        """
        rows = self.conn.execute(sql).fetchdf().to_dict(orient="records")
        return {
            "intent": "attribute_shifts",
            "period": "Full Historical Observation Window",
            "data": rows,
            "metric_type": "Attribute Share (%)",
        }

    def _calc_channel_dynamics(self) -> Dict[str, Any]:
        """Verified SQL: Channel comparison overview."""
        from src.analytics.channel_intelligence import ChannelIntelligence
        chi = ChannelIntelligence(self.conn)
        df = chi.get_channel_overview()
        return {
            "intent": "channel_dynamics",
            "period": "Full Historical Observation Window",
            "data": df.to_dict(orient="records"),
            "metric_type": "Channel Volume Share & Normalized Price Index",
        }

    def _calc_top_products(self) -> Dict[str, Any]:
        """Verified SQL: Top products by volume."""
        sql = """
        SELECT
            t.article_id,
            a.prod_name,
            a.department_name,
            COUNT(*) AS purchase_volume,
            ROUND(AVG(t.price), 6) AS avg_price_index
        FROM transactions t
        JOIN articles a ON t.article_id = a.article_id
        GROUP BY t.article_id, a.prod_name, a.department_name
        ORDER BY purchase_volume DESC
        LIMIT 3
        """
        rows = self.conn.execute(sql).fetchdf().to_dict(orient="records")
        return {
            "intent": "top_products",
            "period": "Full Historical Observation Window",
            "data": rows,
            "metric_type": "Article Observed Purchase Volume",
        }

    def answer_question(self, question: str) -> Dict[str, Any]:
        """Generates a complete decision-support answer strictly grounded in pre-calculated SQL data."""
        intent = self._identify_intent(question)
        calc_fn = self.analytical_registry.get(intent, self._calc_department_momentum)
        metric_payload = calc_fn()

        # Build grounded business synthesis
        data = metric_payload["data"]
        period = metric_payload["period"]

        if intent == "department_momentum" and data:
            top = data[0]
            finding = f"'{top['department_name']}' demonstrated the highest recent demand momentum, accelerating by +{top['growth_pct']}%."
            evidence = f"Recent 4-week volume reached {top['recent_vol']:,} lines compared to {top['prev_vol']:,} in the previous period. Runners up include '{data[1]['department_name']}' (+{data[1]['growth_pct']}%) and '{data[2]['department_name']}' (+{data[2]['growth_pct']}%)."
            interpretation = "Rapid period-over-period expansion in this department indicates strong seasonal pull or assortment resonance."
            recommendation = f"Investigate the possibility of expanding assortment exposure and digital shelf priority for '{top['department_name']}'."
        elif intent == "declining_garments" and data:
            bottom = data[0]
            finding = f"'{bottom['garment_group_name']}' experienced the steepest purchasing deceleration ({bottom['growth_pct']}%)."
            evidence = f"Volume contracted from {bottom['prev_vol']:,} to {bottom['recent_vol']:,} lines across the recent 4-week window."
            interpretation = "Contraction in transaction volume reflects post-peak seasonal decay or style rotation away from this garment grouping."
            recommendation = f"Review markdown depth and assortment refresh timelines for '{bottom['garment_group_name']}'."
        elif intent == "repeat_segments" and data:
            top_seg = data[0]
            finding = f"'{top_seg['segment']}' represents the largest segment ({top_seg['segment_share_pct']}% of customer base)."
            evidence = f"{top_seg['customer_count']:,} customers in this tier with average purchase frequency of {top_seg['avg_purchase_days']} days."
            interpretation = "Understanding the distribution between single-purchase and repeat customers is critical for setting retention initiatives."
            recommendation = "Investigate tailored re-engagement promotions for Cooling and At-Risk customer cohorts."
        elif intent == "channel_dynamics" and data:
            ch2 = next((c for c in data if c.get("sales_channel_id") == 2), data[0])
            ch1 = next((c for c in data if c.get("sales_channel_id") == 1), data[-1])
            finding = f"Channel 2 drives the dominant share of purchase volume ({ch2.get('volume_share_pct')}% vs {ch1.get('volume_share_pct')}% in Channel 1)."
            evidence = f"Channel 2 volume: {ch2.get('purchase_volume'):,} lines across {ch2.get('unique_customers'):,} customers (Avg Price Index: {ch2.get('avg_normalised_price')})."
            interpretation = "Transaction volume concentration in Channel 2 suggests strong digital or specific channel adoption."
            recommendation = "Investigate assortment preferences and exclusive category lines across individual sales channels."
        else:
            finding = "Transaction analysis indicates strong category differentiation across observed periods."
            evidence = str(data[:2])
            interpretation = "Demand signals reflect heterogeneous shopping trajectories across customer clusters."
            recommendation = "Cross-validate recent velocity shifts with inventory stock records."

        return {
            "question": question,
            "intent": intent,
            "finding": finding,
            "supporting_metrics": data,
            "observation_period": period,
            "business_interpretation": interpretation,
            "recommended_action": recommendation,
            "limitations": "Inventory stock levels, return rates, and true currency revenues are not captured in the underlying dataset. Merchandising actions require operational supply chain verification.",
        }
