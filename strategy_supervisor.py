# strategy_supervisor.py - LangChain Enhanced

import pandas as pd
import numpy as np
import time
from dataclasses import dataclass
from config import CFG, HAS_LANGCHAIN, llm

# Always import pydantic
try:
    from pydantic import BaseModel, Field
except ImportError:
    BaseModel = None
    Field = None

if HAS_LANGCHAIN:
    from langchain_core.prompts import ChatPromptTemplate


class StrategyRecommendation(BaseModel):
    """Structured output for LLM strategy analysis"""
    action_rationale: str = Field(description="Why this action is recommended")
    implementation_steps: str = Field(description="How to implement the action")
    expected_outcome: str = Field(description="Expected business impact")
    priority_justification: str = Field(description="Why this priority level")
    confidence_score: float = Field(description="Confidence in strategy (0-1)")


@dataclass
class StrategySupervisorAgent:
    """
    Agent 3: Strategy Supervisor (LangChain Enhanced)
    
    Hybrid approach:
    - Mathematical impact scoring (numpy) for objectivity
    - LLM strategic reasoning (LangChain) for context and nuance
    """
    
    loss_per_day_threshold: float = CFG.loss_per_day_threshold
    min_days_urgency: float = CFG.min_days_for_urgency
    
    def __post_init__(self):
        """Initialize LangChain components if enabled"""
        if HAS_LANGCHAIN and CFG.enable_strategy_supervisor_llm and llm:
            self.has_llm = True
        else:
            self.has_llm = False

    def rank_actions(self, df_enriched: pd.DataFrame) -> pd.DataFrame:
        """
        Rank SKUs by recommended action and priority with optional LLM enhancement
        """
        # STEP 1: Mathematical calculations (always run)
        df = df_enriched.copy()

        # Impact score (higher = more urgent)
        df["impact_score"] = np.where(
            df["days_of_stock_left"] > 0,
            (df["profit_at_risk"] + df["loss_per_day"]) / df["days_of_stock_left"],
            0.0
        )

        # Rule-based action recommendation
        conditions = [
            # CRITICAL profitable SKU
            (df["risk_level"] == "CRITICAL") & (df["profit_per_unit"] > 0),
            
            # High daily loss
            (df["is_loss_maker"]) & (df["loss_per_day"] > self.loss_per_day_threshold),
            
            # WARNING profitable SKU
            (df["risk_level"] == "WARNING") & (df["profit_per_unit"] > 0),
            
            # Overstocked slow mover
            (df["risk_level"] == "SAFE") & (df["days_of_stock_left"] > 90) & (df["sales_velocity_per_day"] < 1),
            
            # Moderate loss maker
            (df["is_loss_maker"]) & (df["loss_per_day"] <= self.loss_per_day_threshold),
        ]

        choices = [
            "REORDER_IMMEDIATELY",
            "PAUSE_ADS_OR_INCREASE_PRICE",
            "PLAN_REORDER",
            "DISCOUNT_TO_MOVE_STOCK",
            "REVIEW_PRICING",
        ]

        df["recommended_action"] = np.select(conditions, choices, default="MONITOR")

        # Priority flag
        df["is_high_priority"] = (
            ((df["risk_level"] == "CRITICAL") & (df["profit_per_unit"] > 0))
            | (df["loss_per_day"] > self.loss_per_day_threshold)
        )

        # STEP 2: LLM Enhancement (optional)
        if self.has_llm and CFG.enable_strategy_supervisor_llm:
            df = self._add_llm_insights(df)

        # Sort by impact score (descending)
        df = df.sort_values("impact_score", ascending=False).reset_index(drop=True)

        return df

    def _add_llm_insights(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Add LLM-generated strategic insights
        
        Only analyzes high-priority actions
        """
        # Initialize LLM insight columns
        df["llm_strategy_insight"] = ""
        df["llm_strategy_confidence"] = 0.0
        
        # Find SKUs that need LLM analysis (high priority items)
        needs_analysis = df["is_high_priority"] == True
        
        analysis_count = needs_analysis.sum()
        if analysis_count == 0:
            return df
        
        print(f"[INFO] Strategy Supervisor: Analyzing {analysis_count} high-priority SKUs with LLM...")
        
        for idx in df[needs_analysis].index:
            try:
                row = df.loc[idx]
                
                # Generate LLM strategy insight using direct invocation
                prompt = f"""You are a business strategist. Analyze:

Product: {row['product_name']}
Action: {row['recommended_action']}
Risk: {row['risk_level']}
Stock: {row['current_stock']} units, {round(row['days_of_stock_left'], 1)} days left
Profit/Unit: ₹{round(row['profit_per_unit'], 2)}
Profit at Risk: ₹{round(row['profit_at_risk'], 2)}
Impact: {round(row['impact_score'], 0)}

Provide: 1) Why this action 2) How to implement 3) Expected outcome 4) Priority. Be concise."""
                
                result = llm.invoke(prompt).content
                
                df.at[idx, "llm_strategy_insight"] = result.strip()
                df.at[idx, "llm_strategy_confidence"] = 0.90  # High confidence for strategy
                
                # Rate limiting
                if hasattr(CFG, 'llm_delay'):
                    time.sleep(CFG.llm_delay)
                else:
                    time.sleep(3)
                
            except Exception as e:
                print(f"[WARNING] LLM strategy failed for {row['sku_id']}: {str(e)}")
                df.at[idx, "llm_strategy_insight"] = ""
                df.at[idx, "llm_strategy_confidence"] = 0.0
        
        print(f"[INFO] Strategy Supervisor: LLM analysis complete")
        
        return df


# Standalone usage
if __name__ == "__main__":
    import os
    import sys
    
    if os.path.exists(CFG.sku_master_path) and os.path.exists(CFG.sales_history_path):
        from profit_doctor import ProfitDoctorAgent
        from inventory_sentinel import InventorySentinelAgent
        
        df_master = pd.read_csv(CFG.sku_master_path)
        df_sales = pd.read_csv(CFG.sales_history_path)
        
        # Run pipeline
        profit_agent = ProfitDoctorAgent()
        df_profit = profit_agent.compute_profit_metrics(df_master)
        
        inventory_agent = InventorySentinelAgent()
        df_inventory = inventory_agent.compute_inventory_metrics(df_profit, df_sales)
        
        strategy_agent = StrategySupervisorAgent()
        result = strategy_agent.rank_actions(df_inventory)
        
        print("\n" + "="*80)
        print("STRATEGY SUPERVISOR ANALYSIS")
        print("="*80)
        print(f"\nLangChain Enabled: {HAS_LANGCHAIN and CFG.enable_strategy_supervisor_llm}")
        print(f"Total SKUs: {len(result)}")
        print(f"High Priority: {result['is_high_priority'].sum()}")
        
        print("\nTop 5 Actions by Impact:")
        top5 = result.head(5)[["product_name", "recommended_action", "impact_score", "risk_level"]]
        for idx, row in top5.iterrows():
            print(f"  {idx+1}. {row['product_name']}: {row['recommended_action']} (Impact: {row['impact_score']:.0f})")
        
        if HAS_LANGCHAIN and "llm_strategy_insight" in result.columns:
            insights = result[result["llm_strategy_insight"] != ""]
            print(f"\nLLM Strategic Insights Generated: {len(insights)}")
            
            if len(insights) > 0:
                print("\nSample Strategic Insight:")
                sample = insights.iloc[0]
                print(f"  Product: {sample['product_name']}")
                print(f"  Action: {sample['recommended_action']}")
                print(f"  Insight: {sample['llm_strategy_insight']}")
        
        print("="*80)
    else:
        print(f"[ERROR] Required files not found")
        sys.exit(1)
