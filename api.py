# api.py

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import pandas as pd
import os
from datetime import datetime
import traceback

from config import CFG
from config import CFG
from pipeline import run_pipeline
from shopify_loader import ShopifyLoader

# Initialize FastAPI app
app = FastAPI(
    title="E-commerce Agent Dashboard API",
    description="API for visualizing e-commerce AI agents in action",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],  # React dev servers
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global state
pipeline_data: Optional[pd.DataFrame] = None
last_execution_time: Optional[datetime] = None
execution_status = {"status": "idle", "message": "Not yet executed"}
data_source: str = "none"  # Track data source: "shopify" or "csv" or "none"


# Pydantic models
class HealthResponse(BaseModel):
    status: str
    timestamp: str
    message: str


class AgentStatus(BaseModel):
    name: str
    status: str
    execution_time: Optional[float] = None
    metrics: Dict[str, Any]


class MetricsSummary(BaseModel):
    total_skus: int
    total_profitable: int
    total_loss_makers: int
    total_critical_risk: int
    total_warning_risk: int
    total_safe: int
    avg_profit_per_unit: float
    total_profit_at_risk: float
    total_daily_loss: float


class SKURecommendation(BaseModel):
    sku_id: str
    category: str
    product_name: str
    selling_price: float
    cogs: float
    current_stock: int
    lead_time_days: int
    profit_per_unit: float
    loss_per_day: float
    sales_velocity_per_day: float
    days_of_stock_left: float
    risk_level: str
    reorder_qty_suggested: float
    profit_at_risk: float
    impact_score: float
    recommended_action: str
    # LangChain LLM insights (optional)
    llm_profit_insight: Optional[str] = None
    llm_inventory_insight: Optional[str] = None
    llm_strategy_insight: Optional[str] = None
    llm_profit_confidence: Optional[float] = None
    llm_inventory_confidence: Optional[float] = None
    llm_strategy_confidence: Optional[float] = None


# Helper function to execute pipeline
def load_shopify_data():
    """Fetch data from Shopify and run pipeline"""
    global pipeline_data, last_execution_time, execution_status, data_source
    
    loader = ShopifyLoader()
    if not loader.validate_config():
        return False
        
    try:
        df_master, df_sales = loader.fetch_data()
        if df_master.empty:
            return False
            
        # Run pipeline with Shopify data
        pipeline_data = run_pipeline(verbose=True, df_master=df_master, df_sales=df_sales)
        last_execution_time = datetime.now()
        data_source = "shopify"
        execution_status = {
            "status": "success",
            "message": f"Shopify data loaded at {last_execution_time.strftime('%Y-%m-%d %H:%M:%S')}"
        }
        return True
    except Exception as e:
        print(f"[ERROR] Shopify load failed: {str(e)}")
        return False

def execute_pipeline():
    global pipeline_data, last_execution_time, execution_status, data_source
    
    # Try Shopify First
    if CFG.shopify_access_token and CFG.shopify_shop_domain and data_source != "shopify":
        print("[INFO] Attempting to load Shopify data...")
        if load_shopify_data():
            return True
            
    # Don't overwrite Shopify data with CSV data
    if data_source == "shopify":
        print("[INFO] Shopify data active. Skipping CSV pipeline.")
        return True
    
    # Don't re-run if we already have CSV data (avoids timeout on refresh)
    if data_source == "csv" and pipeline_data is not None:
        print("[INFO] CSV data already loaded. Skipping re-execution.")
        return True
    
    try:
        execution_status = {"status": "running", "message": "Executing agent pipeline..."}
        df = run_pipeline(verbose=False)
        if not df.empty:
            pipeline_data = df
            data_source = "csv"  # Mark as CSV
            last_execution_time = datetime.now()
            execution_status = {
                "status": "success",
                "message": f"Pipeline executed successfully at {last_execution_time.strftime('%Y-%m-%d %H:%M:%S')}"
            }
            return True
        else:
            execution_status = {"status": "error", "message": "Pipeline returned empty data"}
            return False
    except Exception as e:
        execution_status = {"status": "error", "message": f"Pipeline execution failed: {str(e)}"}
        print(f"[ERROR] Pipeline execution failed: {traceback.format_exc()}")
        return False



# Execute pipeline on startup - Waiting for Shopify data from n8n
@app.on_event("startup")
async def startup_event():
    print("[INFO] API started. Waiting for Shopify data from n8n...")
    print("[INFO] Trigger your n8n workflow to load Shopify products with LangChain insights!")



# API Endpoints
@app.get("/api/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "message": "API is running"
    }


@app.get("/api/agents/status")
async def get_agent_status():
    """Get status of all agents"""
    if pipeline_data is None:
        return {
            "status": execution_status["status"],
            "message": execution_status["message"],
            "agents": []
        }

    # Calculate agent-specific metrics
    profit_doctor_metrics = {
        "total_skus": len(pipeline_data),
        "profitable_skus": int((pipeline_data["profit_per_unit"] > 0).sum()),
        "loss_makers": int((pipeline_data["profit_per_unit"] < 0).sum()),
        "avg_profit": float(pipeline_data["profit_per_unit"].mean()),
        "total_daily_loss": float(pipeline_data["loss_per_day"].sum())
    }

    inventory_sentinel_metrics = {
        "critical_risk": int((pipeline_data["risk_level"] == "CRITICAL").sum()),
        "warning_risk": int((pipeline_data["risk_level"] == "WARNING").sum()),
        "safe": int((pipeline_data["risk_level"] == "SAFE").sum()),
        "no_history": int((pipeline_data["risk_level"] == "NO_HISTORY").sum()),
        "avg_velocity": float(pipeline_data["sales_velocity_per_day"].mean()),
        "total_reorder_qty": float(pipeline_data["reorder_qty_suggested"].sum())
    }

    action_counts = pipeline_data["recommended_action"].value_counts().to_dict()
    strategy_supervisor_metrics = {
        "total_actions": len(action_counts),
        "action_distribution": action_counts,
        "avg_impact_score": float(pipeline_data["impact_score"].mean())
    }

    # Seasonal Analyst metrics (check if columns exist)
    seasonal_analyst_metrics = {}
    if "seasonality_strength" in pipeline_data.columns:
        seasonal_analyst_metrics = {
            "strong_seasonality_count": int((pipeline_data["seasonality_strength"] > 0.3).sum()),
            "seasonal_risk_count": int(pipeline_data["seasonal_risk_flag"].sum()) if "seasonal_risk_flag" in pipeline_data.columns else 0,
            "avg_seasonality_strength": float(pipeline_data["seasonality_strength"].mean()),
            "rising_trend_count": int((pipeline_data["seasonal_trend"] == "RISING").sum()) if "seasonal_trend" in pipeline_data.columns else 0,
            "falling_trend_count": int((pipeline_data["seasonal_trend"] == "FALLING").sum()) if "seasonal_trend" in pipeline_data.columns else 0
        }

    agents = [
        {
            "name": "Profit Doctor",
            "status": "completed",
            "metrics": profit_doctor_metrics
        },
        {
            "name": "Inventory Sentinel",
            "status": "completed",
            "metrics": inventory_sentinel_metrics
        },
        {
            "name": "Seasonal Analyst",
            "status": "completed" if seasonal_analyst_metrics else "disabled",
            "metrics": seasonal_analyst_metrics
        },
        {
            "name": "Strategy Supervisor",
            "status": "completed",
            "metrics": strategy_supervisor_metrics
        }
    ]

    return {
        "status": execution_status["status"],
        "message": execution_status["message"],
        "last_execution": last_execution_time.isoformat() if last_execution_time else None,
        "agents": agents
    }


@app.post("/api/agents/run")
async def run_agents():
    """Trigger agent pipeline execution"""
    success = execute_pipeline()
    if success:
        return {
            "status": "success",
            "message": "Pipeline executed successfully",
            "timestamp": last_execution_time.isoformat() if last_execution_time else None
        }
    else:
        raise HTTPException(status_code=500, detail=execution_status["message"])


@app.get("/api/metrics/summary", response_model=MetricsSummary)
async def get_metrics_summary():
    """Get overall metrics summary"""
    if pipeline_data is None:
        raise HTTPException(status_code=404, detail="No pipeline data available. Run the pipeline first.")

    return {
        "total_skus": len(pipeline_data),
        "total_profitable": int((pipeline_data["profit_per_unit"] > 0).sum()),
        "total_loss_makers": int((pipeline_data["profit_per_unit"] < 0).sum()),
        "total_critical_risk": int((pipeline_data["risk_level"] == "CRITICAL").sum()),
        "total_warning_risk": int((pipeline_data["risk_level"] == "WARNING").sum()),
        "total_safe": int((pipeline_data["risk_level"] == "SAFE").sum()),
        "avg_profit_per_unit": float(pipeline_data["profit_per_unit"].mean()),
        "total_profit_at_risk": float(pipeline_data["profit_at_risk"].sum()),
        "total_daily_loss": float(pipeline_data["loss_per_day"].sum())
    }


@app.get("/api/recommendations", response_model=List[SKURecommendation])
async def get_recommendations():
    """Get all SKU recommendations"""
    if pipeline_data is None:
        raise HTTPException(status_code=404, detail="No pipeline data available. Run the pipeline first.")

    # Check which LLM columns exist in DataFrame
    llm_cols = {
        "llm_profit_insight", "llm_inventory_insight", "llm_strategy_insight",
        "llm_profit_confidence", "llm_inventory_confidence", "llm_strategy_confidence"
    }
    available_llm_cols = [col for col in llm_cols if col in pipeline_data.columns]
    
    # Convert DataFrame to list of dicts (including LLM insights)
    recommendations = []
    for _, row in pipeline_data.iterrows():
        rec = {
            "sku_id": row["sku_id"],
            "category": row["category"],
            "product_name": row["product_name"],
            "selling_price": float(row["selling_price"]),
            "cogs": float(row["cogs"]),
            "current_stock": int(row["current_stock"]),
            "lead_time_days": int(row["lead_time_days"]),
            "profit_per_unit": float(row["profit_per_unit"]),
            "loss_per_day": float(row["loss_per_day"]),
            "sales_velocity_per_day": float(row["sales_velocity_per_day"]),
            "days_of_stock_left": float(row["days_of_stock_left"]) if row["days_of_stock_left"] != float('inf') else 999999,
            "risk_level": row["risk_level"],
            "reorder_qty_suggested": float(row["reorder_qty_suggested"]),
            "profit_at_risk": float(row["profit_at_risk"]),
            "impact_score": float(row["impact_score"]),
            "recommended_action": row["recommended_action"]
        }
        
        # Add LLM insights if columns exist and have values
        for col in available_llm_cols:
            val = row[col]
            if pd.notna(val) and str(val).strip():
                if "confidence" in col:
                    rec[col] = float(val)
                else:
                    rec[col] = str(val)
        
        recommendations.append(rec)

    return recommendations


@app.get("/api/sku/{sku_id}")
async def get_sku_details(sku_id: str):
    """Get details for a specific SKU"""
    if pipeline_data is None:
        raise HTTPException(status_code=404, detail="No pipeline data available. Run the pipeline first.")

    sku_data = pipeline_data[pipeline_data["sku_id"] == sku_id]
    if sku_data.empty:
        raise HTTPException(status_code=404, detail=f"SKU {sku_id} not found")

    row = sku_data.iloc[0]
    return {
        "sku_id": row["sku_id"],
        "category": row["category"],
        "product_name": row["product_name"],
        "selling_price": float(row["selling_price"]),
        "cogs": float(row["cogs"]),
        "current_stock": int(row["current_stock"]),
        "lead_time_days": int(row["lead_time_days"]),
        "profit_per_unit": float(row["profit_per_unit"]),
        "loss_per_day": float(row["loss_per_day"]),
        "sales_velocity_per_day": float(row["sales_velocity_per_day"]),
        "days_of_stock_left": float(row["days_of_stock_left"]) if row["days_of_stock_left"] != float('inf') else 999999,
        "risk_level": row["risk_level"],
        "reorder_qty_suggested": float(row["reorder_qty_suggested"]),
        "profit_at_risk": float(row["profit_at_risk"]),
        "impact_score": float(row["impact_score"]),
        "recommended_action": row["recommended_action"]
    }


@app.get("/api/debug/columns")
async def debug_columns():
    """Debug endpoint to check what columns are in pipeline_data"""
    if pipeline_data is None:
        return {"error": "No pipeline data"}
    return {
        "columns": list(pipeline_data.columns),
        "llm_columns": [c for c in pipeline_data.columns if 'llm' in c.lower()],
        "first_row_llm_profit": str(pipeline_data.iloc[0].get("llm_profit_insight", "NOT FOUND")) if len(pipeline_data) > 0 else "NO DATA"
    }


# ============================================================================
# Seasonal Analysis Endpoints
# ============================================================================

@app.get("/api/seasonal/analysis")
async def get_seasonal_analysis():
    """
    Get seasonal analysis for all SKUs.
    Returns seasonal indices, trends, and risk flags.
    """
    if pipeline_data is None:
        raise HTTPException(status_code=404, detail="No pipeline data available. Run the pipeline first.")
    
    # Check if seasonal columns exist
    if "seasonality_strength" not in pipeline_data.columns:
        return {
            "status": "disabled",
            "message": "Seasonal analysis not available. Run pipeline with seasonal data.",
            "analysis": []
        }
    
    analysis = []
    for _, row in pipeline_data.iterrows():
        item = {
            "sku_id": row["sku_id"],
            "product_name": row["product_name"],
            "category": row["category"],
            "seasonal_index_current": float(row.get("seasonal_index_current", 1.0)),
            "seasonal_index_next": float(row.get("seasonal_index_next", 1.0)),
            "peak_month": row.get("peak_month", ""),
            "trough_month": row.get("trough_month", ""),
            "seasonal_trend": row.get("seasonal_trend", "STABLE"),
            "seasonality_strength": float(row.get("seasonality_strength", 0.0)),
            "seasonal_forecast": float(row.get("seasonal_forecast", 0.0)),
            "seasonal_risk_flag": bool(row.get("seasonal_risk_flag", False)),
            "llm_seasonal_insight": row.get("llm_seasonal_insight", "") if pd.notna(row.get("llm_seasonal_insight")) else ""
        }
        analysis.append(item)
    
    # Sort by seasonality strength (most seasonal first)
    analysis.sort(key=lambda x: x["seasonality_strength"], reverse=True)
    
    return {
        "status": "success",
        "total_skus": len(analysis),
        "strong_seasonality_count": sum(1 for a in analysis if a["seasonality_strength"] > 0.3),
        "seasonal_risk_count": sum(1 for a in analysis if a["seasonal_risk_flag"]),
        "analysis": analysis
    }


@app.get("/api/seasonal/risks")
async def get_seasonal_risks():
    """
    Get SKUs with seasonal risk flags.
    These are products with high stock entering low season.
    """
    if pipeline_data is None:
        raise HTTPException(status_code=404, detail="No pipeline data available.")
    
    if "seasonal_risk_flag" not in pipeline_data.columns:
        return {"risks": [], "message": "Seasonal analysis not available"}
    
    risk_items = pipeline_data[pipeline_data["seasonal_risk_flag"] == True]
    
    risks = []
    for _, row in risk_items.iterrows():
        risks.append({
            "sku_id": row["sku_id"],
            "product_name": row["product_name"],
            "current_stock": int(row["current_stock"]),
            "days_of_stock_left": float(row.get("days_of_stock_left", 0)),
            "seasonal_index_next": float(row.get("seasonal_index_next", 1.0)),
            "seasonal_trend": row.get("seasonal_trend", "STABLE"),
            "profit_per_unit": float(row.get("profit_per_unit", 0)),
            "recommendation": "Consider discount promotion before low season"
        })
    
    return {
        "total_risks": len(risks),
        "risks": risks
    }


@app.get("/api/seasonal/sku/{sku_id}")
async def get_sku_seasonal_details(sku_id: str):
    """
    Get detailed seasonal analysis for a specific SKU.
    """
    if pipeline_data is None:
        raise HTTPException(status_code=404, detail="No pipeline data available.")
    
    sku_data = pipeline_data[pipeline_data["sku_id"] == sku_id]
    if sku_data.empty:
        raise HTTPException(status_code=404, detail=f"SKU {sku_id} not found")
    
    row = sku_data.iloc[0]
    
    return {
        "sku_id": row["sku_id"],
        "product_name": row["product_name"],
        "category": row["category"],
        "seasonal_metrics": {
            "seasonal_index_current": float(row.get("seasonal_index_current", 1.0)),
            "seasonal_index_next": float(row.get("seasonal_index_next", 1.0)),
            "peak_month": row.get("peak_month", ""),
            "trough_month": row.get("trough_month", ""),
            "seasonal_trend": row.get("seasonal_trend", "STABLE"),
            "seasonality_strength": float(row.get("seasonality_strength", 0.0)),
            "seasonal_forecast": float(row.get("seasonal_forecast", 0.0)),
            "seasonal_risk_flag": bool(row.get("seasonal_risk_flag", False))
        },
        "inventory_metrics": {
            "current_stock": int(row["current_stock"]),
            "days_of_stock_left": float(row.get("days_of_stock_left", 0)),
            "sales_velocity_per_day": float(row.get("sales_velocity_per_day", 0))
        },
        "llm_seasonal_insight": row.get("llm_seasonal_insight", "") if pd.notna(row.get("llm_seasonal_insight")) else ""
    }

# ============================================================================
# n8n Integration Endpoints
# ============================================================================

class ShopifyData(BaseModel):
    """Model for Shopify data sent from n8n"""
    products: List[Dict[str, Any]]
    orders: Optional[List[Dict[str, Any]]] = None


class N8nActionLog(BaseModel):
    """Model for logging actions taken by n8n"""
    sku_id: str
    action_type: str
    risk_level: str
    notification_sent: bool
    timestamp: str
    approval_status: Optional[str] = None


class N8nWorkflowComplete(BaseModel):
    """Model for workflow completion notification"""
    workflow_id: str
    execution_id: str
    total_skus_processed: int
    timestamp: str
    status: str


# Global storage for n8n logs
n8n_action_logs: List[Dict[str, Any]] = []
n8n_workflow_history: List[Dict[str, Any]] = []


# ============================================================================
# User Action Models (for bidirectional communication)
# ============================================================================

class UserAction(BaseModel):
    """Model for user actions from email replies or dashboard"""
    sku_id: str
    action: str  # APPROVE_RESTOCK, CHANGE_PRICE, PAUSE_ADS, REJECT, etc.
    quantity: Optional[int] = None
    price: Optional[float] = None
    email_id: Optional[str] = None
    timestamp: str
    status: str = "pending"  # pending, executed, failed
    execution_details: Optional[Dict[str, Any]] = None


class InternalAction(BaseModel):
    """Model for internal actions triggered from dashboard"""
    sku_id: str
    action_type: str  # RESTOCK, PRICE_CHANGE, DISMISS
    value: Optional[float] = None  # New quantity or new price
    original_value: Optional[float] = None
    rationale: Optional[str] = None


# Global storage for user actions
pending_user_actions: List[Dict[str, Any]] = []
completed_user_actions: List[Dict[str, Any]] = []


@app.post("/api/n8n/analyze")
async def n8n_analyze_shopify_data(data: ShopifyData):
    """
    Endpoint for n8n to trigger agent analysis with Shopify data.
    
    This receives product and order data from Shopify via n8n,
    transforms it to agent format, and returns real recommendations.
    """
    global pipeline_data, last_execution_time, execution_status, data_source
    
    try:
        print(f"[INFO] n8n triggered analysis with {len(data.products)} products")
        
        # DEBUG: Print first product to verify input
        if data.products:
            print(f"[DEBUG] First product: {data.products[0].get('title', 'NO TITLE')}")
        
        execution_status = {"status": "running", "message": "n8n workflow triggered analysis..."}
        
        # ============================================================
        # TRANSFORM SHOPIFY DATA TO AGENT FORMAT
        # ============================================================
        
        # Create SKU master DataFrame from Shopify products
        sku_master_rows = []
        
        for product in data.products:
            # Extract product details
            product_id = product.get("id", "unknown")
            product_title = product.get("title", "Unknown Product")
            product_type = product.get("product_type", "General")
            vendor = product.get("vendor", "Unknown")
            
            # Get first variant (or iterate through all variants if needed)
            variants = product.get("variants", [])
            if not variants:
                print(f"[WARNING] Product {product_title} has no variants, skipping")
                continue
                
            variant = variants[0]
            
            # Extract pricing
            selling_price = float(variant.get("price", 0))
            
            # Estimate COGS (48% of selling price as default, adjust as needed)
            cogs = selling_price * 0.48
            
            # Extract inventory
            inventory_quantity = variant.get("inventory_quantity", 0)
            
            # Generate SKU from Shopify ID
            sku_id = f"SKU_{product_type.upper().replace(' ', '_')}_{product_id}"
            
            # Map Shopify product_type to your category system
            category_map = {
                "Shoes": "Footwear",
                "Apparel": "Fashion",
                "Electronics": "Electronics",
                "Beauty": "Beauty",
                "Home": "Home"
            }
            category = category_map.get(product_type, product_type)
            
            # Create row for SKU master
            sku_row = {
                "sku_id": sku_id,
                "category": category,
                "product_name": product_title,
                "selling_price": selling_price,
                "mrp": selling_price * 1.5,  # Estimate MRP as 1.5x selling price
                "cogs": cogs,
                "shipping_cost_per_unit": 75,  # Default shipping cost
                "platform_fee_percent": 2.0,
                "platform_fixed_fee": 3,
                "ad_spend_total_last_30_days": 5000,  # Default ad spend
                "units_sold_last_30_days": 150,  # Default sales (can be calculated from orders if provided)
                "current_stock": inventory_quantity,
                "lead_time_days": 12,  # Default lead time
                "is_hero": False,
                # Store Shopify IDs for write-back
                "shopify_variant_id": variant.get("id"),
                "shopify_inventory_item_id": variant.get("inventory_item_id")
            }
            
            sku_master_rows.append(sku_row)
        
        if not sku_master_rows:
            raise HTTPException(status_code=400, detail="No valid products to analyze")
        
        df_master = pd.DataFrame(sku_master_rows)
        print(f"[INFO] Created SKU master with {len(df_master)} products")
        
        # Create sample sales history (in production, use actual Shopify orders)
        # For now, generate synthetic sales based on units_sold_last_30_days
        sales_rows = []
        for _, sku in df_master.iterrows():
            # Generate 30 days of sales data
            daily_avg = sku["units_sold_last_30_days"] / 30
            for day in range(1, 31):
                # Add some randomness to daily sales
                import random
                daily_units = max(0, int(daily_avg * random.uniform(0.5, 1.5)))
                sales_rows.append({
                    "sku_id": sku["sku_id"],
                    "date": f"{day:02d}-11-2025",
                    "units_sold": daily_units
                })
        
        df_sales = pd.DataFrame(sales_rows)
        print(f"[INFO] Created sales history with {len(df_sales)} records")
        
        # ============================================================
        # RUN AGENT PIPELINE WITH SHOPIFY DATA
        # ============================================================
        
        # Run agents on transformed Shopify data
        from profit_doctor import ProfitDoctorAgent
        from inventory_sentinel import InventorySentinelAgent
        from strategy_supervisor import StrategySupervisorAgent
        
        # Agent 1: Profit Doctor
        profit_agent = ProfitDoctorAgent()
        df_profit = profit_agent.compute_profit_metrics(df_master)
        print(f"[INFO] Profit Doctor analyzed {len(df_profit)} SKUs")
        
        # Agent 2: Inventory Sentinel
        inventory_agent = InventorySentinelAgent()
        df_inventory = inventory_agent.compute_inventory_metrics(df_profit, df_sales)
        print(f"[INFO] Inventory Sentinel analyzed {len(df_inventory)} SKUs")
        
        # Agent 3: Strategy Supervisor
        strategy_agent = StrategySupervisorAgent()
        df_final = strategy_agent.rank_actions(df_inventory)
        print(f"[INFO] Strategy Supervisor ranked {len(df_final)} SKUs")
        
        # Update global pipeline data
        pipeline_data = df_final
        data_source = "shopify"  # Mark as Shopify data
        last_execution_time = datetime.now()
        execution_status = {
            "status": "success",
            "message": f"n8n analysis completed at {last_execution_time.strftime('%Y-%m-%d %H:%M:%S')}"
        }
        
        # Convert recommendations to JSON-serializable format
        recommendations = []
        for _, row in df_final.iterrows():
            recommendations.append({
                "sku_id": row["sku_id"],
                "category": row["category"],
                "product_name": row["product_name"],
                "selling_price": float(row["selling_price"]),
                "cogs": float(row["cogs"]),
                "current_stock": int(row["current_stock"]),
                "lead_time_days": int(row["lead_time_days"]),
                "profit_per_unit": float(row["profit_per_unit"]),
                "loss_per_day": float(row["loss_per_day"]),
                "sales_velocity_per_day": float(row["sales_velocity_per_day"]),
                "days_of_stock_left": float(row["days_of_stock_left"]) if row["days_of_stock_left"] != float('inf') else 999999,
                "risk_level": row["risk_level"],
                "reorder_qty_suggested": float(row["reorder_qty_suggested"]),
                "profit_at_risk": float(row["profit_at_risk"]),
                "impact_score": float(row["impact_score"]),
                "recommended_action": row["recommended_action"]
            })
        
        return {
            "status": "success",
            "message": "Agent analysis completed with Shopify data",
            "timestamp": last_execution_time.isoformat(),
            "total_skus": len(recommendations),
            "recommendations": recommendations,
            "summary": {
                "critical_risk": int((df_final["risk_level"] == "CRITICAL").sum()),
                "warning_risk": int((df_final["risk_level"] == "WARNING").sum()),
                "profitable_skus": int((df_final["profit_per_unit"] > 0).sum()),
                "loss_makers": int((df_final["profit_per_unit"] < 0).sum())
            }
        }
            
    except Exception as e:
        execution_status = {"status": "error", "message": f"n8n analysis failed: {str(e)}"}
        print(f"[ERROR] n8n analysis failed: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/n8n/log-action")
async def n8n_log_action(log: N8nActionLog):
    """
    Endpoint for n8n to log actions taken (alerts, approvals, executions).
    
    This creates an audit trail of all n8n workflow actions.
    """
    try:
        log_entry = {
            "sku_id": log.sku_id,
            "action_type": log.action_type,
            "risk_level": log.risk_level,
            "notification_sent": log.notification_sent,
            "timestamp": log.timestamp,
            "approval_status": log.approval_status,
            "logged_at": datetime.now().isoformat()
        }
        
        n8n_action_logs.append(log_entry)
        
        print(f"[INFO] n8n action logged: {log.sku_id} - {log.action_type}")
        
        return {
            "status": "success",
            "message": "Action logged successfully",
            "log_id": len(n8n_action_logs) - 1
        }
        
    except Exception as e:
        print(f"[ERROR] Failed to log n8n action: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/n8n/workflow-complete")
async def n8n_workflow_complete(workflow: N8nWorkflowComplete):
    """
    Endpoint for n8n to notify when workflow completes.
    
    This tracks workflow execution history and completion status.
    """
    try:
        workflow_entry = {
            "workflow_id": workflow.workflow_id,
            "execution_id": workflow.execution_id,
            "total_skus_processed": workflow.total_skus_processed,
            "timestamp": workflow.timestamp,
            "status": workflow.status,
            "completed_at": datetime.now().isoformat()
        }
        
        n8n_workflow_history.append(workflow_entry)
        
        print(f"[INFO] n8n workflow completed: {workflow.execution_id} - {workflow.total_skus_processed} SKUs")
        
        return {
            "status": "success",
            "message": "Workflow completion recorded",
            "workflow_history_id": len(n8n_workflow_history) - 1
        }
        
    except Exception as e:
        print(f"[ERROR] Failed to record workflow completion: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/n8n/logs")
async def get_n8n_logs(limit: int = 50):
    """Get recent n8n action logs"""
    return {
        "total_logs": len(n8n_action_logs),
        "logs": n8n_action_logs[-limit:]
    }


@app.get("/api/n8n/workflow-history")
async def get_n8n_workflow_history(limit: int = 20):
    """Get n8n workflow execution history"""
    return {
        "total_executions": len(n8n_workflow_history),
        "history": n8n_workflow_history[-limit:]
    }


# ============================================================================
# User Action Endpoints (Bidirectional Communication)
# ============================================================================

@app.post("/api/n8n/user-action")
async def receive_user_action(action: UserAction):
    """
    Endpoint for n8n to send user actions (from email replies).
    
    This receives user responses from email and logs them for tracking.
    The action execution (Shopify updates) happens in n8n workflow.
    """
    try:
        action_entry = {
            "sku_id": action.sku_id,
            "action": action.action,
            "quantity": action.quantity,
            "price": action.price,
            "email_id": action.email_id,
            "timestamp": action.timestamp,
            "status": action.status,
            "execution_details": action.execution_details,
            "received_at": datetime.now().isoformat()
        }
        
        # Add to appropriate list based on status
        if action.status == "pending":
            pending_user_actions.append(action_entry)
        elif action.status in ["executed", "completed", "success"]:
            completed_user_actions.append(action_entry)
            # Remove from pending if it was there
            pending_user_actions[:] = [a for a in pending_user_actions if a["sku_id"] != action.sku_id or a["action"] != action.action]
        
        print(f"[INFO] User action received: {action.sku_id} - {action.action} ({action.status})")
        
        return {
            "status": "success",
            "message": "User action received and logged",
            "action_id": len(completed_user_actions + pending_user_actions) - 1
        }
        
    except Exception as e:
        print(f"[ERROR] Failed to log user action: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/user-actions/pending")
async def get_pending_actions():
    """Get all pending user actions (awaiting execution)"""
    return {
        "total_pending": len(pending_user_actions),
        "actions": pending_user_actions
    }


@app.get("/api/user-actions/completed")
async def get_completed_actions(limit: int = 50):
    """Get recent completed user actions"""
    return {
        "total_completed": len(completed_user_actions),
        "actions": completed_user_actions[-limit:]
    }


@app.get("/api/user-actions/history")
async def get_action_history(sku_id: Optional[str] = None, limit: int = 100):
    """
    Get action history, optionally filtered by SKU.
    Returns both pending and completed actions.
    """
    all_actions = pending_user_actions + completed_user_actions
    
    if sku_id:
        filtered = [a for a in all_actions if a["sku_id"] == sku_id]
        all_actions = filtered
    
    # Sort by timestamp (most recent first)
    all_actions = sorted(all_actions, key=lambda x: x.get("received_at", ""), reverse=True)
    
    return {
        "total_actions": len(all_actions),
        "sku_filter": sku_id,
        "actions": all_actions[:limit]
    }


@app.patch("/api/user-actions/{action_index}/status")
async def update_action_status(action_index: int, status: str, execution_details: Optional[Dict[str, Any]] = None):
    """
    Update the status of a user action (called by n8n after execution).
    
    Args:
        action_index: Index of the action in pending_user_actions
        status: New status (executed, failed, etc.)
        execution_details: Details about the execution
    """
    try:
        if action_index < 0 or action_index >= len(pending_user_actions):
            raise HTTPException(status_code=404, detail="Action not found")
        
        action = pending_user_actions[action_index]
        action["status"] = status
        action["execution_details"] = execution_details
        action ["updated_at"] = datetime.now().isoformat()
        
        # Move to completed if status is final
        if status in ["executed", "completed", "success", "failed", "rejected"]:
            completed_user_actions.append(action)
            pending_user_actions.pop(action_index)
        
        print(f"[INFO] Action status updated: {action['sku_id']} - {status}")
        
        return {
            "status": "success",
            "message": "Action status updated",
            "action": action
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"[ERROR] Failed to update action status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/alerts")
async def get_alerts():
    """
    Get actionable alerts from current recommendations.
    Filters for CRITICAL or WARNING items unless already acted upon.
    """
    if pipeline_data is None:
        return {"alerts": []}
        
    alerts = []
    
    # Filter for actionable items
    actionable = pipeline_data[
        (pipeline_data["risk_level"].isin(["CRITICAL", "WARNING"])) |
        (pipeline_data["is_loss_maker"] == True)
    ]
    
    # Exclude already acted upon SKUs (simple in-memory check for this session)
    acted_skus = {a["sku_id"] for a in completed_user_actions if a["status"] == "executed"}
    # Also exclude dismissed
    dismissed_skus = {a["sku_id"] for a in completed_user_actions if a.get("action") == "DISMISS"}
    
    exclude_skus = acted_skus.union(dismissed_skus)
    
    for _, row in actionable.iterrows():
        if row["sku_id"] in exclude_skus:
            continue
            
        alerts.append({
            "sku_id": row["sku_id"],
            "product_name": row["product_name"],
            "risk_level": row["risk_level"],
            "recommended_action": row["recommended_action"],
            "current_stock": int(row["current_stock"]),
            "selling_price": float(row["selling_price"]),
            "profit_per_unit": float(row["profit_per_unit"]),
            "impact_score": float(row["impact_score"]),
            # Include suggested values
            "suggested_reorder": float(row["reorder_qty_suggested"]) if row["reorder_qty_suggested"] > 0 else 50,
            "suggested_price": float(row["selling_price"]) * 1.1 if "PRICE" in row["recommended_action"] else None
        })
        
    # Sort by impact
    alerts.sort(key=lambda x: x["impact_score"], reverse=True)
    return alerts



def update_csv_source(sku_id: str, action_type: str, value: float):
    """
    Update the master CSV file to persist changes locally.
    """
    try:
        master_path = CFG.sku_master_path
        if not os.path.exists(master_path):
            print(f"[WARNING] Master CSV not found at {master_path}")
            return

        df_master = pd.read_csv(master_path)
        mask = df_master["sku_id"] == sku_id
        
        if mask.any():
            if action_type == "RESTOCK":
                current = df_master.loc[mask, "current_stock"].values[0]
                df_master.loc[mask, "current_stock"] = current + (value or 0)
            elif action_type == "PRICE_CHANGE":
                df_master.loc[mask, "selling_price"] = value
                
            df_master.to_csv(master_path, index=False)
            print(f"[SUCCESS] Updated {sku_id} in {master_path}")
        else:
            print(f"[WARNING] SKU {sku_id} not found in master CSV")
            
    except Exception as e:
        print(f"[ERROR] Error updating CSV: {str(e)}")
        raise


@app.post("/api/alerts/action")
async def execute_alert_action(action: InternalAction):
    """
    Execute an action from the Alerts tab.
    Mock update for now, but logs the action as if sent to Shopify.
    """
    global pipeline_data
    
    try:
        # Log the action
        action_entry = {
            "sku_id": action.sku_id,
            "action": action.action_type,
            "value": action.value,
            "timestamp": datetime.now().isoformat(),
            "status": "executed",
            "source": "dashboard_alerts"
        }
        completed_user_actions.append(action_entry)
        
        # MOCK UPDATE: Update the local pipeline_data to reflect change
        if pipeline_data is not None and not pipeline_data.empty:
            if action.action_type == "RESTOCK":
                # Update stock
                mask = pipeline_data["sku_id"] == action.sku_id
                if mask.any():
                    current = pipeline_data.loc[mask, "current_stock"].values[0]
                    new_stock = current + (action.value or 0)
                    pipeline_data.loc[mask, "current_stock"] = new_stock
                    # Recalculate risk (simplified)
                    pipeline_data.loc[mask, "risk_level"] = "SAFE" 
                    pipeline_data.loc[mask, "recommended_action"] = "MONITOR"
                    print(f"[INFO] Mock update: Restocked {action.sku_id} to {new_stock}")
                    
            elif action.action_type == "PRICE_CHANGE":
                # Update price
                mask = pipeline_data["sku_id"] == action.sku_id
                if mask.any():
                    pipeline_data.loc[mask, "selling_price"] = action.value
                    # Recalculate profit (simplified)
                    pipeline_data.loc[mask, "profit_per_unit"] += (action.value - (action.original_value or action.value)) # Approximate
                    pipeline_data.loc[mask, "recommended_action"] = "MONITOR"
                    print(f"[INFO] Mock update: Repriced {action.sku_id} to {action.value}")

        # PERSIST UPDATE: Update the source (CSV or Shopify)
        try:
            if data_source == "shopify" and CFG.shopify_access_token:
                loader = ShopifyLoader()
                # Find IDs from dataframe
                mask = pipeline_data["sku_id"] == action.sku_id
                if mask.any():
                    row = pipeline_data.loc[mask].iloc[0]
                    # Check if we have variant ID mapped (ShopifyLoader adds it)
                    if "shopify_variant_id" in row:
                        variant_id = int(row["shopify_variant_id"])
                        inv_id = int(row["shopify_inventory_item_id"])
                        
                        if action.action_type == "RESTOCK":
                            # We need new TOTAL qty, not just add
                            current = int(row["current_stock"]) # This is already updated in memory above
                            # But wait, above updated pipeline_data. So 'row' has NEW stock.
                            loader.update_stock(variant_id, inv_id, current)
                        elif action.action_type == "PRICE_CHANGE":
                             loader.update_price(variant_id, action.value)
                        
                        print(f"[INFO] Shopify updated for {action.sku_id}")
            
            elif data_source != "shopify":
                update_csv_source(action.sku_id, action.action_type, action.value)
                print(f"[INFO] Source CSV updated for {action.sku_id}")
                
        except Exception as e:
            print(f"[ERROR] Failed to persist update: {str(e)}")

        return {
            "status": "success", 
            "message": f"Action {action.action_type} executed for {action.sku_id}",
            "updated_value": action.value
        }
        
    except Exception as e:
        print(f"[ERROR] Failed to execute alert action: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# End n8n Integration Endpoints
# ============================================================================



if __name__ == "__main__":
    import uvicorn
    print("[INFO] Starting FastAPI server...")
    print("[INFO] API docs available at http://localhost:8000/docs")
    print("[INFO] Dashboard should connect to http://localhost:8000/api")
    print("[INFO] n8n endpoints available at http://localhost:8000/api/n8n/*")
    uvicorn.run(app, host="0.0.0.0", port=8000)
