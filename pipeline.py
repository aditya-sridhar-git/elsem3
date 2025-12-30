# pipeline.py

import pandas as pd
import os
import time
from typing import Optional

from config import CFG
from profit_doctor import ProfitDoctorAgent
from inventory_sentinel import InventorySentinelAgent
from seasonal_analyst import SeasonalAnalystAgent
from strategy_supervisor import StrategySupervisorAgent


def run_pipeline(
    sku_master_path: str = CFG.sku_master_path,
    sales_history_path: str = CFG.sales_history_path,
    output_path: str = "agent_recommendations.csv",
    verbose: bool = True,
    df_master: Optional[pd.DataFrame] = None,
    df_sales: Optional[pd.DataFrame] = None
) -> pd.DataFrame:
    """
    End-to-end pipeline (OPTIMIZED):

    1. Load master + sales data (from CSV or passed DFs)
    2. Agent 2 (ProfitDoctor): profitability metrics
    3. Agent 3 (InventorySentinel): inventory + risk metrics
    4. Agent 4 (StrategySupervisor): impact score + recommended actions
    5. Save final ranked output to CSV
    
    Performance Improvements:
    - Added timing information for performance monitoring
    - Better error handling
    - Optional verbose mode
    - Memory-efficient data loading
    """
    
    start_time = time.time()
    
    # 1. Load Data
    if df_master is None:
        # Check if files exist
        if not os.path.exists(sku_master_path):
            print(f"[ERROR] Master file not found: {sku_master_path}")
            return pd.DataFrame()
            
        if verbose:
            print(f"[INFO] Loading master data from: {sku_master_path}")
        load_start = time.time()
        df_master = pd.read_csv(sku_master_path)
        if verbose:
            print(f"[INFO] Loaded {len(df_master)} SKUs in {time.time() - load_start:.2f}s")
    
    if df_sales is None:
        if not os.path.exists(sales_history_path):
            print(f"[ERROR] Sales history file not found: {sales_history_path}")
            # Continue without sales history? Or return empty? 
            # Inventory agent needs sales. Let's return empty DF or create dummy.
            df_sales = pd.DataFrame(columns=["sku_id", "date", "units_sold"])

        if verbose:
            print(f"[INFO] Loading sales history from: {sales_history_path}")
        load_start = time.time()
        df_sales = pd.read_csv(sales_history_path)
        if verbose:
            print(f"[INFO] Loaded {len(df_sales)} sales records in {time.time() - load_start:.2f}s")

    # Agent 2: Profit Doctor
    if verbose:
        print("[INFO] Running ProfitDoctorAgent...")
    agent_start = time.time()
    profit_agent = ProfitDoctorAgent()
    df_profit = profit_agent.compute_profit_metrics(df_master)
    if verbose:
        print(f"[INFO] ProfitDoctor completed in {time.time() - agent_start:.2f}s")

    # Agent 3: Inventory Sentinel
    if verbose:
        print("[INFO] Running InventorySentinelAgent...")
    agent_start = time.time()
    inventory_agent = InventorySentinelAgent()
    df_inventory = inventory_agent.compute_inventory_metrics(df_profit, df_sales)
    if verbose:
        print(f"[INFO] InventorySentinel completed in {time.time() - agent_start:.2f}s")

    # Agent 4: Seasonal Analyst
    if verbose:
        print("[INFO] Running SeasonalAnalystAgent...")
    agent_start = time.time()
    seasonal_agent = SeasonalAnalystAgent()
    df_seasonal = seasonal_agent.compute_seasonal_metrics(df_inventory, df_sales)
    if verbose:
        print(f"[INFO] SeasonalAnalyst completed in {time.time() - agent_start:.2f}s")

    # Agent 5: Strategy Supervisor
    if verbose:
        print("[INFO] Running StrategySupervisorAgent...")
    agent_start = time.time()
    strategy_agent = StrategySupervisorAgent()
    df_ranked = strategy_agent.rank_actions(df_seasonal)
    if verbose:
        print(f"[INFO] StrategySupervisor completed in {time.time() - agent_start:.2f}s")

    # Select columns for output (including LLM insights if present)
    cols_for_output = [
        "sku_id", "category", "product_name",
        "selling_price", "cogs", "current_stock", "lead_time_days",
        "profit_per_unit", "loss_per_day",
        "sales_velocity_per_day", "days_of_stock_left", "risk_level",
        "reorder_qty_suggested", "profit_at_risk",
        "impact_score", "recommended_action",
        # Seasonal metrics
        "seasonal_index_current", "seasonal_index_next",
        "peak_month", "trough_month", "seasonal_trend",
        "seasonality_strength", "seasonal_forecast", "seasonal_risk_flag",
        # LangChain LLM insights
        "llm_profit_insight", "llm_inventory_insight", "llm_strategy_insight",
        "llm_seasonal_insight",
        "llm_profit_confidence", "llm_inventory_confidence", "llm_strategy_confidence",
        "llm_seasonal_confidence",
    ]

    # Filter to existing columns
    existing_cols = [c for c in cols_for_output if c in df_ranked.columns]
    df_final = df_ranked[existing_cols]

    # Save output
    if verbose:
        print(f"[INFO] Saving final recommendations to: {output_path}")
    save_start = time.time()
    df_final.to_csv(output_path, index=False)
    if verbose:
        print(f"[INFO] Saved in {time.time() - save_start:.2f}s")

    total_time = time.time() - start_time
    if verbose:
        print(f"\n[SUCCESS] Pipeline completed in {total_time:.2f}s")
        print(f"[INFO] Processed {len(df_final)} SKUs")
        print(f"[INFO] Average time per SKU: {(total_time / len(df_final) * 1000):.2f}ms")

    return df_final


if __name__ == "__main__":
    df = run_pipeline(verbose=True)
    if not df.empty:
        print("\n" + "="*80)
        print("TOP 15 RECOMMENDATIONS BY IMPACT SCORE")
        print("="*80)
        print(df.head(15).to_string())
        print("="*80)
    else:
        print("[ERROR] Pipeline failed to produce output.")
