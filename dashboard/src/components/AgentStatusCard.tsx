import React from 'react';
import { Activity, TrendingUp, TrendingDown, AlertTriangle, CheckCircle } from 'lucide-react';
import type { Agent } from '../types';

interface AgentStatusCardProps {
    agent: Agent;
}

const AgentStatusCard: React.FC<AgentStatusCardProps> = ({ agent }) => {
    const getAgentIcon = (name: string) => {
        if (name.includes('Profit')) return TrendingUp;
        if (name.includes('Inventory')) return Activity;
        return CheckCircle;
    };

    const Icon = getAgentIcon(agent.name);

    // Extract key metrics based on agent type
    const renderMetrics = () => {
        if (agent.name === 'Profit Doctor') {
            return (
                <>
                    <div className="flex justify-between items-center">
                        <span className="text-slate-400 text-sm">Profitable SKUs</span>
                        <span className="text-emerald-400 font-semibold">{agent.metrics.profitable_skus || 0}</span>
                    </div>
                    <div className="flex justify-between items-center">
                        <span className="text-slate-400 text-sm">Loss Makers</span>
                        <span className="text-red-400 font-semibold">{agent.metrics.loss_makers || 0}</span>
                    </div>
                    <div className="flex justify-between items-center">
                        <span className="text-slate-400 text-sm">Avg Profit</span>
                        <span className={`font-semibold ${(agent.metrics.avg_profit || 0) > 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                            ₹{(agent.metrics.avg_profit || 0).toFixed(2)}
                        </span>
                    </div>
                </>
            );
        } else if (agent.name === 'Inventory Sentinel') {
            return (
                <>
                    <div className="flex justify-between items-center">
                        <span className="text-slate-400 text-sm flex items-center gap-1">
                            <span className="w-2 h-2 bg-red-500 rounded-full"></span>
                            Critical Risk
                        </span>
                        <span className="text-red-400 font-semibold">{agent.metrics.critical_risk || 0}</span>
                    </div>
                    <div className="flex justify-between items-center">
                        <span className="text-slate-400 text-sm flex items-center gap-1">
                            <span className="w-2 h-2 bg-yellow-500 rounded-full"></span>
                            Warning
                        </span>
                        <span className="text-yellow-400 font-semibold">{agent.metrics.warning_risk || 0}</span>
                    </div>
                    <div className="flex justify-between items-center">
                        <span className="text-slate-400 text-sm flex items-center gap-1">
                            <span className="w-2 h-2 bg-emerald-500 rounded-full"></span>
                            Safe
                        </span>
                        <span className="text-emerald-400 font-semibold">{agent.metrics.safe || 0}</span>
                    </div>
                </>
            );
        } else if (agent.name === 'Strategy Supervisor') {
            const actionCount = Object.keys(agent.metrics.action_distribution || {}).length;
            return (
                <>
                    <div className="flex justify-between items-center">
                        <span className="text-slate-400 text-sm">Total Actions</span>
                        <span className="text-blue-400 font-semibold">{actionCount}</span>
                    </div>
                    <div className="flex justify-between items-center">
                        <span className="text-slate-400 text-sm">Avg Impact</span>
                        <span className="text-purple-400 font-semibold">
                            {(agent.metrics.avg_impact_score || 0).toFixed(2)}
                        </span>
                    </div>
                </>
            );
        }
    };

    return (
        <div className="glass-card p-6 fade-in hover:scale-105 transition-transform duration-200">
            <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold text-white flex items-center gap-2">
                    <Icon className="w-5 h-5 text-blue-400" />
                    {agent.name}
                </h3>
                <span className={`px-3 py-1 rounded-full text-xs font-medium ${agent.status === 'completed'
                        ? 'bg-emerald-500/20 text-emerald-400'
                        : 'bg-yellow-500/20 text-yellow-400'
                    }`}>
                    {agent.status}
                </span>
            </div>
            <div className="space-y-3">
                {renderMetrics()}
            </div>
        </div>
    );
};

export default AgentStatusCard;
