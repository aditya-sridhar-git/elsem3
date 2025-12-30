import React, { useState, useEffect } from 'react';
import { Megaphone, Play, Pause, BarChart2, Plus, DollarSign, Target } from 'lucide-react';
import { api } from '../services/api';
import type { AdMetricsSummary, AdCampaign } from '../types';

const AdsTab: React.FC = () => {
    const [metrics, setMetrics] = useState<AdMetricsSummary | null>(null);
    const [campaigns, setCampaigns] = useState<AdCampaign[]>([]);
    const [loading, setLoading] = useState(true);

    const fetchData = async () => {
        try {
            const [metricsData, campaignsData] = await Promise.all([
                api.getAdMetrics(),
                api.getAdCampaigns()
            ]);
            setMetrics(metricsData);
            setCampaigns(campaignsData.campaigns || []); // API returns { total: n, campaigns: [] }
        } catch (err) {
            console.error(err);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchData();
    }, []);

    const toggleCampaign = async (id: string, currentStatus: string) => {
        const action = currentStatus === 'ACTIVE' ? 'pause' : 'resume';
        try {
            await api.toggleCampaign(id, action);
            fetchData(); // Refresh list
        } catch (err) {
            console.error('Failed to toggle campaign', err);
        }
    };

    if (loading) {
        return <div className="p-12 text-center text-slate-400">Loading Ad Data...</div>;
    }

    if (!metrics || campaigns.length === 0) {
        return (
            <div className="glass-card p-12 text-center">
                <Megaphone className="w-16 h-16 text-slate-600 mx-auto mb-4" />
                <h3 className="text-xl font-semibold text-white mb-2">No Ad Campaigns Found</h3>
                <p className="text-slate-400 mb-6">Connect an ad platform using the API to get started.</p>
                <button className="px-4 py-2 bg-blue-600 rounded-lg text-white hover:bg-blue-700 transition">
                    Connect Platform
                </button>
            </div>
        );
    }

    return (
        <div className="space-y-6">
            {/* Metrics Overview */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
                <div className="glass-card p-6">
                    <div className="flex items-center gap-3 mb-2">
                        <Target className="w-5 h-5 text-blue-400" />
                        <h3 className="text-slate-400 text-sm font-medium">Active Campaigns</h3>
                    </div>
                    <p className="text-3xl font-bold text-white">{metrics.active_campaigns}</p>
                    <p className="text-xs text-slate-500 mt-1">Total: {metrics.total_campaigns}</p>
                </div>

                <div className="glass-card p-6">
                    <div className="flex items-center gap-3 mb-2">
                        <DollarSign className="w-5 h-5 text-emerald-400" />
                        <h3 className="text-slate-400 text-sm font-medium">30d Spend</h3>
                    </div>
                    <p className="text-3xl font-bold text-emerald-400">₹{metrics.total_spend_30d.toLocaleString()}</p>
                </div>

                <div className="glass-card p-6">
                    <div className="flex items-center gap-3 mb-2">
                        <BarChart2 className="w-5 h-5 text-purple-400" />
                        <h3 className="text-slate-400 text-sm font-medium">Avg ROAS</h3>
                    </div>
                    <p className="text-3xl font-bold text-purple-400">{metrics.avg_roas}x</p>
                </div>

                <div className="glass-card p-6 flex flex-col justify-center items-center">
                    <button className="flex items-center gap-2 px-4 py-3 bg-blue-600 hover:bg-blue-700 text-white rounded-lg w-full justify-center transition">
                        <Plus className="w-4 h-4" />
                        New Campaign
                    </button>
                </div>
            </div>

            {/* Campaign List */}
            <div className="glass-card overflow-hidden">
                <div className="p-6 border-b border-slate-700">
                    <h3 className="text-lg font-semibold text-white">Campaign Performance</h3>
                </div>
                <div className="overflow-x-auto">
                    <table className="w-full text-left">
                        <thead className="bg-slate-800/50">
                            <tr>
                                <th className="p-4 text-xs font-medium text-slate-400 uppercase">Status</th>
                                <th className="p-4 text-xs font-medium text-slate-400 uppercase">Campaign</th>
                                <th className="p-4 text-xs font-medium text-slate-400 uppercase">Platform</th>
                                <th className="p-4 text-xs font-medium text-slate-400 uppercase">Daily Budget</th>
                                <th className="p-4 text-xs font-medium text-slate-400 uppercase">ROAS</th>
                                <th className="p-4 text-xs font-medium text-slate-400 uppercase">Spend (30d)</th>
                                <th className="p-4 text-xs font-medium text-slate-400 uppercase">Action</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-700">
                            {campaigns.map((c) => (
                                <tr key={c.campaign_id} className="hover:bg-slate-700/30">
                                    <td className="p-4">
                                        <span className={`inline-flex items-center gap-1.5 px-2 py-1 rounded-full text-xs font-medium
                                            ${c.status === 'ACTIVE' ? 'bg-emerald-500/10 text-emerald-400' : 'bg-slate-500/10 text-slate-400'}`}>
                                            <span className={`w-1.5 h-1.5 rounded-full ${c.status === 'ACTIVE' ? 'bg-emerald-400' : 'bg-slate-400'}`}></span>
                                            {c.status}
                                        </span>
                                    </td>
                                    <td className="p-4 font-medium text-white">{c.campaign_name}</td>
                                    <td className="p-4 text-slate-400 text-sm">{c.platform}</td>
                                    <td className="p-4 text-white">₹{c.daily_budget}</td>
                                    <td className="p-4">
                                        <span className={`${c.roas >= 4 ? 'text-emerald-400' : c.roas >= 2 ? 'text-blue-400' : 'text-red-400'}`}>
                                            {c.roas}x
                                        </span>
                                    </td>
                                    <td className="p-4 text-slate-300">₹{c.total_spend_30d.toLocaleString()}</td>
                                    <td className="p-4">
                                        <button
                                            onClick={() => toggleCampaign(c.campaign_id, c.status)}
                                            className="p-1.5 hover:bg-slate-700 rounded-md text-slate-400 hover:text-white transition"
                                            title={c.status === 'ACTIVE' ? "Pause Campaign" : "Resume Campaign"}
                                        >
                                            {c.status === 'ACTIVE' ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4" />}
                                        </button>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    );
};

export default AdsTab;
