import React, { useState, useEffect } from 'react';
import { RefreshCw, TrendingUp, TrendingDown, AlertTriangle, Activity, Bell } from 'lucide-react';
import AgentStatusCard from './AgentStatusCard';
import MetricsChart from './MetricsChart';
import RecommendationsTable from './RecommendationsTable';
import AlertsTab from './AlertsTab';
import SeasonalTab from './SeasonalTab';
import AdsTab from './AdsTab';
import { api } from '../services/api';
import type { AgentStatusResponse, MetricsSummary, SKURecommendation } from '../types';

type Tab = 'overview' | 'alerts' | 'seasonal' | 'ads';

const Dashboard: React.FC = () => {
    const [activeTab, setActiveTab] = useState<Tab>('overview');
    const [agentStatus, setAgentStatus] = useState<AgentStatusResponse | null>(null);
    const [metrics, setMetrics] = useState<MetricsSummary | null>(null);
    const [recommendations, setRecommendations] = useState<SKURecommendation[]>([]);
    const [loading, setLoading] = useState(true);
    const [refreshing, setRefreshing] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const fetchData = async (isRefresh = false) => {
        try {
            if (isRefresh) setRefreshing(true);
            else setLoading(true);

            setError(null);

            const [statusData, metricsData, recsData] = await Promise.all([
                api.getAgentStatus(),
                api.getMetricsSummary(),
                api.getRecommendations(),
            ]);

            setAgentStatus(statusData);
            setMetrics(metricsData);
            setRecommendations(recsData);
        } catch (err: any) {
            console.error('Error fetching data:', err);
            setError(err.message || 'Failed to fetch data');
        } finally {
            setLoading(false);
            setRefreshing(false);
        }
    };

    const handleRefresh = async () => {
        try {
            setRefreshing(true);
            await api.runAgents();
            await fetchData(true);
        } catch (err: any) {
            setError(err.message || 'Failed to refresh data');
            setRefreshing(false);
        }
    };

    useEffect(() => {
        fetchData();

        // Auto-refresh every 30 seconds
        const interval = setInterval(() => fetchData(true), 30000);
        return () => clearInterval(interval);
    }, []);

    if (loading) {
        return (
            <div className="min-h-screen flex items-center justify-center">
                <div className="text-center">
                    <div className="animate-spin rounded-full h-16 w-16 border-t-2 border-b-2 border-blue-500 mx-auto mb-4"></div>
                    <p className="text-slate-400">Loading dashboard...</p>
                </div>
            </div>
        );
    }

    if (error && !metrics) {
        return (
            <div className="min-h-screen flex items-center justify-center">
                <div className="glass-card p-8 text-center max-w-md">
                    <AlertTriangle className="w-16 h-16 text-red-400 mx-auto mb-4" />
                    <h3 className="text-xl font-semibold text-white mb-2">Error Loading Data</h3>
                    <p className="text-slate-400 mb-4">{error}</p>
                    <button
                        onClick={() => fetchData()}
                        className="px-6 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors"
                    >
                        Retry
                    </button>
                </div>
            </div>
        );
    }

    return (
        <div className="min-h-screen p-6">
            <div className="max-w-7xl mx-auto">
                {/* Header */}
                <div className="mb-8">
                    <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-6">
                        <div className="flex items-center gap-4">
                            <h1 className="text-4xl font-bold bg-gradient-to-r from-blue-400 to-purple-500 bg-clip-text text-transparent">
                                Agent Dashboard
                            </h1>
                            {/* LangChain Indicator */}
                            {recommendations.some(r => r.llm_profit_insight || r.llm_inventory_insight || r.llm_strategy_insight) && (
                                <div className="flex items-center gap-2 px-3 py-1.5 bg-gradient-to-r from-purple-600/20 to-pink-600/20 border border-purple-500/30 rounded-full">
                                    <div className="relative flex h-2 w-2">
                                        <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-purple-400 opacity-75"></span>
                                        <span className="relative inline-flex rounded-full h-2 w-2 bg-purple-500"></span>
                                    </div>
                                    <span className="text-xs font-medium text-purple-300">
                                        Active
                                    </span>
                                </div>
                            )}
                        </div>
                        <div className="flex items-center gap-3">
                            <div className="flex p-1 bg-slate-800/50 rounded-lg border border-slate-700">
                                <button
                                    onClick={() => setActiveTab('overview')}
                                    className={`px-4 py-1.5 rounded-md text-sm font-medium transition-all ${activeTab === 'overview'
                                        ? 'bg-blue-600 text-white shadow-lg'
                                        : 'text-slate-400 hover:text-white'
                                        }`}
                                >
                                    Overview
                                </button>
                                <button
                                    onClick={() => setActiveTab('alerts')}
                                    className={`px-4 py-1.5 rounded-md text-sm font-medium transition-all flex items-center gap-2 ${activeTab === 'alerts'
                                        ? 'bg-blue-600 text-white shadow-lg'
                                        : 'text-slate-400 hover:text-white'
                                        }`}
                                >
                                    <Bell className="w-4 h-4" />
                                    Alerts
                                    {metrics && (metrics.total_critical_risk > 0 || metrics.total_loss_makers > 0) && (
                                        <span className="flex h-2 w-2 relative">
                                            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-red-400 opacity-75"></span>
                                            <span className="relative inline-flex rounded-full h-2 w-2 bg-red-500"></span>
                                        </span>
                                    )}
                                </button>
                                <button
                                    onClick={() => setActiveTab('seasonal')}
                                    className={`px-4 py-1.5 rounded-md text-sm font-medium transition-all ${activeTab === 'seasonal'
                                        ? 'bg-blue-600 text-white shadow-lg'
                                        : 'text-slate-400 hover:text-white'
                                        }`}
                                >
                                    Seasonal
                                </button>
                                <button
                                    onClick={() => setActiveTab('ads')}
                                    className={`px-4 py-1.5 rounded-md text-sm font-medium transition-all ${activeTab === 'ads'
                                        ? 'bg-purple-600 text-white shadow-lg'
                                        : 'text-slate-400 hover:text-white'
                                        }`}
                                >
                                    Ads
                                </button>
                            </div>
                            <button
                                onClick={handleRefresh}
                                disabled={refreshing}
                                className="flex items-center gap-2 px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 rounded-lg transition-colors"
                            >
                                <RefreshCw className={`w-4 h-4 ${refreshing ? 'animate-spin' : ''}`} />
                            </button>
                        </div>
                    </div>
                </div>

                {activeTab === 'overview' ? (
                    <div className="animate-in fade-in duration-300">
                        {/* Overview Cards */}
                        {metrics && (
                            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
                                <div className="glass-card p-6 fade-in pulse-glow">
                                    <div className="flex items-center justify-between mb-2">
                                        <span className="text-slate-400 text-sm">Total SKUs</span>
                                        <Activity className="w-5 h-5 text-blue-400" />
                                    </div>
                                    <p className="text-3xl font-bold text-white">{metrics.total_skus}</p>
                                </div>

                                <div className="glass-card p-6 fade-in">
                                    <div className="flex items-center justify-between mb-2">
                                        <span className="text-slate-400 text-sm">Profitable</span>
                                        <TrendingUp className="w-5 h-5 text-emerald-400" />
                                    </div>
                                    <p className="text-3xl font-bold text-emerald-400">{metrics.total_profitable}</p>
                                    <p className="text-xs text-slate-500 mt-1">
                                        Avg: ₹{metrics.avg_profit_per_unit.toFixed(2)}
                                    </p>
                                </div>

                                <div className="glass-card p-6 fade-in">
                                    <div className="flex items-center justify-between mb-2">
                                        <span className="text-slate-400 text-sm">Loss Makers</span>
                                        <TrendingDown className="w-5 h-5 text-red-400" />
                                    </div>
                                    <p className="text-3xl font-bold text-red-400">{metrics.total_loss_makers}</p>
                                    <p className="text-xs text-slate-500 mt-1">
                                        Daily Loss: ₹{metrics.total_daily_loss.toFixed(2)}
                                    </p>
                                </div>

                                <div className="glass-card p-6 fade-in">
                                    <div className="flex items-center justify-between mb-2">
                                        <span className="text-slate-400 text-sm">Critical Risk</span>
                                        <AlertTriangle className="w-5 h-5 text-red-400" />
                                    </div>
                                    <p className="text-3xl font-bold text-red-400">{metrics.total_critical_risk}</p>
                                    <p className="text-xs text-slate-500 mt-1">
                                        Warning: {metrics.total_warning_risk}
                                    </p>
                                </div>
                            </div>
                        )}

                        {/* Agent Status Cards */}
                        {agentStatus && agentStatus.agents && (
                            <div className="mb-8">
                                <h2 className="text-2xl font-semibold text-white mb-4">Agent Status</h2>
                                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                                    {agentStatus.agents.map((agent) => (
                                        <AgentStatusCard key={agent.name} agent={agent} />
                                    ))}
                                </div>
                            </div>
                        )}

                        {/* Charts */}
                        {metrics && recommendations.length > 0 && (
                            <div className="mb-8">
                                <h2 className="text-2xl font-semibold text-white mb-4">Analytics</h2>
                                <MetricsChart metrics={metrics} recommendations={recommendations} />
                            </div>
                        )}

                        {/* Recommendations Table */}
                        {recommendations.length > 0 && (
                            <RecommendationsTable recommendations={recommendations} />
                        )}
                    </div>
                ) : activeTab === 'alerts' ? (
                    <div className="animate-in fade-in duration-300">
                        <AlertsTab />
                    </div>
                ) : activeTab === 'seasonal' ? (
                    <div className="animate-in fade-in duration-300">
                        <SeasonalTab />
                    </div>
                ) : (
                    <div className="animate-in fade-in duration-300">
                        <AdsTab />
                    </div>
                )}

                {/* Error Banner */}
                {error && (
                    <div className="fixed bottom-4 right-4 glass-card p-4 border-l-4 border-red-500 max-w-md">
                        <div className="flex items-start gap-3">
                            <AlertTriangle className="w-5 h-5 text-red-400 flex-shrink-0 mt-0.5" />
                            <div>
                                <p className="text-sm font-medium text-white">Error</p>
                                <p className="text-sm text-slate-400">{error}</p>
                            </div>
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
};

export default Dashboard;
