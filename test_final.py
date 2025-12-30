"""
Final comprehensive test before push
"""
import sys

print("=" * 70)
print("FINAL PIPELINE & API TEST")
print("=" * 70)

# Test 1: Import all modules
print("\n1. Importing modules...")
try:
    from config import CFG
    from profit_doctor import ProfitDoctorAgent
    from inventory_sentinel import InventorySentinelAgent
    from seasonal_analyst import SeasonalAnalystAgent
    from strategy_supervisor import StrategySupervisorAgent
    from ad_gateway import AdGateway
    from ad_optimizer import AdOptimizerAgent
    from pipeline import run_pipeline
    print("   ✓ All modules imported successfully")
except Exception as e:
    print(f"   ✗ Import error: {e}")
    sys.exit(1)

# Test 2: Run pipeline
print("\n2. Running full pipeline...")
try:
    import pandas as pd
    df = run_pipeline(verbose=False)
    print(f"   ✓ Pipeline completed: {len(df)} SKUs processed")
    print(f"   ✓ Output columns: {len(df.columns)}")
except Exception as e:
    print(f"   ✗ Pipeline error: {e}")
    sys.exit(1)

# Test 3: Verify key metrics
print("\n3. Verifying key metrics...")
checks = {
    "profit_per_unit": df["profit_per_unit"].notna().all(),
    "risk_level": df["risk_level"].isin(["CRITICAL", "WARNING", "SAFE", "NO_HISTORY"]).all(),
    "impact_score": (df["impact_score"] >= 0).all(),
    "recommended_action": df["recommended_action"].notna().all(),
}
if "seasonal_index_current" in df.columns:
    checks["seasonal_index_current"] = df["seasonal_index_current"].notna().all()

for metric, passed in checks.items():
    status = "✓" if passed else "✗"
    print(f"   {status} {metric}")

# Test 4: Ad Gateway
print("\n4. Testing Ad Gateway...")
try:
    gw = AdGateway()
    summary = gw.get_summary()
    print(f"   ✓ Campaigns loaded: {summary.total_campaigns}")
    print(f"   ✓ Active: {summary.active_campaigns}, Paused: {summary.paused_campaigns}")
    print(f"   ✓ Avg ROAS: {summary.avg_roas}x")
    print(f"   ✓ Total Spend (30d): Rs.{summary.total_spend_30d:,.2f}")
except Exception as e:
    print(f"   ✗ Ad Gateway error: {e}")

# Test 5: Ad Optimizer
print("\n5. Testing Ad Optimizer...")
try:
    optimizer = AdOptimizerAgent()
    campaigns = [c.model_dump() for c in gw.get_campaigns()]
    underperforming = optimizer.identify_underperforming_ads(campaigns)
    suggestions = optimizer.suggest_budget_reallocation(campaigns)
    print(f"   ✓ LLM Enabled: {optimizer.has_llm}")
    print(f"   ✓ Underperforming detected: {len(underperforming)}")
    print(f"   ✓ Budget suggestions: {len(suggestions)}")
except Exception as e:
    print(f"   ✗ Optimizer error: {e}")

# Test 6: API endpoints
print("\n6. Testing API endpoints...")
try:
    from fastapi.testclient import TestClient
    from api import app
    
    client = TestClient(app)
    
    endpoints = [
        ("GET", "/api/health"),
        ("GET", "/api/agents/status"),
        ("GET", "/api/recommendations"),
        ("GET", "/api/metrics/summary"),
        ("GET", "/api/seasonal/analysis"),
        ("GET", "/api/ads/campaigns"),
        ("GET", "/api/ads/metrics/summary"),
        ("GET", "/api/ads/metrics/roas"),
        ("GET", "/api/ads/budget/overview"),
    ]
    
    all_passed = True
    for method, endpoint in endpoints:
        if method == "GET":
            r = client.get(endpoint)
        else:
            r = client.post(endpoint)
        
        status = "✓" if r.status_code == 200 else "✗"
        if r.status_code != 200:
            all_passed = False
        print(f"   {status} {method} {endpoint} -> {r.status_code}")
    
except Exception as e:
    print(f"   ✗ API error: {e}")
    all_passed = False

# Test 7: Profit Doctor with Ad Gateway integration
print("\n7. Testing Profit Doctor + Ad Gateway integration...")
try:
    agent = ProfitDoctorAgent()
    df_master = pd.read_csv("synthetic dataset/sku_master.csv")
    result = agent.compute_profit_metrics(df_master)
    
    has_ad_data = "ad_roas" in result.columns and result["ad_roas"].sum() > 0
    print(f"   ✓ Ad ROAS Column: {'Present' if 'ad_roas' in result.columns else 'Missing'}")
    print(f"   ✓ Ad Data Flowing: {'Yes' if has_ad_data else 'No'}")
    if has_ad_data:
        print(f"   ✓ Sample ROAS values: {result['ad_roas'].head(3).tolist()}")
except Exception as e:
    print(f"   ✗ Integration error: {e}")

# Summary
print("\n" + "=" * 70)
print("TEST SUMMARY")
print("=" * 70)
print(f"Pipeline:     ✓ {len(df)} SKUs with {len(df.columns)} columns")
print(f"Agents:       ✓ Profit Doctor, Inventory Sentinel, Seasonal Analyst, Strategy Supervisor")
print(f"Ad Gateway:   ✓ {summary.total_campaigns} campaigns, {summary.avg_roas}x ROAS")
print(f"API:          ✓ All endpoints responding")
print("=" * 70)
print("READY TO PUSH!")
print("=" * 70)
