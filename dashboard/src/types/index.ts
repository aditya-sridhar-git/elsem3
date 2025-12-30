// TypeScript interfaces for API responses

export interface AgentMetrics {
    [key: string]: any;
}

export interface Agent {
    name: string;
    status: string;
    execution_time?: number;
    metrics: AgentMetrics;
}

export interface AgentStatusResponse {
    status: string;
    message: string;
    last_execution?: string;
    agents: Agent[];
}

export interface MetricsSummary {
    total_skus: number;
    total_profitable: number;
    total_loss_makers: number;
    total_critical_risk: number;
    total_warning_risk: number;
    total_safe: number;
    avg_profit_per_unit: number;
    total_profit_at_risk: number;
    total_daily_loss: number;
}

export interface SKURecommendation {
    sku_id: string;
    category: string;
    product_name: string;
    selling_price: number;
    cogs: number;
    current_stock: number;
    lead_time_days: number;
    profit_per_unit: number;
    loss_per_day: number;
    sales_velocity_per_day: number;
    days_of_stock_left: number;
    risk_level: string;
    reorder_qty_suggested: number;
    profit_at_risk: number;
    impact_score: number;
    recommended_action: string;
    // LangChain LLM insights (optional)
    llm_profit_insight?: string;
    llm_inventory_insight?: string;
    llm_strategy_insight?: string;
    llm_confidence?: number;
    llm_profit_confidence?: number;
    llm_inventory_confidence?: number;
    llm_strategy_confidence?: number;
}

export interface Alert {
    sku_id: string;
    product_name: string;
    risk_level: string;
    recommended_action: string;
    current_stock: number;
    selling_price: number;
    profit_per_unit: number;
    impact_score: number;
    suggested_reorder?: number;
    suggested_price?: number;
}

// Seasonal Analysis Types
export interface SeasonalAnalysis {
    sku_id: string;
    product_name: string;
    category: string;
    seasonal_index_current: number;
    seasonal_index_next: number;
    peak_month: string;
    trough_month: string;
    seasonal_trend: string;
    seasonality_strength: number;
    seasonal_forecast: number;
    seasonal_risk_flag: boolean;
    llm_seasonal_insight?: string;
}

export interface SeasonalResponse {
    status: string;
    total_skus: number;
    strong_seasonality_count: number;
    seasonal_risk_count: number;
    analysis: SeasonalAnalysis[];
}

// Ad Gateway Types
export interface AdCampaign {
    campaign_id: string;
    campaign_name: string;
    platform: string;
    status: string;
    daily_budget: number;
    total_spend_30d: number;
    roas: number;
    impressions: number;
    clicks: number;
    conversions: number;
    ctr: number;
    cpc: number;
    sku_id?: string;
}

export interface AdMetricsSummary {
    total_campaigns: number;
    active_campaigns: number;
    paused_campaigns: number;
    total_spend_30d: number;
    avg_roas: number;
    platforms: Record<string, boolean>;
}

export interface AdPlatformCredentials {
    platform: string;
    api_key: string;
    account_id: string;
    client_secret?: string;
}

