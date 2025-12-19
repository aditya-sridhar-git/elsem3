# config.py - Updated with LangChain support

import os
from dataclasses import dataclass
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

@dataclass
class Config:
    """Configuration for E-commerce Agent Dashboard"""
    
    # Data paths
    sku_master_path: str = "sku_master.csv"
    sales_history_path: str = "sales_history.csv"
    
    # Agent parameters
    fee_gst_rate: float = 0.18
    min_arima_history_days: int = 30
    forecast_horizon_days: int = 14
    wma_window_days: int = 7
    lead_time_buffer_days: int = 5
    demand_uncertainty_factor: float = 1.5
    min_velocity_for_risk: float = 0.01
    loss_per_day_threshold: float = 100.0
    min_days_for_urgency: float = 1.0
    
    # LangChain Configuration
    enable_langchain: bool = os.getenv("ENABLE_LANGCHAIN", "False").lower() == "true"
    groq_api_key: str = os.getenv("GROQ_API_KEY", "")
    llm_model: str = os.getenv("LLM_MODEL", "llama-3.3-70b-versatile")
    llm_temperature: float = float(os.getenv("LLM_TEMPERATURE", "0.1"))
    llm_max_retries: int = int(os.getenv("LLM_MAX_RETRIES", "3"))
    llm_delay: float = float(os.getenv("LLM_DELAY", "3.0"))  # Seconds between calls
    max_tokens: int = int(os.getenv("MAX_TOKENS", "1000"))
    
    # Agent-specific LLM toggles
    enable_profit_doctor_llm: bool = os.getenv("ENABLE_PROFIT_DOCTOR_LLM", "True").lower() == "true"
    enable_inventory_sentinel_llm: bool = os.getenv("ENABLE_INVENTORY_SENTINEL_LLM", "True").lower() == "true"
    enable_strategy_supervisor_llm: bool = os.getenv("ENABLE_STRATEGY_SUPERVISOR_LLM", "True").lower() == "true"
    
    # Performance settings
    batch_size: int = int(os.getenv("BATCH_SIZE", "5"))
    enable_caching: bool = os.getenv("ENABLE_CACHING", "True").lower() == "true"
    cache_ttl: int = int(os.getenv("CACHE_TTL", "3600"))

    # Shopify Configuration
    shopify_access_token: str = os.getenv("SHOPIFY_ACCESS_TOKEN", "")
    shopify_api_key: str = os.getenv("SHOPIFY_API_KEY", "")
    shopify_api_secret: str = os.getenv("SHOPIFY_API_SECRET", "")
    shopify_shop_domain: str = os.getenv("SHOPIFY_SHOP_DOMAIN", "")

CFG = Config()

# ARIMA configuration
try:
    from statsmodels.tsa.arima.model import ARIMA
    HAS_ARIMA = True
except ImportError:
    ARIMA = None
    HAS_ARIMA = False
    print("[WARNING] statsmodels not installed. ARIMA forecasting disabled.")

# LangChain initialization
if CFG.enable_langchain and CFG.groq_api_key:
    try:
        from langchain_groq import ChatGroq
        
        # Initialize Groq LLM
        llm = ChatGroq(
            groq_api_key=CFG.groq_api_key,
            model_name=CFG.llm_model,
            temperature=CFG.llm_temperature,
            max_tokens=CFG.max_tokens
        )
        HAS_LANGCHAIN = True
        print(f"[INFO] LangChain enabled with Groq ({CFG.llm_model})")
    except ImportError:
        llm = None
        HAS_LANGCHAIN = False
        print("[WARNING] LangChain/Groq not installed. LLM features disabled.")
    except Exception as e:
        llm = None
        HAS_LANGCHAIN = False
        print(f"[ERROR] Failed to initialize LangChain: {str(e)}")
else:
    llm = None
    HAS_LANGCHAIN = False
    if CFG.enable_langchain:
        print("[WARNING] LangChain enabled but no GROQ_API_KEY found.")
