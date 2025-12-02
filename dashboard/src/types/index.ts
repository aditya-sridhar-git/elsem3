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
}
