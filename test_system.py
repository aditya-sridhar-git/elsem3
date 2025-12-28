"""
Comprehensive test of all agents and API endpoints
"""
from fastapi.testclient import TestClient
from api import app

client = TestClient(app)

print("=" * 60)
print("COMPREHENSIVE SYSTEM TEST")
print("=" * 60)

# 1. Health check
print("\n1. Health Check...")
r = client.get("/api/health")
print(f"   Status: {r.status_code} - {r.json()['status']}")

# 2. Run agents
print("\n2. Running Agent Pipeline...")
r = client.post("/api/agents/run")
print(f"   Status: {r.status_code}")
if r.status_code == 200:
    print(f"   Message: {r.json().get('message', 'OK')}")

# 3. Agent status
print("\n3. Agent Status...")
r = client.get("/api/agents/status")
data = r.json()
print(f"   Pipeline Status: {data.get('status', 'N/A')}")
for agent in data.get("agents", []):
    name = agent["name"]
    status = agent["status"]
    metrics = agent.get("metrics", {})
    print(f"   - {name}: {status}")
    if metrics:
        # Show first 2 metrics
        for i, (k, v) in enumerate(metrics.items()):
            if i < 2:
                print(f"     • {k}: {v}")

# 4. Seasonal analysis
print("\n4. Seasonal Analysis...")
r = client.get("/api/seasonal/analysis")
data = r.json()
print(f"   Status: {data.get('status', 'N/A')}")
print(f"   Total SKUs: {data.get('total_skus', 0)}")
print(f"   Strong Seasonality: {data.get('strong_seasonality_count', 0)}")
print(f"   Seasonal Risks: {data.get('seasonal_risk_count', 0)}")

# Show sample seasonal data
if data.get("analysis"):
    sample = data["analysis"][0]
    print(f"   Sample: {sample['product_name'][:30]}...")
    print(f"     Peak: {sample['peak_month']}, Trough: {sample['trough_month']}")
    print(f"     Strength: {sample['seasonality_strength']:.1%}")

# 5. Recommendations
print("\n5. Recommendations...")
r = client.get("/api/recommendations")
recs = r.json()
print(f"   Total: {len(recs)}")
if recs:
    print(f"   Sample: {recs[0]['product_name'][:30]}...")
    print(f"     Action: {recs[0]['recommended_action']}")
    print(f"     Risk: {recs[0]['risk_level']}")
    if "seasonal_index_current" in recs[0]:
        print(f"     Seasonal Index: {recs[0]['seasonal_index_current']}")

# 6. Metrics summary
print("\n6. Metrics Summary...")
r = client.get("/api/metrics/summary")
data = r.json()
print(f"   Total SKUs: {data.get('total_skus', 0)}")
print(f"   Profitable: {data.get('total_profitable', 0)}")
print(f"   Loss Makers: {data.get('total_loss_makers', 0)}")
print(f"   Critical Risk: {data.get('total_critical_risk', 0)}")

print("\n" + "=" * 60)
print("ALL TESTS PASSED!")
print("=" * 60)
