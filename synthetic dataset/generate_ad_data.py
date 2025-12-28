"""
Generate synthetic ad campaign data for e-commerce products.
Creates realistic ad metrics across Google Ads, Meta Ads, and Amazon Ads.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os
import random

# Set random seed for reproducibility
np.random.seed(42)

# Load SKU master to create campaigns for each product
SKU_MASTER_PATH = "sku_master.csv"

# Platform configurations
PLATFORMS = {
    "GOOGLE_ADS": {
        "base_cpc": 8.0,  # Base cost per click in INR
        "ctr_range": (0.02, 0.08),  # CTR 2-8%
        "conv_rate_range": (0.02, 0.06),  # Conversion rate 2-6%
    },
    "META_ADS": {
        "base_cpc": 5.0,
        "ctr_range": (0.01, 0.05),  # CTR 1-5%
        "conv_rate_range": (0.01, 0.04),  # Conversion rate 1-4%
    },
    "AMAZON_ADS": {
        "base_cpc": 12.0,
        "ctr_range": (0.03, 0.10),  # CTR 3-10% (higher intent)
        "conv_rate_range": (0.05, 0.12),  # Higher conversion (product pages)
    }
}

# Campaign name templates
CAMPAIGN_TEMPLATES = {
    "GOOGLE_ADS": ["Search_{product}", "Display_{product}", "Shopping_{product}"],
    "META_ADS": ["FB_{product}_Awareness", "IG_{product}_Retarget", "FB_{product}_Lookalike"],
    "AMAZON_ADS": ["SP_{product}", "SB_{product}_Brand", "SD_{product}_Retarget"]
}


def generate_campaign_id():
    """Generate unique campaign ID"""
    return f"CAM_{random.randint(10000, 99999)}"


def calculate_roas(revenue, spend):
    """Calculate Return on Ad Spend"""
    if spend == 0:
        return 0.0
    return round(revenue / spend, 2)


def generate_campaigns(df_master):
    """Generate ad campaigns for each SKU"""
    campaigns = []
    
    for _, sku in df_master.iterrows():
        sku_id = sku["sku_id"]
        product_name = sku["product_name"].replace(" ", "_")[:20]
        selling_price = sku["selling_price"]
        units_sold_30d = sku.get("units_sold_last_30_days", 100)
        
        # Randomly assign 1-3 platforms per SKU
        num_platforms = random.choice([1, 2, 2, 3])  # Weighted towards 2
        selected_platforms = random.sample(list(PLATFORMS.keys()), num_platforms)
        
        for platform in selected_platforms:
            config = PLATFORMS[platform]
            
            # Generate campaign metrics
            ctr = random.uniform(*config["ctr_range"])
            conv_rate = random.uniform(*config["conv_rate_range"])
            cpc = config["base_cpc"] * random.uniform(0.7, 1.5)
            
            # Calculate impressions, clicks, conversions
            # Work backwards from units sold to estimate ad contribution
            ad_attributed_sales = int(units_sold_30d * random.uniform(0.3, 0.7))
            conversions = max(1, ad_attributed_sales)
            clicks = max(conversions, int(conversions / conv_rate))
            impressions = max(clicks, int(clicks / ctr))
            
            # Calculate spend and revenue
            total_spend = clicks * cpc
            revenue = conversions * selling_price
            roas = calculate_roas(revenue, total_spend)
            
            # Daily budget (slightly higher than avg daily spend)
            daily_budget = round((total_spend / 30) * random.uniform(1.1, 1.3), 2)
            
            # Campaign status
            status = random.choices(
                ["ACTIVE", "PAUSED", "ACTIVE", "ACTIVE"],  # 75% active
                k=1
            )[0]
            
            # Dates
            start_date = datetime.now() - timedelta(days=random.randint(30, 180))
            end_date = None if status != "ENDED" else datetime.now() - timedelta(days=random.randint(1, 30))
            
            # Pick campaign name template
            template = random.choice(CAMPAIGN_TEMPLATES[platform])
            campaign_name = template.format(product=product_name)
            
            campaigns.append({
                "campaign_id": generate_campaign_id(),
                "sku_id": sku_id,
                "platform": platform,
                "campaign_name": campaign_name,
                "status": status,
                "daily_budget": daily_budget,
                "total_spend_30d": round(total_spend, 2),
                "impressions_30d": impressions,
                "clicks_30d": clicks,
                "conversions_30d": conversions,
                "cpc": round(cpc, 2),
                "ctr": round(ctr * 100, 2),  # Store as percentage
                "conversion_rate": round(conv_rate * 100, 2),  # Store as percentage
                "roas": roas,
                "revenue_30d": round(revenue, 2),
                "start_date": start_date.strftime("%Y-%m-%d"),
                "end_date": end_date.strftime("%Y-%m-%d") if end_date else ""
            })
    
    return pd.DataFrame(campaigns)


def generate_daily_metrics(df_campaigns, days=30):
    """Generate daily ad metrics for trend analysis"""
    daily_records = []
    
    end_date = datetime.now()
    
    for _, campaign in df_campaigns.iterrows():
        if campaign["status"] == "ENDED":
            continue
            
        campaign_id = campaign["campaign_id"]
        avg_daily_spend = campaign["total_spend_30d"] / 30
        avg_daily_impressions = campaign["impressions_30d"] / 30
        avg_daily_clicks = campaign["clicks_30d"] / 30
        avg_daily_conversions = campaign["conversions_30d"] / 30
        
        for day_offset in range(days):
            date = end_date - timedelta(days=day_offset)
            
            # Add daily variation (±30%)
            variation = random.uniform(0.7, 1.3)
            
            # Weekend boost for some platforms
            if date.weekday() >= 5:  # Weekend
                variation *= random.uniform(1.0, 1.2)
            
            daily_spend = max(0, avg_daily_spend * variation)
            daily_impressions = max(0, int(avg_daily_impressions * variation))
            daily_clicks = max(0, int(avg_daily_clicks * variation))
            daily_conversions = max(0, int(avg_daily_conversions * variation))
            
            daily_records.append({
                "campaign_id": campaign_id,
                "date": date.strftime("%Y-%m-%d"),
                "spend": round(daily_spend, 2),
                "impressions": daily_impressions,
                "clicks": daily_clicks,
                "conversions": daily_conversions,
                "cpc": round(daily_spend / max(1, daily_clicks), 2),
                "ctr": round((daily_clicks / max(1, daily_impressions)) * 100, 2),
                "conv_rate": round((daily_conversions / max(1, daily_clicks)) * 100, 2)
            })
    
    return pd.DataFrame(daily_records)


def main():
    print("[INFO] Generating ad campaign data...")
    
    # Load SKU master
    if not os.path.exists(SKU_MASTER_PATH):
        print(f"[ERROR] SKU master not found: {SKU_MASTER_PATH}")
        return
    
    df_master = pd.read_csv(SKU_MASTER_PATH)
    print(f"[INFO] Loaded {len(df_master)} SKUs")
    
    # Generate campaigns
    df_campaigns = generate_campaigns(df_master)
    print(f"[INFO] Generated {len(df_campaigns)} campaigns")
    
    # Generate daily metrics
    df_daily = generate_daily_metrics(df_campaigns, days=30)
    print(f"[INFO] Generated {len(df_daily)} daily metric records")
    
    # Save to CSV
    campaigns_path = "ad_campaigns.csv"
    daily_path = "ad_daily_metrics.csv"
    
    df_campaigns.to_csv(campaigns_path, index=False)
    df_daily.to_csv(daily_path, index=False)
    
    print(f"[SUCCESS] Saved campaigns to: {campaigns_path}")
    print(f"[SUCCESS] Saved daily metrics to: {daily_path}")
    
    # Print summary
    print("\n[SUMMARY]")
    print(f"  Total campaigns: {len(df_campaigns)}")
    print(f"  Active campaigns: {(df_campaigns['status'] == 'ACTIVE').sum()}")
    print(f"  Paused campaigns: {(df_campaigns['status'] == 'PAUSED').sum()}")
    print(f"  Platforms:")
    for platform in PLATFORMS.keys():
        count = (df_campaigns['platform'] == platform).sum()
        print(f"    - {platform}: {count}")
    print(f"  Total ad spend (30d): ₹{df_campaigns['total_spend_30d'].sum():,.2f}")
    print(f"  Avg ROAS: {df_campaigns['roas'].mean():.2f}")
    
    return df_campaigns, df_daily


if __name__ == "__main__":
    main()
