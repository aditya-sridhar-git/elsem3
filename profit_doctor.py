# profit_doctor.py - LangChain Enhanced

import pandas as pd
import numpy as np
from dataclasses import dataclass
import time
from typing import Optional
from config import CFG, HAS_LANGCHAIN, llm

# Always import pydantic (used for data validation)
try:
    from pydantic import BaseModel, Field
except ImportError:
    BaseModel = None
    Field = None

if HAS_LANGCHAIN:
    from langchain_core.prompts import ChatPromptTemplate


class ProfitInsight(BaseModel):
    """Structured output for LLM profit analysis"""
    profitability_assessment: str = Field(description="Brief assessment of product profitability")
    pricing_recommendation: str = Field(description="Pricing strategy recommendation")
    cost_optimization: str = Field(description="Cost reduction suggestions")
    confidence_score: float = Field(description="Confidence in recommendations (0-1)")


@dataclass
class ProfitDoctorAgent:
    """
    Agent 2: Profit Doctor (LangChain Enhanced)
    
    Hybrid approach:
    - Mathematical calculations (pandas/numpy) for accuracy
    - LLM analysis (LangChain) for insights and recommendations
    """
    
    fee_gst_rate: float = CFG.fee_gst_rate
    
    def __post_init__(self):
        """Initialize LangChain components if enabled"""
        if HAS_LANGCHAIN and CFG.enable_profit_doctor_llm and llm:
            self.has_llm = True
        else:
            self.has_llm = False
    
    def compute_profit_metrics(self, df_master: pd.DataFrame) -> pd.DataFrame:
        """
        Compute profit metrics with optional LLM enhancement
        """
        # STEP 1: Mathematical calculations (always run - fast and accurate)
        df = df_master.copy()
        
        # Discount / Effective Selling Price
        if "mrp" in df.columns:
            df["discount_applied"] = np.maximum(df["mrp"] - df["selling_price"], 0.0)
        else:
            df["discount_applied"] = 0.0
        
        df["effective_selling_price"] = df["selling_price"] - df["discount_applied"]
        
        # Payment fees + GST
        df["payment_fee"] = (
            (df["platform_fee_percent"] / 100.0) * df["effective_selling_price"]
            + df["platform_fixed_fee"]
        )
        df["fee_gst"] = self.fee_gst_rate * df["payment_fee"]
        df["total_fees"] = df["payment_fee"] + df["fee_gst"]
        
        # Ad cost per unit
        df["ad_cost_per_unit"] = np.divide(
            df["ad_spend_total_last_30_days"],
            df["units_sold_last_30_days"],
            out=np.zeros_like(df["ad_spend_total_last_30_days"], dtype=float),
            where=df["units_sold_last_30_days"] > 0
        )
        
        # Profit per unit
        df["profit_per_unit"] = (
            df["effective_selling_price"]
            - df["cogs"]
            - df["total_fees"]
            - df["ad_cost_per_unit"]
            - df["shipping_cost_per_unit"]
        )
        
        # Units sold per day
        df["units_sold_per_day"] = df["units_sold_last_30_days"] / 30.0
        
        # Loss per day for negative-margin SKUs
        is_loss = df["profit_per_unit"] < 0
        df["loss_per_day"] = np.where(
            is_loss,
            np.abs(df["profit_per_unit"]) * df["units_sold_per_day"],
            0.0
        )
        df["is_loss_maker"] = is_loss
        
        # STEP 2: LLM Enhancement (optional - adds insights)
        if self.has_llm and CFG.enable_profit_doctor_llm:
            df = self._add_llm_insights(df)
        
        return df
    
    def _add_llm_insights(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Add LLM-generated insights to profitable/loss-making products
        
        Only analyzes:
        - Loss-making products (profit < 0)
        - High-margin products (profit > median)
        
        This keeps costs low while providing insights where they matter most.
        """
        # Initialize LLM insight columns
        df["llm_profit_insight"] = ""
        df["llm_confidence"] = 0.0
        
        # Find SKUs that need LLM analysis
        needs_analysis = (
            (df["profit_per_unit"] < 0) |  # Loss makers
            (df["profit_per_unit"] > df["profit_per_unit"].median())  # High performers
        )
        
        analysis_count = needs_analysis.sum()
        if analysis_count == 0:
            return df
        
        print(f"[INFO] Profit Doctor: Analyzing {analysis_count} SKUs with LLM...")
        
        # Analyze in batches to avoid API rate limits
        for idx in df[needs_analysis].index:
            try:
                row = df.loc[idx]
                
                # Generate LLM insight using direct invocation
                prompt = f"""You are a profit optimization expert. Analyze:

Product: {row['product_name']}
Category: {row['category']}
Selling Price: ₹{row['selling_price']}
COGS: ₹{row['cogs']}
Profit/Unit: ₹{row['profit_per_unit']}
Daily Loss: ₹{row['loss_per_day']}

Provide: 1) Brief assessment 2) Pricing action 3) Cost tip. Be concise."""
                
                result = llm.invoke(prompt).content
                
                df.at[idx, "llm_profit_insight"] = result.strip()
                df.at[idx, "llm_confidence"] = 0.85  # Default confidence
                
                # Rate limiting
                if hasattr(CFG, 'llm_delay'):
                    time.sleep(CFG.llm_delay)
                else:
                    time.sleep(3) # Fallback
                
            except Exception as e:
                print(f"[WARNING] LLM analysis failed for {row['sku_id']}: {str(e)}")
                # Leave empty so it doesn't show as a broken insight
                df.at[idx, "llm_profit_insight"] = "" 
                df.at[idx, "llm_confidence"] = 0.0
        
        print(f"[INFO] Profit Doctor: LLM analysis complete")
        
        return df


# Standalone usage
if __name__ == "__main__":
    import sys
    import os
    
    # Load sample data
    if os.path.exists(CFG.sku_master_path):
        df = pd.read_csv(CFG.sku_master_path)
        
        agent = ProfitDoctorAgent()
        result = agent.compute_profit_metrics(df)
        
        print("\n" + "="*80)
        print("PROFIT DOCTOR ANALYSIS")
        print("="*80)
        print(f"\nLangChain Enabled: {HAS_LANGCHAIN and CFG.enable_profit_doctor_llm}")
        print(f"Total SKUs: {len(result)}")
        print(f"Profitable: {(result['profit_per_unit'] > 0).sum()}")
        print(f"Loss Makers: {(result['profit_per_unit'] < 0).sum()}")
        
        if HAS_LANGCHAIN and "llm_profit_insight" in result.columns:
            insights = result[result["llm_profit_insight"] != ""]
            print(f"\nLLM Insights Generated: {len(insights)}")
            
            if len(insights) > 0:
                print("\nSample Insight:")
                sample = insights.iloc[0]
                print(f"  Product: {sample['product_name']}")
                print(f"  Profit: ₹{sample['profit_per_unit']:.2f}/unit")
                print(f"  Insight: {sample['llm_profit_insight']}")
        
        print("="*80)
    else:
        print(f"[ERROR] File not found: {CFG.sku_master_path}")
        sys.exit(1)
