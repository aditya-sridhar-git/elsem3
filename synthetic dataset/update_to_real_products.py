"""
Script to update synthetic dataset with real Shopify product SKUs and names.
"""
import pandas as pd
import random

# Real Shopify products mapping
REAL_PRODUCTS = {
    "SKU_SHOES_9083792720088": "Classic Leather Loafers",
    "SKU_SHOES_9083792785624": "Limited Edition Hype Kicks",
    "SKU_SHOES_9083792654552": "Urban High-Top Sneakers",
    "SKU_SHOES_9083792687320": "Marathon Pro Running Shoes",
    "SKU_SHOES_9083792752856": "Canvas Slip-Ons"
}

# Get list of real SKUs
REAL_SKUS = list(REAL_PRODUCTS.keys())

# Old fake SKUs to replace
OLD_SKUS = [
    "SKU_ELEC_001", "SKU_ELEC_002", "SKU_ELEC_003", "SKU_ELEC_004",
    "SKU_FASH_001", "SKU_FASH_002", "SKU_FASH_003", "SKU_FASH_004",
    "SKU_HOME_001", "SKU_HOME_002", "SKU_HOME_003", "SKU_HOME_004",
    "SKU_BEAUTY_001", "SKU_BEAUTY_002", "SKU_BEAUTY_003", "SKU_BEAUTY_004",
    "SKU_SPORTS_001", "SKU_SPORTS_002", "SKU_SPORTS_003", "SKU_SPORTS_004"
]

# Create mapping from old SKUs to real SKUs (distribute evenly, 4 old SKUs -> 1 real SKU)
SKU_MAPPING = {}
for i, old_sku in enumerate(OLD_SKUS):
    SKU_MAPPING[old_sku] = REAL_SKUS[i % 5]

print("SKU Mapping:")
for old, new in SKU_MAPPING.items():
    print(f"  {old} -> {new} ({REAL_PRODUCTS[new]})")

# 1. Update sku_master.csv
print("\n1. Updating sku_master.csv...")
sku_master = pd.read_csv("sku_master.csv")

# Create new sku_master with only 5 products
new_sku_master_data = []
for sku_id, product_name in REAL_PRODUCTS.items():
    new_sku_master_data.append({
        "sku_id": sku_id,
        "category": "Footwear",
        "product_name": product_name,
        "selling_price": 2499,
        "mrp": 3499,
        "cogs": 900,
        "shipping_cost_per_unit": 70,
        "platform_fee_percent": 2.0,
        "platform_fixed_fee": 3,
        "ad_spend_total_last_30_days": 8000,
        "units_sold_last_30_days": 100,
        "current_stock": [5, 20, 45, 120, 200][list(REAL_PRODUCTS.keys()).index(sku_id)],  # Match screenshot
        "lead_time_days": 10,
        "is_hero": sku_id in ["SKU_SHOES_9083792785624", "SKU_SHOES_9083792687320"]  # Hype Kicks and Marathon Pro
    })

new_sku_master = pd.DataFrame(new_sku_master_data)
new_sku_master.to_csv("sku_master.csv", index=False)
print(f"   Created new sku_master.csv with {len(new_sku_master)} products")

# 2. Update seasonal_sales_history.csv - add product_name column
print("\n2. Updating seasonal_sales_history.csv...")
seasonal = pd.read_csv("seasonal_sales_history.csv")
print(f"   Original rows: {len(seasonal)}")

# Replace old SKUs with real SKUs
seasonal["sku_id"] = seasonal["sku_id"].map(SKU_MAPPING)
# Add product_name column
seasonal["product_name"] = seasonal["sku_id"].map(REAL_PRODUCTS)

# Aggregate sales data by new SKU and date (since multiple old SKUs map to same new SKU)
seasonal_agg = seasonal.groupby(["sku_id", "product_name", "date", "month", "day_of_week", "is_weekend"], as_index=False).agg({
    "units_sold": "sum"
})

# Reorder columns
seasonal_agg = seasonal_agg[["sku_id", "product_name", "date", "units_sold", "month", "day_of_week", "is_weekend"]]
seasonal_agg.to_csv("seasonal_sales_history.csv", index=False)
print(f"   New rows: {len(seasonal_agg)} (with product_name column added)")

# 3. Update ad_campaigns.csv
print("\n3. Updating ad_campaigns.csv...")
campaigns = pd.read_csv("ad_campaigns.csv")
print(f"   Original campaigns: {len(campaigns)}")

# Replace old SKUs with real SKUs
campaigns["sku_id"] = campaigns["sku_id"].map(SKU_MAPPING)

# Update campaign names to reflect real product names
def update_campaign_name(row):
    product_name = REAL_PRODUCTS[row["sku_id"]]
    short_name = "_".join(product_name.split()[:3])
    platform = row["platform"]
    if platform == "GOOGLE_ADS":
        prefix = random.choice(["Search", "Shopping", "Display"])
    elif platform == "META_ADS":
        prefix = random.choice(["FB", "IG"])
    else:  # AMAZON_ADS
        prefix = random.choice(["SP", "SB", "SD"])
    return f"{prefix}_{short_name}"

campaigns["campaign_name"] = campaigns.apply(update_campaign_name, axis=1)

# Keep only unique campaigns per SKU+platform (take first 2-3 per SKU)
campaigns_filtered = campaigns.groupby(["sku_id", "platform"]).head(1).reset_index(drop=True)
campaigns_filtered.to_csv("ad_campaigns.csv", index=False)
print(f"   New campaigns: {len(campaigns_filtered)}")

# 4. Update ad_daily_metrics.csv
print("\n4. Updating ad_daily_metrics.csv...")
daily_metrics = pd.read_csv("ad_daily_metrics.csv")
print(f"   Original rows: {len(daily_metrics)}")

# Get the campaign IDs that we're keeping
valid_campaign_ids = set(campaigns_filtered["campaign_id"])
daily_metrics_filtered = daily_metrics[daily_metrics["campaign_id"].isin(valid_campaign_ids)]
daily_metrics_filtered.to_csv("ad_daily_metrics.csv", index=False)
print(f"   New rows: {len(daily_metrics_filtered)}")

print("\n✅ All files updated successfully!")
print("\nNew product lineup:")
for sku_id, name in REAL_PRODUCTS.items():
    print(f"  {sku_id}: {name}")
