# seasonal_analyst.py - LangChain Enhanced Seasonal Analysis Agent

import pandas as pd
import numpy as np
from dataclasses import dataclass
import time
from typing import Optional, Dict, Tuple
from datetime import datetime
from config import CFG, HAS_ARIMA, HAS_LANGCHAIN, llm

# Import pydantic for structured output
try:
    from pydantic import BaseModel, Field
except ImportError:
    BaseModel = None
    Field = None

# Import SARIMA for seasonal decomposition
try:
    from statsmodels.tsa.statespace.sarimax import SARIMAX
    from statsmodels.tsa.seasonal import seasonal_decompose
    HAS_SARIMA = True
except ImportError:
    SARIMAX = None
    seasonal_decompose = None
    HAS_SARIMA = False
    print("[WARNING] statsmodels not installed. Seasonal analysis disabled.")

if HAS_LANGCHAIN:
    from langchain_core.prompts import ChatPromptTemplate


class SeasonalInsight(BaseModel):
    """Structured output for LLM seasonal analysis"""
    seasonal_assessment: str = Field(description="Assessment of seasonal patterns")
    inventory_recommendation: str = Field(description="Seasonal inventory strategy")
    pricing_recommendation: str = Field(description="Seasonal pricing strategy")
    timing_advice: str = Field(description="When to act based on seasonality")
    confidence_score: float = Field(description="Confidence in recommendations (0-1)")


# Month name mapping
MONTH_NAMES = {
    1: "January", 2: "February", 3: "March", 4: "April",
    5: "May", 6: "June", 7: "July", 8: "August",
    9: "September", 10: "October", 11: "November", 12: "December"
}


@dataclass
class SeasonalAnalystAgent:
    """
    Agent 4: Seasonal Analyst (LangChain Enhanced)
    
    Hybrid approach:
    - SARIMA decomposition for seasonal pattern extraction
    - Statistical analysis for seasonal indices
    - LLM analysis for strategic seasonal recommendations
    
    Key Outputs:
    - seasonal_index_current: Current month's seasonal multiplier
    - seasonal_index_next: Next month's expected multiplier
    - peak_month: Best performing month
    - trough_month: Worst performing month
    - seasonal_trend: RISING, FALLING, STABLE
    - seasonality_strength: 0-1 score
    - seasonal_risk_flag: TRUE if high stock entering low season
    """
    
    seasonal_period: int = 12  # Monthly seasonality
    min_history_days: int = 90  # Minimum days for analysis
    strength_threshold: float = 0.3  # Min strength for seasonal flags
    
    def __post_init__(self):
        """Initialize LangChain components if enabled"""
        if HAS_LANGCHAIN and hasattr(CFG, 'enable_seasonal_analyst_llm'):
            self.has_llm = CFG.enable_seasonal_analyst_llm and llm is not None
        elif HAS_LANGCHAIN and llm is not None:
            self.has_llm = True
        else:
            self.has_llm = False
    
    def _compute_monthly_aggregates(self, df_sales: pd.DataFrame, sku_id: str) -> pd.DataFrame:
        """
        Aggregate daily sales to monthly for seasonal analysis
        """
        sku_sales = df_sales[df_sales["sku_id"] == sku_id].copy()
        
        if sku_sales.empty:
            return pd.DataFrame()
        
        # Parse dates
        sku_sales["date"] = pd.to_datetime(sku_sales["date"])
        sku_sales["month"] = sku_sales["date"].dt.month
        sku_sales["year_month"] = sku_sales["date"].dt.to_period("M")
        
        # Aggregate to monthly
        monthly = sku_sales.groupby("year_month").agg({
            "units_sold": "sum",
            "month": "first"
        }).reset_index()
        
        monthly = monthly.sort_values("year_month")
        
        return monthly
    
    def _compute_seasonal_indices(self, monthly_sales: pd.DataFrame) -> Dict[int, float]:
        """
        Compute seasonal index for each month (1-12)
        Index > 1 means above average, < 1 means below average
        """
        if monthly_sales.empty or len(monthly_sales) < 3:
            return {m: 1.0 for m in range(1, 13)}
        
        # Calculate average sales per month
        overall_mean = monthly_sales["units_sold"].mean()
        
        if overall_mean == 0:
            return {m: 1.0 for m in range(1, 13)}
        
        # Group by month and get average
        monthly_avg = monthly_sales.groupby("month")["units_sold"].mean()
        
        # Calculate index
        indices = {}
        for m in range(1, 13):
            if m in monthly_avg.index:
                indices[m] = monthly_avg[m] / overall_mean
            else:
                indices[m] = 1.0
        
        return indices
    
    def _fit_sarima(self, monthly_sales: pd.DataFrame) -> Optional[Tuple[float, float]]:
        """
        Fit SARIMA model and return seasonality strength and forecast
        Returns: (seasonality_strength, next_month_forecast) or None if fails
        """
        if not HAS_SARIMA or len(monthly_sales) < self.seasonal_period:
            return None
        
        try:
            series = monthly_sales.set_index("year_month")["units_sold"]
            
            # Fit simple seasonal decomposition first
            if len(series) >= 12:
                decomp = seasonal_decompose(series, model='multiplicative', period=min(12, len(series)//2))
                
                # Calculate seasonality strength
                seasonal_var = np.var(decomp.seasonal.dropna())
                residual_var = np.var(decomp.resid.dropna())
                
                if (seasonal_var + residual_var) > 0:
                    strength = seasonal_var / (seasonal_var + residual_var)
                else:
                    strength = 0.0
            else:
                strength = 0.0
            
            # Fit SARIMA for forecast
            model = SARIMAX(
                series,
                order=(1, 0, 1),
                seasonal_order=(1, 0, 1, min(12, len(series)//2)),
                enforce_stationarity=False,
                enforce_invertibility=False
            )
            
            results = model.fit(disp=False, maxiter=100)
            forecast = results.forecast(steps=1)
            
            return (min(1.0, max(0.0, strength)), float(forecast.iloc[0]))
            
        except Exception as e:
            print(f"[WARNING] SARIMA fit failed: {str(e)}")
            return None
    
    def _determine_trend(self, indices: Dict[int, float], current_month: int) -> str:
        """
        Determine if we're in a RISING, FALLING, or STABLE seasonal period
        """
        current_idx = indices.get(current_month, 1.0)
        next_month = (current_month % 12) + 1
        next_idx = indices.get(next_month, 1.0)
        
        diff = next_idx - current_idx
        
        if diff > 0.1:
            return "RISING"
        elif diff < -0.1:
            return "FALLING"
        else:
            return "STABLE"
    
    def compute_seasonal_metrics(
        self,
        df_enriched: pd.DataFrame,
        df_sales: pd.DataFrame
    ) -> pd.DataFrame:
        """
        Compute seasonal metrics with optional LLM enhancement
        """
        df = df_enriched.copy()
        
        # Initialize new columns
        df["seasonal_index_current"] = 1.0
        df["seasonal_index_next"] = 1.0
        df["peak_month"] = ""
        df["trough_month"] = ""
        df["seasonal_trend"] = "STABLE"
        df["seasonality_strength"] = 0.0
        df["seasonal_forecast"] = 0.0
        df["seasonal_risk_flag"] = False
        df["llm_seasonal_insight"] = ""
        df["llm_seasonal_confidence"] = 0.0
        
        # Get current month
        current_month = datetime.now().month
        next_month = (current_month % 12) + 1
        
        print(f"[INFO] Seasonal Analyst: Analyzing {len(df)} SKUs for month {current_month}...")
        
        # Analyze each SKU
        for idx in df.index:
            sku_id = df.loc[idx, "sku_id"]
            
            try:
                # Get monthly aggregates
                monthly_sales = self._compute_monthly_aggregates(df_sales, sku_id)
                
                if monthly_sales.empty or len(monthly_sales) < 3:
                    continue
                
                # Compute seasonal indices
                indices = self._compute_seasonal_indices(monthly_sales)
                
                # Get current and next month indices
                df.at[idx, "seasonal_index_current"] = round(indices.get(current_month, 1.0), 3)
                df.at[idx, "seasonal_index_next"] = round(indices.get(next_month, 1.0), 3)
                
                # Find peak and trough
                peak_month = max(indices, key=indices.get)
                trough_month = min(indices, key=indices.get)
                df.at[idx, "peak_month"] = MONTH_NAMES[peak_month]
                df.at[idx, "trough_month"] = MONTH_NAMES[trough_month]
                
                # Determine trend
                df.at[idx, "seasonal_trend"] = self._determine_trend(indices, current_month)
                
                # Fit SARIMA for strength and forecast
                sarima_result = self._fit_sarima(monthly_sales)
                if sarima_result:
                    strength, forecast = sarima_result
                    df.at[idx, "seasonality_strength"] = round(strength, 3)
                    df.at[idx, "seasonal_forecast"] = round(forecast, 1)
                
                # Seasonal risk flag
                # High stock + entering low season + profitable = risk
                days_of_stock = df.loc[idx, "days_of_stock_left"] if "days_of_stock_left" in df.columns else 0
                entering_low_season = indices.get(next_month, 1.0) < 0.8
                is_profitable = df.loc[idx, "profit_per_unit"] > 0 if "profit_per_unit" in df.columns else True
                
                if days_of_stock > 45 and entering_low_season and is_profitable:
                    df.at[idx, "seasonal_risk_flag"] = True
                    
            except Exception as e:
                print(f"[WARNING] Seasonal analysis failed for {sku_id}: {str(e)}")
                continue
        
        # STEP 2: LLM Enhancement (optional)
        if self.has_llm:
            df = self._add_llm_insights(df)
        
        print(f"[INFO] Seasonal Analyst: Analysis complete")
        
        return df
    
    def _add_llm_insights(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Add LLM-generated seasonal insights
        
        Only analyzes:
        - Products with strong seasonality (strength > threshold)
        - Products with seasonal risk flag
        - Products entering peak/trough season
        """
        # Find SKUs that need LLM analysis
        needs_analysis = (
            (df["seasonality_strength"] > self.strength_threshold) |
            (df["seasonal_risk_flag"] == True) |
            (df["seasonal_trend"].isin(["RISING", "FALLING"]))
        )
        
        analysis_count = needs_analysis.sum()
        if analysis_count == 0:
            return df
        
        print(f"[INFO] Seasonal Analyst: Generating LLM insights for {analysis_count} SKUs...")
        
        for idx in df[needs_analysis].index:
            try:
                row = df.loc[idx]
                
                # Generate LLM insight
                prompt = f"""You are a seasonal business analyst. Analyze this product's seasonal patterns:

Product: {row['product_name']}
Category: {row['category']}
Current Month Index: {row['seasonal_index_current']:.2f} (1.0 = average)
Next Month Index: {row['seasonal_index_next']:.2f}
Peak Month: {row['peak_month']}
Trough Month: {row['trough_month']}
Seasonal Trend: {row['seasonal_trend']}
Seasonality Strength: {row['seasonality_strength']:.0%}
Seasonal Risk Flag: {row['seasonal_risk_flag']}
Current Stock Days: {row.get('days_of_stock_left', 'N/A')}
Profit/Unit: ₹{row.get('profit_per_unit', 0):.2f}

Provide concise recommendations:
1) Inventory action based on upcoming season
2) Pricing strategy for current season
3) Key timing to watch
Keep response under 100 words."""

                result = llm.invoke(prompt).content
                
                df.at[idx, "llm_seasonal_insight"] = result.strip()
                df.at[idx, "llm_seasonal_confidence"] = 0.85
                
                # Rate limiting
                if hasattr(CFG, 'llm_delay'):
                    time.sleep(CFG.llm_delay)
                else:
                    time.sleep(3)
                
            except Exception as e:
                print(f"[WARNING] LLM seasonal analysis failed for {row['sku_id']}: {str(e)}")
                df.at[idx, "llm_seasonal_insight"] = ""
                df.at[idx, "llm_seasonal_confidence"] = 0.0
        
        print(f"[INFO] Seasonal Analyst: LLM analysis complete")
        
        return df


# Standalone usage and testing
if __name__ == "__main__":
    import os
    import sys
    
    # Check for required files
    sku_master_path = "synthetic dataset/sku_master.csv"
    sales_history_path = "synthetic dataset/seasonal_sales_history.csv"
    
    if not os.path.exists(sku_master_path):
        print(f"[ERROR] SKU master not found: {sku_master_path}")
        sys.exit(1)
    
    if not os.path.exists(sales_history_path):
        print(f"[ERROR] Sales history not found: {sales_history_path}")
        sys.exit(1)
    
    # Load data
    print("[INFO] Loading data...")
    df_master = pd.read_csv(sku_master_path)
    df_sales = pd.read_csv(sales_history_path)
    
    print(f"[INFO] Loaded {len(df_master)} SKUs and {len(df_sales)} sales records")
    
    # Run profit doctor first (to get profit metrics)
    from profit_doctor import ProfitDoctorAgent
    profit_agent = ProfitDoctorAgent()
    df_profit = profit_agent.compute_profit_metrics(df_master)
    
    # Run inventory sentinel (to get days_of_stock_left)
    from inventory_sentinel import InventorySentinelAgent
    inventory_agent = InventorySentinelAgent()
    df_inventory = inventory_agent.compute_inventory_metrics(df_profit, df_sales)
    
    # Run seasonal analyst
    print("\n" + "="*80)
    print("SEASONAL ANALYST TESTING")
    print("="*80)
    
    seasonal_agent = SeasonalAnalystAgent()
    result = seasonal_agent.compute_seasonal_metrics(df_inventory, df_sales)
    
    print(f"\nLangChain Enabled: {seasonal_agent.has_llm}")
    print(f"SARIMA Available: {HAS_SARIMA}")
    print(f"Total SKUs Analyzed: {len(result)}")
    print(f"SKUs with Strong Seasonality: {(result['seasonality_strength'] > 0.3).sum()}")
    print(f"SKUs with Seasonal Risk: {result['seasonal_risk_flag'].sum()}")
    
    print("\nTop 5 Most Seasonal Products:")
    top_seasonal = result.nlargest(5, "seasonality_strength")[
        ["product_name", "peak_month", "trough_month", "seasonality_strength", "seasonal_trend"]
    ]
    print(top_seasonal.to_string(index=False))
    
    print("\nSeasonal Risk Alerts:")
    risk_items = result[result["seasonal_risk_flag"] == True][
        ["product_name", "seasonal_index_next", "days_of_stock_left"]
    ]
    if len(risk_items) > 0:
        print(risk_items.to_string(index=False))
    else:
        print("  No seasonal risks detected")
    
    if HAS_LANGCHAIN and "llm_seasonal_insight" in result.columns:
        insights = result[result["llm_seasonal_insight"] != ""]
        print(f"\nLLM Seasonal Insights Generated: {len(insights)}")
        
        if len(insights) > 0:
            print("\nSample Insight:")
            sample = insights.iloc[0]
            print(f"  Product: {sample['product_name']}")
            print(f"  Peak: {sample['peak_month']}, Trough: {sample['trough_month']}")
            print(f"  Insight: {sample['llm_seasonal_insight'][:200]}...")
    
    print("\n" + "="*80)
    
    # Save results
    output_path = "seasonal_analysis_results.csv"
    result.to_csv(output_path, index=False)
    print(f"[SUCCESS] Results saved to {output_path}")
