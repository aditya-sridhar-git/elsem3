
import requests
import pandas as pd
import time
from typing import Tuple, Optional, Dict, List
from datetime import datetime, timedelta
from config import CFG

class ShopifyLoader:
    def __init__(self):
        self.shop_url = CFG.shopify_shop_domain
        self.access_token = CFG.shopify_access_token
        self.api_version = "2024-01"
        self.base_url = f"https://{self.shop_url}/admin/api/{self.api_version}"
        self.headers = {
            "X-Shopify-Access-Token": self.access_token,
            "Content-Type": "application/json"
        }
        
    def _get_headers(self):
        return self.headers

    def validate_config(self):
        if not self.shop_url or "myshopify.com" not in self.shop_url:
            print("[ERROR] Invalid Shopify shop domain")
            return False
        if not self.access_token:
            print("[ERROR] Missing Shopify access token")
            return False
        return True

    def fetch_data(self) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Fetch products and orders from Shopify and convert to DataFrames
        Returns: (df_master, df_sales)
        """
        if not self.validate_config():
            return pd.DataFrame(), pd.DataFrame()
            
        print(f"[INFO] Fetching data from Shopify: {self.shop_url}")
        
        # 1. Fetch Products
        products = self._fetch_all_resource("products")
        print(f"[INFO] Fetched {len(products)} products")
        
        # 2. Fetch Orders (last 90 days for sales history)
        ninety_days_ago = (datetime.now() - timedelta(days=90)).isoformat()
        orders = self._fetch_all_resource("orders", params={"status": "any", "created_at_min": ninety_days_ago})
        print(f"[INFO] Fetched {len(orders)} orders")
        
        # 3. Process into DataFrames
        df_master = self._process_products(products)
        df_sales = self._process_orders(orders)
        
        return df_master, df_sales

    def _fetch_all_resource(self, resource: str, params: Dict = None) -> List[Dict]:
        all_items = []
        url = f"{self.base_url}/{resource}.json"
        params = params or {}
        params["limit"] = 250
        
        while url:
            try:
                response = requests.get(url, headers=self.headers, params=params)
                response.raise_for_status()
                data = response.json()
                
                items = data.get(resource, [])
                all_items.extend(items)
                
                # Pagination
                link_header = response.headers.get("Link")
                url = self._get_next_link(link_header)
                params = {} # Params only needed for first request if using link header
                
                time.sleep(0.5) # Rate limit friendly
            except Exception as e:
                print(f"[ERROR] Failed to fetch {resource}: {str(e)}")
                break
                
        return all_items

    def _get_next_link(self, link_header):
        if not link_header:
            return None
        links = link_header.split(',')
        for link in links:
            if 'rel="next"' in link:
                return link.split(';')[0].strip('<> ')
        return None

    def _process_products(self, products: List[Dict]) -> pd.DataFrame:
        rows = []
        for p in products:
            for v in p.get("variants", []):
                # Basic fields
                sku = v.get("sku") or f"no-sku-{v['id']}"
                price = float(v.get("price", 0))
                stock = int(v.get("inventory_quantity", 0))
                
                # Mock COGS if not available (Shopify doesn't expose cost in standard product read usually)
                # Assumes 40% margin if unknown
                cogs = price * 0.6 
                
                # Lead time mock
                lead_time = 7 
                
                rows.append({
                    "sku_id": sku,
                    "category": p.get("product_type", "Uncategorized"),
                    "product_name": p.get("title") + ("" if len(p["variants"]) == 1 else f" - {v.get('title')}"),
                    "selling_price": price,
                    "cogs": cogs,
                    "current_stock": stock,
                    "lead_time_days": lead_time,
                    "shopify_variant_id": v["id"],
                    "shopify_inventory_item_id": v["inventory_item_id"]
                })
        
        df = pd.DataFrame(rows)
        if df.empty:
            return df
            
        # Ensure correct types
        df["selling_price"] = df["selling_price"].astype(float)
        df["cogs"] = df["cogs"].astype(float)
        df["current_stock"] = df["current_stock"].astype(int)
        
        return df

    def _process_orders(self, orders: List[Dict]) -> pd.DataFrame:
        rows = []
        for o in orders:
            date_str = o.get("created_at", "")[:10] # YYYY-MM-DD
            # Convert YYYY-MM-DD to DD-MM-YYYY as expected by pipeline sometimes? 
            # Actually pipeline often expects standard parsing. Let's stick to YYYY-MM-DD and ensure pipeline handles it.
            # Wait, sales_gen.py usually outputs DD-MM-YYYY. Let's convert to match typical format if needed.
            # Using standard pandas `to_datetime` in pipeline is safer.
            
            for item in o.get("line_items", []):
                rows.append({
                    "sku_id": item.get("sku") or f"no-sku-{item.get('variant_id')}",
                    "date": date_str,
                    "units_sold": item.get("quantity", 0)
                })
                
        df = pd.DataFrame(rows)
        if df.empty:
             return pd.DataFrame(columns=["sku_id", "date", "units_sold"])
        return df

    def update_stock(self, variant_id: int, inventory_item_id: int, new_qty: int):
        """
        Update inventory level. Shopify requires setting inventory at a location.
        We'll first fetch locations, then set for the first one.
        """
        try:
            # 1. Get Location
            loc_resp = requests.get(f"{self.base_url}/locations.json", headers=self.headers)
            loc_resp.raise_for_status()
            locations = loc_resp.json().get("locations", [])
            if not locations:
                raise Exception("No location found")
            location_id = locations[0]["id"]
            
            # 2. Set Inventory
            time.sleep(0.5)
            payload = {
                "location_id": location_id,
                "inventory_item_id": inventory_item_id,
                "available": new_qty
            }
            resp = requests.post(f"{self.base_url}/inventory_levels/set.json", headers=self.headers, json=payload)
            resp.raise_for_status()
            print(f"[SUCCESS] Updated stock for item {inventory_item_id} to {new_qty}")
            return True
        except Exception as e:
            print(f"[ERROR] Failed to update stock: {str(e)}")
            raise

    def update_price(self, variant_id: int, new_price: float):
        try:
            payload = {
                "variant": {
                    "id": variant_id,
                    "price": str(new_price)
                }
            }
            resp = requests.put(f"{self.base_url}/variants/{variant_id}.json", headers=self.headers, json=payload)
            resp.raise_for_status()
            print(f"[SUCCESS] Updated price for variant {variant_id} to {new_price}")
            return True
        except Exception as e:
            print(f"[ERROR] Failed to update price: {str(e)}")
            raise
