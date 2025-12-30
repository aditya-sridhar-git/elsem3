# ad_gateway.py - Central Ad Management and Tracking Module

import pandas as pd
import numpy as np
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import os
from pydantic import BaseModel, Field

from config import CFG


# ============================================================================
# Pydantic Models for API
# ============================================================================

class AdPlatformCredentials(BaseModel):
    """Model for connecting ad platform APIs"""
    platform: str  # GOOGLE_ADS, META_ADS, AMAZON_ADS
    api_key: str
    account_id: str
    client_id: Optional[str] = None
    client_secret: Optional[str] = None


class CampaignCreate(BaseModel):
    """Model for creating a new campaign"""
    sku_id: str
    platform: str
    campaign_name: str
    daily_budget: float
    status: str = "ACTIVE"


class CampaignUpdate(BaseModel):
    """Model for updating a campaign"""
    campaign_name: Optional[str] = None
    daily_budget: Optional[float] = None
    status: Optional[str] = None


class Campaign(BaseModel):
    """Full campaign model"""
    campaign_id: str
    sku_id: str
    platform: str
    campaign_name: str
    status: str
    daily_budget: float
    total_spend_30d: float
    impressions_30d: int
    clicks_30d: int
    conversions_30d: int
    cpc: float
    ctr: float
    conversion_rate: float
    roas: float
    revenue_30d: float = 0.0
    start_date: str = ""
    end_date: str = ""


class AdMetrics(BaseModel):
    """Ad performance metrics"""
    impressions: int
    clicks: int
    conversions: int
    spend: float
    revenue: float
    cpc: float
    ctr: float
    conversion_rate: float
    roas: float
    trend: str = "STABLE"  # IMPROVING, DECLINING, STABLE


class AdSummary(BaseModel):
    """Overall ad summary"""
    total_campaigns: int
    active_campaigns: int
    paused_campaigns: int
    total_spend_30d: float
    total_revenue_30d: float
    avg_roas: float
    avg_cpc: float
    total_conversions: int
    platforms: Dict[str, int]


# ============================================================================
# Ad Gateway Class
# ============================================================================

@dataclass
class AdGateway:
    """
    Central hub for ad management and tracking.
    
    Features:
    1. Platform Connectors - Connect to ad APIs (simulated)
    2. Campaign Manager - CRUD operations on campaigns
    3. Performance Tracker - Real-time metrics
    4. Spend Calculator - Calculate ad spend by SKU
    """
    
    campaigns_path: str = "synthetic dataset/ad_campaigns.csv"
    daily_metrics_path: str = "synthetic dataset/ad_daily_metrics.csv"
    
    # In-memory storage
    connected_platforms: Dict[str, AdPlatformCredentials] = field(default_factory=dict)
    _campaigns_df: Optional[pd.DataFrame] = None
    _daily_metrics_df: Optional[pd.DataFrame] = None
    
    def __post_init__(self):
        """Load campaign data on initialization"""
        self._load_data()
    
    def _load_data(self):
        """Load campaign and daily metrics data"""
        if os.path.exists(self.campaigns_path):
            self._campaigns_df = pd.read_csv(self.campaigns_path)
            print(f"[INFO] AdGateway: Loaded {len(self._campaigns_df)} campaigns")
        else:
            self._campaigns_df = pd.DataFrame()
            print(f"[WARNING] AdGateway: No campaigns data found at {self.campaigns_path}")
        
        if os.path.exists(self.daily_metrics_path):
            self._daily_metrics_df = pd.read_csv(self.daily_metrics_path)
        else:
            self._daily_metrics_df = pd.DataFrame()
    
    def _save_campaigns(self):
        """Save campaigns to CSV"""
        if self._campaigns_df is not None:
            self._campaigns_df.to_csv(self.campaigns_path, index=False)
    
    # ========================================================================
    # Platform Connection
    # ========================================================================
    
    def connect_platform(self, credentials: AdPlatformCredentials) -> Dict[str, Any]:
        """
        Connect to an ad platform API (simulated).
        In production, this would validate API credentials with the platform.
        """
        platform = credentials.platform.upper()
        
        # Validate platform
        valid_platforms = ["GOOGLE_ADS", "META_ADS", "AMAZON_ADS"]
        if platform not in valid_platforms:
            return {
                "success": False,
                "error": f"Invalid platform. Must be one of: {valid_platforms}"
            }
        
        # Simulate API validation (in production, would call actual API)
        if not credentials.api_key or not credentials.account_id:
            return {
                "success": False,
                "error": "Missing required credentials (api_key, account_id)"
            }
        
        # Store connection
        self.connected_platforms[platform] = credentials
        
        # Get campaign count for this platform
        platform_campaigns = 0
        if self._campaigns_df is not None and not self._campaigns_df.empty:
            platform_campaigns = (self._campaigns_df["platform"] == platform).sum()
        
        return {
            "success": True,
            "platform": platform,
            "account_id": credentials.account_id,
            "campaigns_found": platform_campaigns,
            "message": f"Successfully connected to {platform}"
        }
    
    def disconnect_platform(self, platform: str) -> bool:
        """Disconnect from a platform"""
        platform = platform.upper()
        if platform in self.connected_platforms:
            del self.connected_platforms[platform]
            return True
        return False
    
    def get_connected_platforms(self) -> List[Dict[str, Any]]:
        """Get list of connected platforms"""
        result = []
        for platform, creds in self.connected_platforms.items():
            # Get platform stats
            stats = {"campaigns": 0, "spend_30d": 0}
            if self._campaigns_df is not None and not self._campaigns_df.empty:
                platform_data = self._campaigns_df[self._campaigns_df["platform"] == platform]
                stats["campaigns"] = len(platform_data)
                stats["spend_30d"] = float(platform_data["total_spend_30d"].sum())
            
            result.append({
                "platform": platform,
                "account_id": creds.account_id,
                "connected_at": datetime.now().isoformat(),  # Would be actual connect time
                **stats
            })
        return result
    
    # ========================================================================
    # Campaign Management
    # ========================================================================
    
    def get_campaigns(self, sku_id: Optional[str] = None, platform: Optional[str] = None,
                      status: Optional[str] = None) -> List[Campaign]:
        """Get campaigns with optional filters"""
        if self._campaigns_df is None or self._campaigns_df.empty:
            return []
        
        df = self._campaigns_df.copy()
        
        if sku_id:
            df = df[df["sku_id"] == sku_id]
        if platform:
            df = df[df["platform"] == platform.upper()]
        if status:
            df = df[df["status"] == status.upper()]
        
        campaigns = []
        for _, row in df.iterrows():
            campaigns.append(Campaign(
                campaign_id=row["campaign_id"],
                sku_id=row["sku_id"],
                platform=row["platform"],
                campaign_name=row["campaign_name"],
                status=row["status"],
                daily_budget=float(row["daily_budget"]),
                total_spend_30d=float(row["total_spend_30d"]),
                impressions_30d=int(row["impressions_30d"]),
                clicks_30d=int(row["clicks_30d"]),
                conversions_30d=int(row["conversions_30d"]),
                cpc=float(row["cpc"]),
                ctr=float(row["ctr"]),
                conversion_rate=float(row["conversion_rate"]),
                roas=float(row["roas"]),
                revenue_30d=float(row.get("revenue_30d", 0)),
                start_date=str(row.get("start_date", "")),
                end_date=str(row.get("end_date", ""))
            ))
        
        return campaigns
    
    def get_campaign(self, campaign_id: str) -> Optional[Campaign]:
        """Get a single campaign by ID"""
        campaigns = self.get_campaigns()
        for c in campaigns:
            if c.campaign_id == campaign_id:
                return c
        return None
    
    def create_campaign(self, data: CampaignCreate) -> Campaign:
        """Create a new campaign"""
        import random
        
        campaign_id = f"CAM_{random.randint(10000, 99999)}"
        
        new_row = {
            "campaign_id": campaign_id,
            "sku_id": data.sku_id,
            "platform": data.platform.upper(),
            "campaign_name": data.campaign_name,
            "status": data.status.upper(),
            "daily_budget": data.daily_budget,
            "total_spend_30d": 0.0,
            "impressions_30d": 0,
            "clicks_30d": 0,
            "conversions_30d": 0,
            "cpc": 0.0,
            "ctr": 0.0,
            "conversion_rate": 0.0,
            "roas": 0.0,
            "revenue_30d": 0.0,
            "start_date": datetime.now().strftime("%Y-%m-%d"),
            "end_date": ""
        }
        
        # Add to DataFrame
        if self._campaigns_df is None or self._campaigns_df.empty:
            self._campaigns_df = pd.DataFrame([new_row])
        else:
            self._campaigns_df = pd.concat([self._campaigns_df, pd.DataFrame([new_row])], ignore_index=True)
        
        self._save_campaigns()
        
        return Campaign(**new_row)
    
    def update_campaign(self, campaign_id: str, data: CampaignUpdate) -> Optional[Campaign]:
        """Update campaign settings"""
        if self._campaigns_df is None or self._campaigns_df.empty:
            return None
        
        mask = self._campaigns_df["campaign_id"] == campaign_id
        if not mask.any():
            return None
        
        if data.campaign_name:
            self._campaigns_df.loc[mask, "campaign_name"] = data.campaign_name
        if data.daily_budget is not None:
            self._campaigns_df.loc[mask, "daily_budget"] = data.daily_budget
        if data.status:
            self._campaigns_df.loc[mask, "status"] = data.status.upper()
        
        self._save_campaigns()
        
        return self.get_campaign(campaign_id)
    
    def pause_campaign(self, campaign_id: str) -> bool:
        """Pause a campaign"""
        result = self.update_campaign(campaign_id, CampaignUpdate(status="PAUSED"))
        return result is not None
    
    def resume_campaign(self, campaign_id: str) -> bool:
        """Resume a paused campaign"""
        result = self.update_campaign(campaign_id, CampaignUpdate(status="ACTIVE"))
        return result is not None
    
    def delete_campaign(self, campaign_id: str) -> bool:
        """Delete a campaign"""
        if self._campaigns_df is None or self._campaigns_df.empty:
            return False
        
        initial_len = len(self._campaigns_df)
        self._campaigns_df = self._campaigns_df[self._campaigns_df["campaign_id"] != campaign_id]
        
        if len(self._campaigns_df) < initial_len:
            self._save_campaigns()
            return True
        return False
    
    # ========================================================================
    # Spend Calculations (for Profit Doctor integration)
    # ========================================================================
    
    def get_ad_spend_by_sku(self, sku_id: str, days: int = 30) -> float:
        """
        Get total ad spend for a SKU.
        This is used by Profit Doctor to calculate net profit.
        """
        if self._campaigns_df is None or self._campaigns_df.empty:
            return 0.0
        
        sku_campaigns = self._campaigns_df[self._campaigns_df["sku_id"] == sku_id]
        
        if sku_campaigns.empty:
            return 0.0
        
        # For 30 days, use total_spend_30d directly
        if days == 30:
            return float(sku_campaigns["total_spend_30d"].sum())
        
        # For other periods, calculate from daily metrics
        if self._daily_metrics_df is not None and not self._daily_metrics_df.empty:
            campaign_ids = sku_campaigns["campaign_id"].tolist()
            cutoff_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
            
            daily_data = self._daily_metrics_df[
                (self._daily_metrics_df["campaign_id"].isin(campaign_ids)) &
                (self._daily_metrics_df["date"] >= cutoff_date)
            ]
            
            return float(daily_data["spend"].sum())
        
        # Fallback: prorate 30-day spend
        return float(sku_campaigns["total_spend_30d"].sum() * (days / 30))
    
    def get_all_sku_ad_spend(self, days: int = 30) -> Dict[str, float]:
        """Get ad spend for all SKUs as a dictionary"""
        if self._campaigns_df is None or self._campaigns_df.empty:
            return {}
        
        result = {}
        for sku_id in self._campaigns_df["sku_id"].unique():
            result[sku_id] = self.get_ad_spend_by_sku(sku_id, days)
        
        return result
    
    # ========================================================================
    # Performance Metrics
    # ========================================================================
    
    def get_metrics_by_sku(self, sku_id: str) -> AdMetrics:
        """Get aggregated ad metrics for a SKU"""
        if self._campaigns_df is None or self._campaigns_df.empty:
            return AdMetrics(
                impressions=0, clicks=0, conversions=0, spend=0,
                revenue=0, cpc=0, ctr=0, conversion_rate=0, roas=0
            )
        
        sku_campaigns = self._campaigns_df[self._campaigns_df["sku_id"] == sku_id]
        
        if sku_campaigns.empty:
            return AdMetrics(
                impressions=0, clicks=0, conversions=0, spend=0,
                revenue=0, cpc=0, ctr=0, conversion_rate=0, roas=0
            )
        
        impressions = int(sku_campaigns["impressions_30d"].sum())
        clicks = int(sku_campaigns["clicks_30d"].sum())
        conversions = int(sku_campaigns["conversions_30d"].sum())
        spend = float(sku_campaigns["total_spend_30d"].sum())
        revenue = float(sku_campaigns["revenue_30d"].sum())
        
        cpc = spend / max(1, clicks)
        ctr = (clicks / max(1, impressions)) * 100
        conv_rate = (conversions / max(1, clicks)) * 100
        roas = revenue / max(1, spend)
        
        # Determine trend from daily metrics
        trend = self._calculate_trend(sku_campaigns["campaign_id"].tolist())
        
        return AdMetrics(
            impressions=impressions,
            clicks=clicks,
            conversions=conversions,
            spend=round(spend, 2),
            revenue=round(revenue, 2),
            cpc=round(cpc, 2),
            ctr=round(ctr, 2),
            conversion_rate=round(conv_rate, 2),
            roas=round(roas, 2),
            trend=trend
        )
    
    def _calculate_trend(self, campaign_ids: List[str]) -> str:
        """Calculate performance trend from daily metrics"""
        if self._daily_metrics_df is None or self._daily_metrics_df.empty:
            return "STABLE"
        
        daily = self._daily_metrics_df[self._daily_metrics_df["campaign_id"].isin(campaign_ids)]
        
        if len(daily) < 14:
            return "STABLE"
        
        # Compare last 7 days vs previous 7 days
        daily["date"] = pd.to_datetime(daily["date"])
        daily = daily.sort_values("date")
        
        recent = daily.tail(7)["conversions"].sum()
        previous = daily.head(len(daily) - 7).tail(7)["conversions"].sum()
        
        if previous == 0:
            return "STABLE"
        
        change = (recent - previous) / previous
        
        if change > 0.1:
            return "IMPROVING"
        elif change < -0.1:
            return "DECLINING"
        else:
            return "STABLE"
    
    def get_summary(self) -> AdSummary:
        """Get overall ad performance summary"""
        if self._campaigns_df is None or self._campaigns_df.empty:
            return AdSummary(
                total_campaigns=0, active_campaigns=0, paused_campaigns=0,
                total_spend_30d=0, total_revenue_30d=0, avg_roas=0,
                avg_cpc=0, total_conversions=0, platforms={}
            )
        
        df = self._campaigns_df
        
        return AdSummary(
            total_campaigns=len(df),
            active_campaigns=int((df["status"] == "ACTIVE").sum()),
            paused_campaigns=int((df["status"] == "PAUSED").sum()),
            total_spend_30d=round(float(df["total_spend_30d"].sum()), 2),
            total_revenue_30d=round(float(df["revenue_30d"].sum()), 2),
            avg_roas=round(float(df["roas"].mean()), 2),
            avg_cpc=round(float(df["cpc"].mean()), 2),
            total_conversions=int(df["conversions_30d"].sum()),
            platforms={
                platform: int((df["platform"] == platform).sum())
                for platform in df["platform"].unique()
            }
        )
    
    def get_roas_by_sku(self) -> Dict[str, float]:
        """Get ROAS for each SKU"""
        if self._campaigns_df is None or self._campaigns_df.empty:
            return {}
        
        result = {}
        for sku_id in self._campaigns_df["sku_id"].unique():
            sku_data = self._campaigns_df[self._campaigns_df["sku_id"] == sku_id]
            total_revenue = sku_data["revenue_30d"].sum()
            total_spend = sku_data["total_spend_30d"].sum()
            result[sku_id] = round(total_revenue / max(1, total_spend), 2)
        
        return result


# Global instance
ad_gateway = AdGateway()


# ============================================================================
# Standalone Testing
# ============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("AD GATEWAY TEST")
    print("=" * 60)
    
    gw = AdGateway()
    
    # Test summary
    summary = gw.get_summary()
    print(f"\nTotal Campaigns: {summary.total_campaigns}")
    print(f"Active: {summary.active_campaigns}, Paused: {summary.paused_campaigns}")
    print(f"Total Spend (30d): ₹{summary.total_spend_30d:,.2f}")
    print(f"Total Revenue (30d): ₹{summary.total_revenue_30d:,.2f}")
    print(f"Average ROAS: {summary.avg_roas}x")
    print(f"Platforms: {summary.platforms}")
    
    # Test get campaigns
    campaigns = gw.get_campaigns()
    print(f"\nLoaded {len(campaigns)} campaigns")
    
    if campaigns:
        sample = campaigns[0]
        print(f"\nSample Campaign: {sample.campaign_name}")
        print(f"  Platform: {sample.platform}")
        print(f"  SKU: {sample.sku_id}")
        print(f"  Status: {sample.status}")
        print(f"  Spend: ₹{sample.total_spend_30d:,.2f}")
        print(f"  ROAS: {sample.roas}x")
    
    # Test SKU spend lookup
    if campaigns:
        sku_id = campaigns[0].sku_id
        spend = gw.get_ad_spend_by_sku(sku_id)
        print(f"\nAd spend for {sku_id}: ₹{spend:,.2f}")
        
        metrics = gw.get_metrics_by_sku(sku_id)
        print(f"Metrics: {metrics.impressions} impressions, {metrics.clicks} clicks, {metrics.conversions} conversions")
        print(f"Trend: {metrics.trend}")
    
    # Test connect platform
    print("\nTesting platform connection...")
    result = gw.connect_platform(AdPlatformCredentials(
        platform="GOOGLE_ADS",
        api_key="test_key_123",
        account_id="ACC_123456"
    ))
    print(f"Connection result: {result}")
    
    print(f"\nConnected platforms: {gw.get_connected_platforms()}")
    
    print("\n" + "=" * 60)
    print("AD GATEWAY TEST COMPLETE")
    print("=" * 60)
