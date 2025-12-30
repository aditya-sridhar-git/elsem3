# ad_optimizer.py - LangChain-powered Ad Optimization Agent

import pandas as pd
import numpy as np
from dataclasses import dataclass
import time
from typing import Optional, List, Dict, Any
from datetime import datetime

from config import CFG, HAS_LANGCHAIN, llm

# Import pydantic
try:
    from pydantic import BaseModel, Field
except ImportError:
    BaseModel = None
    Field = None

if HAS_LANGCHAIN:
    from langchain_core.prompts import ChatPromptTemplate


class AdOptimizationInsight(BaseModel):
    """Structured output for ad optimization recommendations"""
    assessment: str = Field(description="Current performance assessment")
    budget_recommendation: str = Field(description="Budget allocation advice")
    targeting_suggestion: str = Field(description="Audience targeting improvements")
    action_priority: str = Field(description="Priority level: HIGH, MEDIUM, LOW")
    expected_impact: str = Field(description="Expected improvement from changes")
    confidence_score: float = Field(description="Confidence in recommendations (0-1)")


class BudgetSuggestion(BaseModel):
    """Budget reallocation suggestion"""
    campaign_id: str
    campaign_name: str
    current_budget: float
    suggested_budget: float
    change_percent: float
    reason: str


class UnderperformingCampaign(BaseModel):
    """Campaign flagged as underperforming"""
    campaign_id: str
    campaign_name: str
    sku_id: str
    platform: str
    roas: float
    target_roas: float
    issue: str
    suggested_action: str


@dataclass
class AdOptimizerAgent:
    """
    LangChain-powered Ad Optimization Agent
    
    Analyzes:
    - ROAS trends per SKU
    - Budget allocation efficiency
    - Platform performance comparison
    - Seasonal ad effectiveness (integrates with Seasonal Analyst)
    
    Provides:
    - Budget reallocation suggestions
    - Underperforming campaign alerts
    - Platform-specific recommendations
    - LLM-generated strategic insights
    """
    
    target_roas: float = 3.0  # Target 3x return
    min_roas_threshold: float = 1.5  # Minimum acceptable ROAS
    budget_change_limit: float = 0.5  # Max 50% budget change
    
    def __post_init__(self):
        """Initialize LangChain components if enabled"""
        if HAS_LANGCHAIN and hasattr(CFG, 'enable_ad_optimizer_llm'):
            self.has_llm = CFG.enable_ad_optimizer_llm and llm is not None
        elif HAS_LANGCHAIN and llm is not None:
            self.has_llm = True
        else:
            self.has_llm = False
    
    def analyze_campaign(self, campaign: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze a single campaign and provide recommendations
        """
        roas = campaign.get("roas", 0)
        ctr = campaign.get("ctr", 0)
        conv_rate = campaign.get("conversion_rate", 0)
        spend = campaign.get("total_spend_30d", 0)
        
        # Determine performance level
        if roas >= self.target_roas:
            performance = "EXCELLENT"
            action = "SCALE_UP"
        elif roas >= self.min_roas_threshold:
            performance = "GOOD"
            action = "MAINTAIN"
        elif roas > 0:
            performance = "UNDERPERFORMING"
            action = "OPTIMIZE"
        else:
            performance = "CRITICAL"
            action = "PAUSE_OR_REVAMP"
        
        # Identify specific issues
        issues = []
        if ctr < 1.0:
            issues.append("Low CTR - ad creative may need refresh")
        if conv_rate < 2.0:
            issues.append("Low conversion rate - landing page or targeting issue")
        if spend > 0 and roas < 1:
            issues.append("Negative ROI - losing money on ads")
        
        result = {
            "campaign_id": campaign.get("campaign_id"),
            "campaign_name": campaign.get("campaign_name"),
            "performance_level": performance,
            "recommended_action": action,
            "roas": roas,
            "roas_gap": round(self.target_roas - roas, 2),
            "issues": issues,
            "llm_insight": ""
        }
        
        # Add LLM insight for underperforming campaigns
        if self.has_llm and performance in ["UNDERPERFORMING", "CRITICAL"]:
            result["llm_insight"] = self._generate_campaign_insight(campaign)
        
        return result
    
    def _generate_campaign_insight(self, campaign: Dict[str, Any]) -> str:
        """Generate LLM insight for a campaign"""
        try:
            prompt = f"""You are an ad optimization expert. Analyze this campaign:

Campaign: {campaign.get('campaign_name')}
Platform: {campaign.get('platform')}
Product SKU: {campaign.get('sku_id')}
Spend (30d): ₹{campaign.get('total_spend_30d', 0):,.2f}
Impressions: {campaign.get('impressions_30d', 0):,}
Clicks: {campaign.get('clicks_30d', 0):,}
Conversions: {campaign.get('conversions_30d', 0)}
CTR: {campaign.get('ctr', 0):.2f}%
Conversion Rate: {campaign.get('conversion_rate', 0):.2f}%
ROAS: {campaign.get('roas', 0):.2f}x (Target: {self.target_roas}x)

Provide:
1) What's likely wrong (1 sentence)
2) Specific fix to try (1 sentence)
3) Expected improvement (1 sentence)

Be concise and actionable."""

            result = llm.invoke(prompt).content
            return result.strip()
            
        except Exception as e:
            print(f"[WARNING] LLM insight failed: {str(e)}")
            return ""
    
    def identify_underperforming_ads(self, campaigns: List[Dict[str, Any]]) -> List[UnderperformingCampaign]:
        """
        Identify campaigns that are underperforming
        """
        underperforming = []
        
        for campaign in campaigns:
            if campaign.get("status") != "ACTIVE":
                continue
                
            roas = campaign.get("roas", 0)
            
            if roas < self.min_roas_threshold:
                # Determine specific issue
                if roas < 1:
                    issue = "Negative ROI - spending more than earning"
                    action = "Pause campaign or reduce budget by 50%"
                elif campaign.get("ctr", 0) < 1:
                    issue = "Very low CTR - ads not engaging"
                    action = "Refresh ad creative and copy"
                elif campaign.get("conversion_rate", 0) < 1:
                    issue = "Low conversion rate - clicks not converting"
                    action = "Review landing page and product page"
                else:
                    issue = "Below target ROAS"
                    action = "Optimize targeting and reduce wasted spend"
                
                underperforming.append(UnderperformingCampaign(
                    campaign_id=campaign["campaign_id"],
                    campaign_name=campaign["campaign_name"],
                    sku_id=campaign["sku_id"],
                    platform=campaign["platform"],
                    roas=roas,
                    target_roas=self.target_roas,
                    issue=issue,
                    suggested_action=action
                ))
        
        # Sort by ROAS (worst first)
        underperforming.sort(key=lambda x: x.roas)
        
        return underperforming
    
    def suggest_budget_reallocation(self, campaigns: List[Dict[str, Any]]) -> List[BudgetSuggestion]:
        """
        Suggest budget reallocation based on performance
        """
        suggestions = []
        
        if not campaigns:
            return suggestions
        
        # Calculate average ROAS
        active_campaigns = [c for c in campaigns if c.get("status") == "ACTIVE"]
        if not active_campaigns:
            return suggestions
        
        avg_roas = np.mean([c.get("roas", 0) for c in active_campaigns])
        
        for campaign in active_campaigns:
            roas = campaign.get("roas", 0)
            current_budget = campaign.get("daily_budget", 0)
            
            if current_budget == 0:
                continue
            
            # Calculate suggested change
            if roas > avg_roas * 1.5 and roas >= self.target_roas:
                # High performer - increase budget
                change_percent = min(0.3, self.budget_change_limit)  # Up to 30% increase
                suggested_budget = current_budget * (1 + change_percent)
                reason = f"High performer with {roas:.1f}x ROAS - scale up"
            elif roas < self.min_roas_threshold:
                # Underperformer - decrease budget
                change_percent = -min(0.4, self.budget_change_limit)  # Up to 40% decrease
                suggested_budget = current_budget * (1 + change_percent)
                reason = f"Underperforming at {roas:.1f}x ROAS - reduce spend"
            else:
                continue  # No change needed
            
            if abs(change_percent) >= 0.1:  # Only suggest if change is significant
                suggestions.append(BudgetSuggestion(
                    campaign_id=campaign["campaign_id"],
                    campaign_name=campaign["campaign_name"],
                    current_budget=round(current_budget, 2),
                    suggested_budget=round(suggested_budget, 2),
                    change_percent=round(change_percent * 100, 1),
                    reason=reason
                ))
        
        # Sort by change magnitude
        suggestions.sort(key=lambda x: abs(x.change_percent), reverse=True)
        
        return suggestions
    
    def generate_optimization_report(self, campaigns: List[Dict[str, Any]], 
                                     summary: Dict[str, Any]) -> str:
        """
        Generate a comprehensive optimization report using LLM
        """
        if not self.has_llm:
            return self._generate_rule_based_report(campaigns, summary)
        
        try:
            # Prepare campaign summary
            active = [c for c in campaigns if c.get("status") == "ACTIVE"]
            high_performers = [c for c in active if c.get("roas", 0) >= self.target_roas]
            underperformers = [c for c in active if c.get("roas", 0) < self.min_roas_threshold]
            
            # Platform breakdown
            platform_stats = {}
            for c in active:
                p = c.get("platform", "UNKNOWN")
                if p not in platform_stats:
                    platform_stats[p] = {"spend": 0, "revenue": 0, "count": 0}
                platform_stats[p]["spend"] += c.get("total_spend_30d", 0)
                platform_stats[p]["revenue"] += c.get("revenue_30d", 0)
                platform_stats[p]["count"] += 1
            
            platform_summary = "\n".join([
                f"  {p}: {s['count']} campaigns, ₹{s['spend']:,.0f} spend, {s['revenue']/max(1,s['spend']):.1f}x ROAS"
                for p, s in platform_stats.items()
            ])
            
            prompt = f"""You are a digital marketing strategist. Provide an optimization report:

OVERALL METRICS:
- Total campaigns: {summary.get('total_campaigns', 0)}
- Active campaigns: {summary.get('active_campaigns', 0)}
- Total spend (30d): ₹{summary.get('total_spend_30d', 0):,.2f}
- Total revenue (30d): ₹{summary.get('total_revenue_30d', 0):,.2f}
- Average ROAS: {summary.get('avg_roas', 0):.2f}x

PERFORMANCE BREAKDOWN:
- High performers (ROAS ≥ {self.target_roas}x): {len(high_performers)}
- Underperformers (ROAS < {self.min_roas_threshold}x): {len(underperformers)}

PLATFORM BREAKDOWN:
{platform_summary}

Provide a concise report with:
1) Overall assessment (1-2 sentences)
2) Top 3 actionable recommendations
3) Priority focus area

Keep response under 200 words."""

            result = llm.invoke(prompt).content
            return result.strip()
            
        except Exception as e:
            print(f"[WARNING] LLM report failed: {str(e)}")
            return self._generate_rule_based_report(campaigns, summary)
    
    def _generate_rule_based_report(self, campaigns: List[Dict[str, Any]], 
                                    summary: Dict[str, Any]) -> str:
        """Generate a rule-based report when LLM is not available"""
        avg_roas = summary.get("avg_roas", 0)
        total_spend = summary.get("total_spend_30d", 0)
        
        report = "AD PERFORMANCE REPORT\n"
        report += "=" * 40 + "\n\n"
        
        if avg_roas >= self.target_roas:
            report += f"✅ Overall performance is GOOD (ROAS: {avg_roas:.1f}x)\n"
        elif avg_roas >= self.min_roas_threshold:
            report += f"⚠️ Overall performance is MODERATE (ROAS: {avg_roas:.1f}x)\n"
        else:
            report += f"❌ Overall performance needs IMPROVEMENT (ROAS: {avg_roas:.1f}x)\n"
        
        report += f"\nTotal Spend: ₹{total_spend:,.2f}\n"
        report += f"Campaigns: {summary.get('total_campaigns', 0)} total, {summary.get('active_campaigns', 0)} active\n"
        
        # Recommendations
        report += "\nRECOMMENDATIONS:\n"
        underperformers = self.identify_underperforming_ads(campaigns)
        if underperformers:
            report += f"1. Review {len(underperformers)} underperforming campaigns\n"
            report += f"2. Consider pausing lowest ROAS campaign: {underperformers[0].campaign_name}\n"
        
        suggestions = self.suggest_budget_reallocation(campaigns)
        if suggestions:
            report += f"3. Reallocate budget as suggested ({len(suggestions)} changes)\n"
        
        return report


# Standalone testing
if __name__ == "__main__":
    from ad_gateway import AdGateway
    
    print("=" * 60)
    print("AD OPTIMIZER TEST")
    print("=" * 60)
    
    # Load gateway and get campaigns
    gw = AdGateway()
    campaigns = [c.model_dump() for c in gw.get_campaigns()]
    summary = gw.get_summary().model_dump()
    
    print(f"\nLoaded {len(campaigns)} campaigns")
    
    # Initialize optimizer
    optimizer = AdOptimizerAgent()
    print(f"LLM Enabled: {optimizer.has_llm}")
    
    # Identify underperformers
    underperformers = optimizer.identify_underperforming_ads(campaigns)
    print(f"\nUnderperforming Campaigns: {len(underperformers)}")
    for up in underperformers[:3]:
        print(f"  - {up.campaign_name}: ROAS {up.roas}x ({up.issue})")
    
    # Budget suggestions
    suggestions = optimizer.suggest_budget_reallocation(campaigns)
    print(f"\nBudget Reallocation Suggestions: {len(suggestions)}")
    for s in suggestions[:3]:
        print(f"  - {s.campaign_name}: ₹{s.current_budget} → ₹{s.suggested_budget} ({s.change_percent:+.0f}%)")
    
    # Generate report
    print("\nGenerating optimization report...")
    report = optimizer.generate_optimization_report(campaigns, summary)
    print("\n" + report)
    
    print("\n" + "=" * 60)
    print("AD OPTIMIZER TEST COMPLETE")
    print("=" * 60)
