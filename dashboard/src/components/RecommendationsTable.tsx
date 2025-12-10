import React, { useState } from 'react';
import { ArrowUpDown, AlertCircle, ChevronDown, ChevronUp, Sparkles } from 'lucide-react';
import type { SKURecommendation } from '../types';

interface RecommendationsTableProps {
    recommendations: SKURecommendation[];
}

const RecommendationsTable: React.FC<RecommendationsTableProps> = ({ recommendations }) => {
    const [sortBy, setSortBy] = useState<keyof SKURecommendation>('impact_score');
    const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc');
    const [expandedRows, setExpandedRows] = useState<Set<string>>(new Set());

    const handleSort = (field: keyof SKURecommendation) => {
        if (sortBy === field) {
            setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
        } else {
            setSortBy(field);
            setSortOrder('desc');
        }
    };

    const toggleRow = (skuId: string) => {
        const newExpanded = new Set(expandedRows);
        if (newExpanded.has(skuId)) {
            newExpanded.delete(skuId);
        } else {
            newExpanded.add(skuId);
        }
        setExpandedRows(newExpanded);
    };

    const sortedRecommendations = [...recommendations].sort((a, b) => {
        const aVal = a[sortBy];
        const bVal = b[sortBy];

        if (typeof aVal === 'number' && typeof bVal === 'number') {
            return sortOrder === 'asc' ? aVal - bVal : bVal - aVal;
        }

        return sortOrder === 'asc'
            ? String(aVal).localeCompare(String(bVal))
            : String(bVal).localeCompare(String(aVal));
    });

    const getRiskBadgeColor = (risk: string) => {
        switch (risk) {
            case 'CRITICAL': return 'bg-red-500/20 text-red-400 border-red-500/50';
            case 'WARNING': return 'bg-yellow-500/20 text-yellow-400 border-yellow-500/50';
            case 'SAFE': return 'bg-emerald-500/20 text-emerald-400 border-emerald-500/50';
            default: return 'bg-slate-500/20 text-slate-400 border-slate-500/50';
        }
    };

    const getActionBadgeColor = (action: string) => {
        if (action.includes('PAUSE') || action.includes('INCREASE_PRICE')) {
            return 'bg-red-500/20 text-red-400 border-red-500/50';
        }
        if (action.includes('REORDER_IMMEDIATELY')) {
            return 'bg-orange-500/20 text-orange-400 border-orange-500/50';
        }
        if (action.includes('PLAN_REORDER')) {
            return 'bg-yellow-500/20 text-yellow-400 border-yellow-500/50';
        }
        if (action.includes('DISCOUNT')) {
            return 'bg-purple-500/20 text-purple-400 border-purple-500/50';
        }
        return 'bg-blue-500/20 text-blue-400 border-blue-500/50';
    };

    const hasLLMInsights = (rec: SKURecommendation) => {
        return !!(rec.llm_profit_insight || rec.llm_inventory_insight || rec.llm_strategy_insight);
    };

    const SortButton: React.FC<{ field: keyof SKURecommendation; label: string }> = ({ field, label }) => (
        <button
            onClick={() => handleSort(field)}
            className="flex items-center gap-1 hover:text-blue-400 transition-colors"
        >
            {label}
            <ArrowUpDown className="w-3 h-3" />
        </button>
    );

    return (
        <div className="glass-card p-6 fade-in overflow-hidden">
            <h3 className="text-xl font-semibold text-white mb-4 flex items-center gap-2">
                <AlertCircle className="w-5 h-5 text-blue-400" />
                Agent Recommendations
                {recommendations.some(hasLLMInsights) && (
                    <span className="ml-2 flex items-center gap-1 px-2 py-0.5 bg-purple-500/20 text-purple-300 text-xs rounded-full border border-purple-500/30">
                        <Sparkles className="w-3 h-3" />
                        AI Insights
                    </span>
                )}
            </h3>

            <div className="overflow-x-auto">
                <table className="w-full">
                    <thead>
                        <tr className="border-b border-slate-700">
                            <th className="w-8"></th>
                            <th className="text-left py-3 px-4 text-sm font-medium text-slate-300">
                                <SortButton field="sku_id" label="SKU" />
                            </th>
                            <th className="text-left py-3 px-4 text-sm font-medium text-slate-300">
                                Product
                            </th>
                            <th className="text-left py-3 px-4 text-sm font-medium text-slate-300">
                                <SortButton field="category" label="Category" />
                            </th>
                            <th className="text-right py-3 px-4 text-sm font-medium text-slate-300">
                                <SortButton field="profit_per_unit" label="Profit/Unit" />
                            </th>
                            <th className="text-right py-3 px-4 text-sm font-medium text-slate-300">
                                <SortButton field="current_stock" label="Stock" />
                            </th>
                            <th className="text-center py-3 px-4 text-sm font-medium text-slate-300">
                                <SortButton field="risk_level" label="Risk" />
                            </th>
                            <th className="text-right py-3 px-4 text-sm font-medium text-slate-300">
                                <SortButton field="impact_score" label="Impact" />
                            </th>
                            <th className="text-left py-3 px-4 text-sm font-medium text-slate-300">
                                Action
                            </th>
                        </tr>
                    </thead>
                    <tbody>
                        {sortedRecommendations.map((rec, index) => (
                            <React.Fragment key={rec.sku_id}>
                                <tr
                                    className="border-b border-slate-800 hover:bg-slate-800/30 transition-colors cursor-pointer"
                                    style={{ animationDelay: `${index * 50}ms` }}
                                    onClick={() => hasLLMInsights(rec) && toggleRow(rec.sku_id)}
                                >
                                    <td className="py-3 px-4">
                                        {hasLLMInsights(rec) && (
                                            <button className="text-slate-400 hover:text-purple-400 transition-colors">
                                                {expandedRows.has(rec.sku_id) ? (
                                                    <ChevronUp className="w-4 h-4" />
                                                ) : (
                                                    <ChevronDown className="w-4 h-4" />
                                                )}
                                            </button>
                                        )}
                                    </td>
                                    <td className="py-3 px-4 text-sm font-medium text-blue-400">
                                        {rec.sku_id}
                                    </td>
                                    <td className="py-3 px-4 text-sm text-slate-200 max-w-xs truncate">
                                        <div className="flex items-center gap-2">
                                            {rec.product_name}
                                            {hasLLMInsights(rec) && (
                                                <Sparkles className="w-3 h-3 text-purple-400" />
                                            )}
                                        </div>
                                    </td>
                                    <td className="py-3 px-4 text-sm text-slate-300">
                                        {rec.category}
                                    </td>
                                    <td className={`py-3 px-4 text-sm text-right font-medium ${rec.profit_per_unit > 0 ? 'text-emerald-400' : 'text-red-400'
                                        }`}>
                                        ₹{rec.profit_per_unit.toFixed(2)}
                                    </td>
                                    <td className="py-3 px-4 text-sm text-right text-slate-300">
                                        {rec.current_stock}
                                    </td>
                                    <td className="py-3 px-4 text-center">
                                        <span className={`px-2 py-1 rounded-full text-xs font-medium border ${getRiskBadgeColor(rec.risk_level)}`}>
                                            {rec.risk_level}
                                        </span>
                                    </td>
                                    <td className="py-3 px-4 text-sm text-right font-semibold text-purple-400">
                                        {rec.impact_score.toFixed(2)}
                                    </td>
                                    <td className="py-3 px-4">
                                        <span className={`px-2 py-1 rounded-full text-xs font-medium border ${getActionBadgeColor(rec.recommended_action)}`}>
                                            {rec.recommended_action.replace(/_/g, ' ')}
                                        </span>
                                    </td>
                                </tr>

                                {/* LLM Insights Expanded Row */}
                                {expandedRows.has(rec.sku_id) && hasLLMInsights(rec) && (
                                    <tr className="border-b border-slate-800 bg-slate-900/50">
                                        <td colSpan={9} className="py-4 px-6">
                                            <div className="space-y-4">
                                                <div className="flex items-center gap-2 mb-3">
                                                    <Sparkles className="w-4 h-4 text-purple-400" />
                                                    <h4 className="text-sm font-semibold text-purple-300">
                                                        LangChain AI Insights
                                                    </h4>
                                                </div>

                                                <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
                                                    {rec.llm_profit_insight && (
                                                        <div className="bg-gradient-to-br from-blue-500/10 to-cyan-500/10 border border-blue-500/20 rounded-lg p-4">
                                                            <div className="flex items-center gap-2 mb-2">
                                                                <div className="w-2 h-2 bg-blue-400 rounded-full"></div>
                                                                <h5 className="text-xs font-semibold text-blue-300">Profit Analysis</h5>
                                                                {rec.llm_profit_confidence && (
                                                                    <span className="text-xs text-slate-400">
                                                                        ({(rec.llm_profit_confidence * 100).toFixed(0)}% confidence)
                                                                    </span>
                                                                )}
                                                            </div>
                                                            <p className="text-xs text-slate-300 leading-relaxed">
                                                                {rec.llm_profit_insight}
                                                            </p>
                                                        </div>
                                                    )}

                                                    {rec.llm_inventory_insight && (
                                                        <div className="bg-gradient-to-br from-emerald-500/10 to-teal-500/10 border border-emerald-500/20 rounded-lg p-4">
                                                            <div className="flex items-center gap-2 mb-2">
                                                                <div className="w-2 h-2 bg-emerald-400 rounded-full"></div>
                                                                <h5 className="text-xs font-semibold text-emerald-300">Inventory Strategy</h5>
                                                                {rec.llm_inventory_confidence && (
                                                                    <span className="text-xs text-slate-400">
                                                                        ({(rec.llm_inventory_confidence * 100).toFixed(0)}% confidence)
                                                                    </span>
                                                                )}
                                                            </div>
                                                            <p className="text-xs text-slate-300 leading-relaxed">
                                                                {rec.llm_inventory_insight}
                                                            </p>
                                                        </div>
                                                    )}

                                                    {rec.llm_strategy_insight && (
                                                        <div className="bg-gradient-to-br from-purple-500/10 to-pink-500/10 border border-purple-500/20 rounded-lg p-4">
                                                            <div className="flex items-center gap-2 mb-2">
                                                                <div className="w-2 h-2 bg-purple-400 rounded-full"></div>
                                                                <h5 className="text-xs font-semibold text-purple-300">Strategic Recommendation</h5>
                                                                {rec.llm_strategy_confidence && (
                                                                    <span className="text-xs text-slate-400">
                                                                        ({(rec.llm_strategy_confidence * 100).toFixed(0)}% confidence)
                                                                    </span>
                                                                )}
                                                            </div>
                                                            <p className="text-xs text-slate-300 leading-relaxed">
                                                                {rec.llm_strategy_insight}
                                                            </p>
                                                        </div>
                                                    )}
                                                </div>

                                                <div className="mt-3 pt-3 border-t border-slate-700/50 text-xs text-slate-500">
                                                    <span className="flex items-center gap-1">
                                                        <span className="w-1.5 h-1.5 bg-purple-500 rounded-full animate-pulse"></span>
                                                        Powered by LangChain + Groq (Mixtral 8x7B)
                                                    </span>
                                                </div>
                                            </div>
                                        </td>
                                    </tr>
                                )}
                            </React.Fragment>
                        ))}
                    </tbody>
                </table>
            </div>

            {recommendations.length === 0 && (
                <div className="text-center py-12 text-slate-400">
                    No recommendations available
                </div>
            )}
        </div>
    );
};

export default RecommendationsTable;
