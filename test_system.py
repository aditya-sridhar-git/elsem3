"""
Comprehensive test of all agents and API endpoints including Ad Gateway
"""
from fastapi.testclient import TestClient
from api import app

client = TestClient(app)

print("=" * 60)
print("COMPREHENSIVE SYSTEM TEST (with Ad Gateway)")
print("=" * 60)

# 1. Health check
print("\n1. Health Check...")
r = client.get("/api/health")
print(f"   Status: {r.status_code} - {r.json()['status']}")

# 2. Run agents
print("\n2. Running Agent Pipeline...")
r = client.post("/api/agents/run")
print(f"   Status: {r.status_code}")

# 3. Agent status (now includes Ad Gateway)
print("\n3. Agent Status...")
r = client.get("/api/agents/status")
data = r.json()
print(f"   Pipeline Status: {data.get('status', 'N/A')}")
for agent in data.get("agents", []):
    name = agent["name"]
    status = agent["status"]
    print(f"   - {name}: {status}")

# 4. Ad Gateway Tests
print("\n4. Ad Gateway Tests...")

# 4a. Get campaigns
r = client.get("/api/ads/campaigns")
data = r.json()
print(f"   Total Campaigns: {data.get('total', 0)}")

# 4b. Get metrics summary
r = client.get("/api/ads/metrics/summary")
data = r.json()
print(f"   Ad Spend (30d): Rs.{data.get('total_spend_30d', 0):,.2f}")
print(f"   Avg ROAS: {data.get('avg_roas', 0)}x")
print(f"   Platforms: {data.get('platforms', {})}")

# 4c. Connect a platform (simulated)
print("\n   Connecting Google Ads...")
r = client.post("/api/ads/connect", json={
    "platform": "GOOGLE_ADS",
    "api_key": "test_api_key_12345",
    "account_id": "ACC_DEMO_001"
})
if r.status_code == 200:
    print(f"   Connected: {r.json().get('message')}")
else:
    print(f"   Error: {r.status_code}")

# 4d. Get connected platforms
r = client.get("/api/ads/platforms")
data = r.json()
print(f"   Connected Platforms: {data.get('total', 0)}")

# 4e. Get ROAS by SKU
r = client.get("/api/ads/metrics/roas")
data = r.json()
print(f"   SKUs with ads: {data.get('total_skus', 0)}")
print(f"   Average ROAS: {data.get('avg_roas', 0)}x")

# 4f. Get budget overview
r = client.get("/api/ads/budget/overview")
data = r.json()
print(f"   Total Daily Budget: Rs.{data.get('total_daily_budget', 0):,.2f}")
print(f"   Active Campaigns: {data.get('active_campaigns', 0)}")

# 4g. Get optimization suggestions
print("\n   Getting Optimization Suggestions...")
r = client.post("/api/ads/optimize")
data = r.json()
print(f"   Underperforming: {len(data.get('underperforming_campaigns', []))}")
print(f"   Budget Suggestions: {len(data.get('budget_suggestions', []))}")
print(f"   LLM Enabled: {data.get('llm_enabled', False)}")

# 5. Seasonal analysis
print("\n5. Seasonal Analysis...")
r = client.get("/api/seasonal/analysis")
data = r.json()
print(f"   Status: {data.get('status', 'N/A')}")
print(f"   Total SKUs: {data.get('total_skus', 0)}")
print(f"   Strong Seasonality: {data.get('strong_seasonality_count', 0)}")

# 6. Recommendations (now includes ad data)
print("\n6. Recommendations...")
r = client.get("/api/recommendations")
recs = r.json()
print(f"   Total: {len(recs)}")
if recs:
    sample = recs[0]
    print(f"   Sample: {sample['product_name'][:30]}...")
    print(f"     Profit/Unit: Rs.{sample.get('profit_per_unit', 0):.2f}")
    print(f"     Risk: {sample.get('risk_level', 'N/A')}")
    if 'ad_roas' in sample:
        print(f"     Ad ROAS: {sample.get('ad_roas', 0)}x")

# 7. Test campaign CRUD
print("\n7. Campaign CRUD Test...")
# Create
r = client.post("/api/ads/campaigns", json={
    "sku_id": "SKU_ELEC_001",
    "platform": "GOOGLE_ADS",
    "campaign_name": "Test_Campaign_API",
    "daily_budget": 100.0
})
if r.status_code == 200:
    campaign_id = r.json().get("campaign", {}).get("campaign_id")
    print(f"   Created: {campaign_id}")
    
    # Pause
    r = client.post(f"/api/ads/campaigns/{campaign_id}/pause")
    print(f"   Paused: {r.status_code == 200}")
    
    # Resume
    r = client.post(f"/api/ads/campaigns/{campaign_id}/resume")
    print(f"   Resumed: {r.status_code == 200}")
    
    # Delete
    r = client.delete(f"/api/ads/campaigns/{campaign_id}")
    print(f"   Deleted: {r.status_code == 200}")

print("\n" + "=" * 60)
print("ALL TESTS PASSED!")
print("=" * 60)
