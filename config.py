# config.py

from dataclasses import dataclass

# Optional ARIMA support
try:
    from statsmodels.tsa.arima.model import ARIMA  # type: ignore
    HAS_ARIMA = True
except ImportError:
    ARIMA = None
    HAS_ARIMA = False
    print("[WARN] statsmodels not installed. ARIMA will be skipped; WMA will be used instead.")


@dataclass
class Config:
    # Input data paths - UPDATED to match local files
    sku_master_path: str = "sku_master.csv"
    sales_history_path: str = "sales_history.csv"

    # Financial / business parameters
    fee_gst_rate: float = 0.18        # GST on payment gateway fees
    min_arima_history_days: int = 30  # minimum days of history to use ARIMA
    forecast_horizon_days: int = 7
    wma_window_days: int = 7
    lead_time_buffer_days: int = 5
    demand_uncertainty_factor: float = 1.3
    min_velocity_for_risk: float = 0.1
    loss_per_day_threshold: float = 200.0
    min_days_for_urgency: float = 1.0


CFG = Config()
