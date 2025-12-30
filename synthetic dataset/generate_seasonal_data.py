"""
Generate seasonal sales history for e-commerce products.
Creates 365 days of sales data with realistic seasonal patterns for Indian market.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os

# Set random seed for reproducibility
np.random.seed(42)

# Define SKUs and their base daily demand
SKUS = {
    "SKU_ELEC_001": {"category": "Electronics", "base_demand": 6, "seasonality": "festival_high"},
    "SKU_ELEC_002": {"category": "Electronics", "base_demand": 4, "seasonality": "festival_high"},
    "SKU_ELEC_003": {"category": "Electronics", "base_demand": 3, "seasonality": "summer_high"},
    "SKU_ELEC_004": {"category": "Electronics", "base_demand": 8, "seasonality": "stable"},
    "SKU_FASH_001": {"category": "Fashion", "base_demand": 5, "seasonality": "summer_high"},
    "SKU_FASH_002": {"category": "Fashion", "base_demand": 3, "seasonality": "festival_high"},
    "SKU_FASH_003": {"category": "Fashion", "base_demand": 3, "seasonality": "stable"},
    "SKU_FASH_004": {"category": "Fashion", "base_demand": 2, "seasonality": "winter_high"},
    "SKU_HOME_001": {"category": "Home", "base_demand": 4, "seasonality": "summer_high"},
    "SKU_HOME_002": {"category": "Home", "base_demand": 2, "seasonality": "stable"},
    "SKU_HOME_003": {"category": "Home", "base_demand": 2, "seasonality": "winter_high"},
    "SKU_HOME_004": {"category": "Home", "base_demand": 1.5, "seasonality": "winter_high"},
    "SKU_BEAUTY_001": {"category": "Beauty", "base_demand": 5, "seasonality": "summer_high"},
    "SKU_BEAUTY_002": {"category": "Beauty", "base_demand": 4, "seasonality": "monsoon_high"},
    "SKU_BEAUTY_003": {"category": "Beauty", "base_demand": 5, "seasonality": "summer_high"},
    "SKU_BEAUTY_004": {"category": "Beauty", "base_demand": 2.5, "seasonality": "festival_high"},
    "SKU_SPORTS_001": {"category": "Sports", "base_demand": 3, "seasonality": "newyear_high"},
    "SKU_SPORTS_002": {"category": "Sports", "base_demand": 4, "seasonality": "newyear_high"},
    "SKU_SPORTS_003": {"category": "Sports", "base_demand": 1.3, "seasonality": "ipl_high"},
    "SKU_SPORTS_004": {"category": "Sports", "base_demand": 2, "seasonality": "stable"},
}

def get_seasonal_multiplier(date, seasonality_type):
    """
    Get seasonal multiplier based on date and product seasonality type.
    Indian market-specific seasonality patterns.
    """
    month = date.month
    day = date.day
    
    # Base multiplier
    multiplier = 1.0
    
    # Diwali period (Oct 15 - Nov 15) - Major festival
    if (month == 10 and day >= 15) or (month == 11 and day <= 15):
        if seasonality_type == "festival_high":
            multiplier = 1.8  # +80%
        elif seasonality_type in ["winter_high", "stable"]:
            multiplier = 1.4  # +40%
        else:
            multiplier = 1.2  # +20%
    
    # Christmas/New Year (Dec 15 - Jan 10)
    elif (month == 12 and day >= 15) or (month == 1 and day <= 10):
        if seasonality_type == "newyear_high":
            multiplier = 1.6  # +60%
        elif seasonality_type == "festival_high":
            multiplier = 1.3  # +30%
        else:
            multiplier = 1.15
    
    # Summer season (Apr - Jun)
    elif month in [4, 5, 6]:
        if seasonality_type == "summer_high":
            if month == 5:  # Peak summer
                multiplier = 1.5  # +50%
            else:
                multiplier = 1.3  # +30%
        elif seasonality_type == "winter_high":
            multiplier = 0.6  # -40%
        else:
            multiplier = 1.0
    
    # Monsoon season (Jul - Sep)
    elif month in [7, 8, 9]:
        if seasonality_type == "monsoon_high":
            multiplier = 1.4  # +40%
        elif seasonality_type == "summer_high":
            multiplier = 0.8  # -20%
        else:
            multiplier = 0.9  # -10%
    
    # Winter season (Nov 16 - Feb)
    elif month in [11, 12, 1, 2] and not ((month == 11 and day <= 15)):
        if seasonality_type == "winter_high":
            multiplier = 1.5
        elif seasonality_type == "summer_high":
            multiplier = 0.7
        else:
            multiplier = 1.0
    
    # IPL Season (Apr - May)
    if month in [4, 5] and seasonality_type == "ipl_high":
        multiplier = max(multiplier, 1.7)  # +70%
    
    # Republic Day Sale (Jan 20-26)
    if month == 1 and 20 <= day <= 26:
        multiplier *= 1.3
    
    # Independence Day Sale (Aug 10-15)
    if month == 8 and 10 <= day <= 15:
        multiplier *= 1.25
    
    return multiplier

def get_weekly_multiplier(date):
    """Weekend effect - higher sales on Sat/Sun"""
    weekday = date.weekday()
    if weekday == 5:  # Saturday
        return 1.25
    elif weekday == 6:  # Sunday
        return 1.15
    elif weekday == 0:  # Monday (hangover from weekend browsing)
        return 1.05
    else:
        return 1.0

def generate_seasonal_sales():
    """Generate 365 days of seasonal sales data"""
    
    # Start from 365 days ago
    end_date = datetime(2024, 12, 28)  # Current date in the simulation
    start_date = end_date - timedelta(days=364)
    
    sales_records = []
    
    current_date = start_date
    while current_date <= end_date:
        for sku_id, sku_info in SKUS.items():
            base_demand = sku_info["base_demand"]
            seasonality = sku_info["seasonality"]
            
            # Get multipliers
            seasonal_mult = get_seasonal_multiplier(current_date, seasonality)
            weekly_mult = get_weekly_multiplier(current_date)
            
            # Add random noise (±20%)
            noise = np.random.uniform(0.8, 1.2)
            
            # Calculate final demand
            demand = base_demand * seasonal_mult * weekly_mult * noise
            units_sold = max(0, int(round(demand)))
            
            # Add some zero-sale days randomly (5% chance)
            if np.random.random() < 0.05:
                units_sold = 0
            
            sales_records.append({
                "sku_id": sku_id,
                "date": current_date.strftime("%Y-%m-%d"),
                "units_sold": units_sold,
                "month": current_date.month,
                "day_of_week": current_date.strftime("%A"),
                "is_weekend": 1 if current_date.weekday() >= 5 else 0
            })
        
        current_date += timedelta(days=1)
    
    return pd.DataFrame(sales_records)

def main():
    print("[INFO] Generating seasonal sales history...")
    
    df = generate_seasonal_sales()
    
    # Save to CSV
    output_path = os.path.join(os.path.dirname(__file__), "seasonal_sales_history.csv")
    df.to_csv(output_path, index=False)
    
    print(f"[SUCCESS] Generated {len(df)} sales records")
    print(f"[INFO] Date range: {df['date'].min()} to {df['date'].max()}")
    print(f"[INFO] SKUs: {df['sku_id'].nunique()}")
    print(f"[INFO] Saved to: {output_path}")
    
    # Print sample statistics
    print("\n[INFO] Sample seasonal patterns:")
    monthly_sales = df.groupby(['sku_id', 'month'])['units_sold'].sum().reset_index()
    for sku in ["SKU_ELEC_001", "SKU_FASH_004", "SKU_BEAUTY_001"]:
        sku_monthly = monthly_sales[monthly_sales['sku_id'] == sku]
        peak_month = sku_monthly.loc[sku_monthly['units_sold'].idxmax(), 'month']
        trough_month = sku_monthly.loc[sku_monthly['units_sold'].idxmin(), 'month']
        print(f"  {sku}: Peak Month={peak_month}, Trough Month={trough_month}")
    
    return df

if __name__ == "__main__":
    main()
