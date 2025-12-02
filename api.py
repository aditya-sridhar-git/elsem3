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


# Helper function to execute pipeline
def execute_pipeline():
    global pipeline_data, last_execution_time, execution_status
    try:
        execution_status = {"status": "running", "message": "Executing agent pipeline..."}
        df = run_pipeline(verbose=False)
        if not df.empty:
            pipeline_data = df
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


# Execute pipeline on startup
@app.on_event("startup")
async def startup_event():
    print("[INFO] Executing pipeline on startup...")
    execute_pipeline()


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

    # Convert DataFrame to list of dicts
    recommendations = []
    for _, row in pipeline_data.iterrows():
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


if __name__ == "__main__":
    import uvicorn
    print("[INFO] Starting FastAPI server...")
    print("[INFO] API docs available at http://localhost:8000/docs")
    print("[INFO] Dashboard should connect to http://localhost:8000/api")
    uvicorn.run(app, host="0.0.0.0", port=8000)
