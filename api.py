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
from pipeline import run_pipeline

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
def execute_pipeline():
    global pipeline_data, last_execution_time, execution_status, data_source
    
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
    # execute_pipeline()  # Disabled - waiting for Shopify via n8n


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
                "is_hero": False
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
