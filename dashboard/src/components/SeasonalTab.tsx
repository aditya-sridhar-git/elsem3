import React, { useState, useEffect } from 'react';
import { Calendar, TrendingUp, TrendingDown, Sun, AlertTriangle, CloudRain } from 'lucide-react';
import { api } from '../services/api';
import type { SeasonalResponse, SeasonalAnalysis } from '../types';

const SeasonalTab: React.FC = () => {
    const [data, setData] = useState<SeasonalResponse | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        const fetchData = async () => {
            try {
                const response = await api.getSeasonalAnalysis();
                setData(response);
            } catch (err: any) {
                setError(err.message || 'Failed to fetch seasonal analysis');
            } finally {
                setLoading(false);
            }
        };

        fetchData();
    }, []);

    if (loading) {
        return (
            <div className="flex items-center justify-center h-64">
                <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-500"></div>
            </div>
        );
    }

    if (error) {
        return (
            <div className="glass-card p-6 text-center">
                <AlertTriangle className="w-12 h-12 text-red-400 mx-auto mb-4" />
                <h3 className="text-xl font-semibold text-white mb-2">Error</h3>
                <p className="text-slate-400">{error}</p>
            </div>
        );
    }

    if (!data || data.status === 'disabled') {
        return (
            <div className="glass-card p-12 text-center">
                <Calendar className="w-16 h-16 text-slate-600 mx-auto mb-4" />
                <h3 className="text-xl font-semibold text-white mb-2">Seasonal Analysis Unavailable</h3>
                <p className="text-slate-400">Run the pipeline with sales history to generate seasonal insights.</p>
            </div>
        );
    }

    const { analysis, strong_seasonality_count, seasonal_risk_count } = data;

    return (
        <div className="space-y-6">
            {/* Summary Cards */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div className="glass-card p-6">
                    <div className="flex items-center gap-3 mb-2">
                        <TrendingUp className="w-5 h-5 text-purple-400" />
                        <h3 className="text-slate-400 text-sm font-medium">Strong Seasonality</h3>
                    </div>
                    <p className="text-3xl font-bold text-white">{strong_seasonality_count}</p>
                    <p className="text-xs text-slate-500 mt-1">Products with {'>'}0.3 strength</p>
                </div>

                <div className="glass-card p-6">
                    <div className="flex items-center gap-3 mb-2">
                        <AlertTriangle className="w-5 h-5 text-amber-400" />
                        <h3 className="text-slate-400 text-sm font-medium">Seasonal Risks</h3>
                    </div>
                    <p className="text-3xl font-bold text-amber-400">{seasonal_risk_count}</p>
                    <p className="text-xs text-slate-500 mt-1">High stock entering low season</p>
                </div>

                <div className="glass-card p-6">
                    <div className="flex items-center gap-3 mb-2">
                        <Calendar className="w-5 h-5 text-blue-400" />
                        <h3 className="text-slate-400 text-sm font-medium">Total Analyzed</h3>
                    </div>
                    <p className="text-3xl font-bold text-white">{data.total_skus}</p>
                    <p className="text-xs text-slate-500 mt-1">SKUs in catalog</p>
                </div>
            </div>

            {/* Analysis List */}
            <div className="glass-card overflow-hidden">
                <div className="p-6 border-b border-slate-700">
                    <h3 className="text-lg font-semibold text-white">Seasonal Trends</h3>
                </div>
                <div className="overflow-x-auto">
                    <table className="w-full text-left">
                        <thead className="bg-slate-800/50">
                            <tr>
                                <th className="p-4 text-xs font-medium text-slate-400 uppercase tracking-wider">Product</th>
                                <th className="p-4 text-xs font-medium text-slate-400 uppercase tracking-wider">Trend</th>
                                <th className="p-4 text-xs font-medium text-slate-400 uppercase tracking-wider">Strength</th>
                                <th className="p-4 text-xs font-medium text-slate-400 uppercase tracking-wider">Peak / Trough</th>
                                <th className="p-4 text-xs font-medium text-slate-400 uppercase tracking-wider">Next Index</th>
                                <th className="p-4 text-xs font-medium text-slate-400 uppercase tracking-wider">Insight</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-700">
                            {analysis.map((item: SeasonalAnalysis) => (
                                <tr key={item.sku_id} className="hover:bg-slate-700/30 transition-colors">
                                    <td className="p-4">
                                        <div className="font-medium text-white">{item.product_name}</div>
                                        <div className="text-xs text-slate-500">{item.category}</div>
                                    </td>
                                    <td className="p-4">
                                        <div className={`inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium
                                            ${item.seasonal_trend === 'RISING' ? 'bg-emerald-500/10 text-emerald-400' :
                                                item.seasonal_trend === 'FALLING' ? 'bg-red-500/10 text-red-400' :
                                                    'bg-slate-500/10 text-slate-400'}`}>
                                            {item.seasonal_trend === 'RISING' && <TrendingUp className="w-3 h-3" />}
                                            {item.seasonal_trend === 'FALLING' && <TrendingDown className="w-3 h-3" />}
                                            {item.seasonal_trend}
                                        </div>
                                    </td>
                                    <td className="p-4">
                                        <div className="flex items-center gap-2">
                                            <div className="w-16 h-1.5 bg-slate-700 rounded-full overflow-hidden">
                                                <div
                                                    className={`h-full rounded-full ${item.seasonality_strength > 0.5 ? 'bg-purple-500' : 'bg-blue-500'}`}
                                                    style={{ width: `${Math.min(item.seasonality_strength * 100, 100)}%` }}
                                                />
                                            </div>
                                            <span className="text-xs text-slate-400">{item.seasonality_strength.toFixed(2)}</span>
                                        </div>
                                    </td>
                                    <td className="p-4">
                                        <div className="flex flex-col gap-1 text-xs">
                                            <span className="text-emerald-400 flex items-center gap-1">
                                                <Sun className="w-3 h-3" /> {item.peak_month}
                                            </span>
                                            <span className="text-red-400 flex items-center gap-1">
                                                <CloudRain className="w-3 h-3" /> {item.trough_month}
                                            </span>
                                        </div>
                                    </td>
                                    <td className="p-4">
                                        <span className={`text-sm font-medium ${item.seasonal_index_next > 1.0 ? 'text-emerald-400' : 'text-slate-400'}`}>
                                            {item.seasonal_index_next.toFixed(2)}x
                                        </span>
                                    </td>
                                    <td className="p-4">
                                        {item.llm_seasonal_insight ? (
                                            <div className="flex items-start gap-2 max-w-xs">
                                                <span className="text-xs text-slate-300 italic">"{item.llm_seasonal_insight}"</span>
                                            </div>
                                        ) : (
                                            <span className="text-xs text-slate-600">-</span>
                                        )}
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

export default SeasonalTab;
