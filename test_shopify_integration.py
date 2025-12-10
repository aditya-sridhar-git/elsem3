"""
Test script to verify Shopify data integration with agents
"""
import requests
import json

# Test data matching your Shopify product
test_data = {
    "products": [
        {
            "id": "9083792752856",
            "title": "Canvas Slip-Ons",
            "product_type": "Shoes",
            "vendor": "ProfitPulse",
            "variants": [
                {
                    "id": "51148627706072",
                    "price": "999.00",
                    "inventory_quantity": 45,
                    "compare_at_price": "1499.00"
                }
            ]
        }
    ]
}

print("=" * 80)
print("TESTING SHOPIFY INTEGRATION")
print("=" * 80)

# Test the endpoint
url = "http://localhost:8000/api/n8n/analyze"
print(f"\n📡 Sending request to: {url}")
print(f"📦 Input product: {test_data['products'][0]['title']}")

try:
    response = requests.post(url, json=test_data, timeout=30)
    
    print(f"\n✅ Response Status: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        
        print(f"\n📊 RESULTS:")
        print(f"   Status: {result['status']}")
        print(f"   Message: {result['message']}")
        print(f"   Total SKUs: {result['total_skus']}")
        
        if result['recommendations']:
            rec = result['recommendations'][0]
            print(f"\n🎯 FIRST RECOMMENDATION:")
            print(f"   SKU ID: {rec['sku_id']}")
            print(f"   Product Name: {rec['product_name']}")
            print(f"   Category: {rec['category']}")
            print(f"   Selling Price: ₹{rec['selling_price']}")
            print(f"   COGS: ₹{rec['cogs']:.2f}")
            print(f"   Profit per Unit: ₹{rec['profit_per_unit']:.2f}")
            print(f"   Risk Level: {rec['risk_level']}")
            print(f"   Recommended Action: {rec['recommended_action']}")
            
            print(f"\n📈 SUMMARY:")
            print(f"   Critical Risk: {result['summary']['critical_risk']}")
            print(f"   Warning Risk: {result['summary']['warning_risk']}")
            print(f"   Profitable SKUs: {result['summary']['profitable_skus']}")
            print(f"   Loss Makers: {result['summary']['loss_makers']}")
            
            # Verify it's the correct product
            print("\n" + "=" * 80)
            if rec['product_name'] == "Canvas Slip-Ons":
                print("✅ SUCCESS: Product name matches input!")
                print("✅ Shopify data is being used correctly!")
            else:
                print(f"❌ FAILURE: Expected 'Canvas Slip-Ons' but got '{rec['product_name']}'")
                print("❌ Backend is still using CSV files!")
            print("=" * 80)
        else:
            print("\n❌ No recommendations returned")
    else:
        print(f"\n❌ Error: {response.status_code}")
        print(response.text)
        
except requests.exceptions.ConnectionError:
    print("\n❌ ERROR: Cannot connect to backend")
    print("   Make sure the backend is running on http://localhost:8000")
except Exception as e:
    print(f"\n❌ ERROR: {type(e).__name__}: {str(e)}")
