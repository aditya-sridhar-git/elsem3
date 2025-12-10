# inventory_sentinel.py - LangChain Enhanced

import pandas as pd
import numpy as np
from dataclasses import dataclass
from typing import Optional
from functools import lru_cache
from config import CFG, HAS_ARIMA, ARIMA, HAS_LANGCHAIN, llm

# Always import pydantic
try:
    from pydantic import BaseModel, Field
except ImportError:
    BaseModel = None
    Field = None

if HAS_LANGCHAIN:
    from langchain_core.prompts import ChatPromptTemplate


class InventoryInsight(BaseModel):
    """Structured output for LLM inventory analysis"""
    risk_assessment: str = Field(description="Assessment of inventory risk")
    demand_pattern: str = Field(description="Analysis of demand patterns")
    reorder_strategy: str = Field(description="Strategic reorder recommendation")
    confidence_score: float = Field(description="Confidence in recommendations (0-1)")


@dataclass
class InventorySentinelAgent:
    """
    Agent 2: Inventory Sentinel (LangChain Enhanced)
    
    Hybrid approach:
    - Mathematical forecasting (ARIMA/WMA) for accuracy
    - LLM analysis (LangChain) for risk assessment and strategy
    """

    min_arima_history_days: int = CFG.min_arima_history_days
    forecast_horizon_days: int = CFG.forecast_horizon_days
    wma_window_days: int = CFG.wma_window_days
    buffer_days: int = CFG.lead_time_buffer_days
    uncertainty_factor: float = CFG.demand_uncertainty_factor
    min_velocity: float = CFG.min_velocity_for_risk

    def __post_init__(self):
        """Initialize LangChain components if enabled"""
        if HAS_LANGCHAIN and CFG.enable_inventory_sentinel_llm and llm:
            self.has_llm = True
        else:
            self.has_llm = False

    def _forecast_velocity_arima(self, series: pd.Series) -> Optional[float]:
        """
        Use ARIMA to forecast average daily demand over the forecast horizon.
        Returns None if ARIMA not available or fails.
        """
        if not HAS_ARIMA or ARIMA is None:
            return None

        try:
            model = ARIMA(series, order=(1, 1, 1))
            model_fit = model.fit()
            forecast = model_fit.forecast(steps=self.forecast_horizon_days)
            velocity = float(np.mean(forecast))
            return max(velocity, 0.0)  # Ensure non-negative
        except Exception:
            return None

    def _forecast_velocity_wma(self, series: pd.Series) -> float:
        """
        Weighted moving average: recent days weighted more heavily.
        """
        if len(series) == 0:
            return 0.0

        window = min(self.wma_window_days, len(series))
        recent = series.iloc[-window:]
        
        weights = np.arange(1, window + 1)
        wma = np.average(recent.values, weights=weights)
        return max(float(wma), 0.0)

    def _forecast_velocity_for_sku(
        self,
        sku_id: str,
        df_sales: pd.DataFrame,
        use_arima_if_available: bool = True
    ) -> float:
        """
        Forecast velocity for a single SKU.
        """
        sku_sales = df_sales[df_sales["sku_id"] == sku_id].copy()
        
        if sku_sales.empty:
            return 0.0

        sku_sales = sku_sales.sort_values("date")
        series = sku_sales["units_sold"]

        # Try ARIMA if enabled and enough history
        if use_arima_if_available and len(series) >= self.min_arima_history_days:
            arima_vel = self._forecast_velocity_arima(series)
            if arima_vel is not None:
                return arima_vel

        # Fallback to WMA
        return self._forecast_velocity_wma(series)

    def compute_inventory_metrics(
        self,
        df_profit_enriched: pd.DataFrame,
        df_sales: pd.DataFrame
    ) -> pd.DataFrame:
        """
        Compute inventory metrics with optional LLM enhancement
        """
        # STEP 1: Mathematical calculations (always run)
        df = df_profit_enriched.copy()

        # Forecast velocity for each SKU
        sku_ids = df["sku_id"].unique()
        velocity_map = {}
        
        for sku_id in sku_ids:
            velocity_map[sku_id] = self._forecast_velocity_for_sku(sku_id, df_sales)

        df["sales_velocity_per_day"] = df["sku_id"].map(velocity_map).fillna(0.0)

        # Days of stock left
        df["days_of_stock_left"] = np.where(
            df["sales_velocity_per_day"] > self.min_velocity,
            df["current_stock"] / df["sales_velocity_per_day"],
            999.0  # Very high if no sales
        )

        # Risk classification
        critical = df["days_of_stock_left"] < df["lead_time_days"]
        warning = (
            (df["days_of_stock_left"] >= df["lead_time_days"])
            & (df["days_of_stock_left"] < (df["lead_time_days"] + self.buffer_days))
        )
        no_history = df["sales_velocity_per_day"] < self.min_velocity

        df["risk_level"] = "SAFE"
        df.loc[warning, "risk_level"] = "WARNING"
        df.loc[critical, "risk_level"] = "CRITICAL"
        df.loc[no_history, "risk_level"] = "NO_HISTORY"

        # Reorder quantity
        should_reorder = (
            ((df["risk_level"] == "CRITICAL") | (df["risk_level"] == "WARNING"))
            & (df["profit_per_unit"] > 0)
        )

        df["reorder_qty_suggested"] = 0
        df.loc[should_reorder, "reorder_qty_suggested"] = (
            df.loc[should_reorder, "sales_velocity_per_day"]
            * df.loc[should_reorder, "lead_time_days"]
            * self.uncertainty_factor
        ).astype(int)

        # Profit at risk
        df["profit_at_risk"] = np.where(
            df["profit_per_unit"] > 0,
            df["profit_per_unit"] * df["sales_velocity_per_day"] * df["days_of_stock_left"],
            0.0
        )

        # STEP 2: LLM Enhancement (optional)
        if self.has_llm and CFG.enable_inventory_sentinel_llm:
            df = self._add_llm_insights(df)

        return df

    def _add_llm_insights(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Add LLM-generated inventory insights
        
        Only analyzes:
        - CRITICAL risk products
        - WARNING risk products with high profit at risk
        """
        # Initialize LLM insight columns
        df["llm_inventory_insight"] = ""
        df["llm_inventory_confidence"] = 0.0
        
        # Find SKUs that need LLM analysis
        needs_analysis = (
            (df["risk_level"] == "CRITICAL") |
            ((df["risk_level"] == "WARNING") & (df["profit_at_risk"] > df["profit_at_risk"].median()))
        )
        
        analysis_count = needs_analysis.sum()
        if analysis_count == 0:
            return df
        
        print(f"[INFO] Inventory Sentinel: Analyzing {analysis_count} SKUs with LLM...")
        
        for idx in df[needs_analysis].index:
            try:
                row = df.loc[idx]
                
                # Generate LLM insight using direct invocation
                prompt = f"""You are an inventory expert. Analyze:

Product: {row['product_name']}
Stock: {row['current_stock']} units, {round(row['days_of_stock_left'], 1)} days left
Velocity: {round(row['sales_velocity_per_day'], 1)} units/day
Lead Time: {row['lead_time_days']} days
Risk: {row['risk_level']}
Profit/Unit: ₹{round(row['profit_per_unit'], 2)}

Provide: 1) Risk assessment 2) Demand pattern 3) Reorder strategy. Be concise."""
                
                result = llm.invoke(prompt).content
                
                df.at[idx, "llm_inventory_insight"] = result.strip()
                df.at[idx, "llm_inventory_confidence"] = 0.85
                
            except Exception as e:
                print(f"[WARNING] LLM analysis failed for {row['sku_id']}: {str(e)}")
                df.at[idx, "llm_inventory_insight"] = "Analysis unavailable"
                df.at[idx, "llm_inventory_confidence"] = 0.0
        
        print(f"[INFO] Inventory Sentinel: LLM analysis complete")
        
        return df


# Standalone usage
if __name__ == "__main__":
    import os
    import sys
    
    if os.path.exists(CFG.sku_master_path) and os.path.exists(CFG.sales_history_path):
        from profit_doctor import ProfitDoctorAgent
        
        df_master = pd.read_csv(CFG.sku_master_path)
        df_sales = pd.read_csv(CFG.sales_history_path)
        
        # Run profit doctor first
        profit_agent = ProfitDoctorAgent()
        df_profit = profit_agent.compute_profit_metrics(df_master)
        
        # Run inventory sentinel
        inventory_agent = InventorySentinelAgent()
        result = inventory_agent.compute_inventory_metrics(df_profit, df_sales)
        
        print("\n" + "="*80)
        print("INVENTORY SENTINEL ANALYSIS")
        print("="*80)
        print(f"\nLangChain Enabled: {HAS_LANGCHAIN and CFG.enable_inventory_sentinel_llm}")
        print(f"Total SKUs: {len(result)}")
        print(f"CRITICAL: {(result['risk_level'] == 'CRITICAL').sum()}")
        print(f"WARNING: {(result['risk_level'] == 'WARNING').sum()}")
        print(f"SAFE: {(result['risk_level'] == 'SAFE').sum()}")
        
        if HAS_LANGCHAIN and "llm_inventory_insight" in result.columns:
            insights = result[result["llm_inventory_insight"] != ""]
            print(f"\nLLM Insights Generated: {len(insights)}")
            
            if len(insights) > 0:
                print("\nSample Insight:")
                sample = insights.iloc[0]
                print(f"  Product: {sample['product_name']}")
                print(f"  Risk: {sample['risk_level']}")
                print(f"  Days Left: {sample['days_of_stock_left']:.1f}")
                print(f"  Insight: {sample['llm_inventory_insight']}")
        
        print("="*80)
    else:
        print(f"[ERROR] Required files not found")
        sys.exit(1)
