import React, { useState, useEffect } from 'react';
import { AlertTriangle, Check, X, ArrowRight, DollarSign, Package } from 'lucide-react';
import type { Alert } from '../types';
import { api } from '../services/api';

const AlertsTab: React.FC = () => {
    const [alerts, setAlerts] = useState<Alert[]>([]);
    const [loading, setLoading] = useState(true);
    const [processingId, setProcessingId] = useState<string | null>(null);
    const [actionModal, setActionModal] = useState<{ alert: Alert, type: 'RESTOCK' | 'PRICE' } | null>(null);
    const [inputValue, setInputValue] = useState<number>(0);

    const fetchAlerts = async () => {
        try {
            const data = await api.getAlerts();
            setAlerts(data);
        } catch (err) {
            console.error("Failed to fetch alerts", err);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchAlerts();
    }, []);

    const handleDismiss = async (skuId: string) => {
        setProcessingId(skuId);
        try {
            await api.executeAction(skuId, 'DISMISS');
            setAlerts(prev => prev.filter(a => a.sku_id !== skuId));
        } catch (err) {
            console.error("Failed to dismiss alert", err);
        } finally {
            setProcessingId(null);
        }
    };

    const openActionModal = (alert: Alert) => {
        const isPrice = alert.recommended_action.includes("PRICE") || alert.recommended_action.includes("DISCOUNT");

        let type: 'RESTOCK' | 'PRICE' = 'RESTOCK';
        let initialValue = 0;

        if (isPrice) {
            type = 'PRICE';
            initialValue = alert.suggested_price || alert.selling_price;
        } else {
            // Default to restock if unclear, or specific logic
            type = 'RESTOCK';
            initialValue = alert.suggested_reorder || 50;
        }

        setActionModal({ alert, type });
        setInputValue(initialValue);
    };

    const confirmAction = async () => {
        if (!actionModal) return;

        setProcessingId(actionModal.alert.sku_id);
        const actionType = actionModal.type === 'RESTOCK' ? 'RESTOCK' : 'PRICE_CHANGE';

        try {
            await api.executeAction(
                actionModal.alert.sku_id,
                actionType,
                Number(inputValue),
                actionModal.type === 'PRICE' ? actionModal.alert.selling_price : undefined
            );
            // Remove from list upon success
            setAlerts(prev => prev.filter(a => a.sku_id !== actionModal.alert.sku_id));
            setActionModal(null);
        } catch (err) {
            console.error("Failed to execute action", err);
        } finally {
            setProcessingId(null);
        }
    };

    if (loading) return <div className="text-center p-8 text-slate-400">Loading alerts...</div>;

    if (alerts.length === 0) {
        return (
            <div className="text-center p-12 glass-card">
                <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-emerald-500/20 mb-4">
                    <Check className="w-8 h-8 text-emerald-400" />
                </div>
                <h3 className="text-xl font-semibold text-white mb-2">All Clear!</h3>
                <p className="text-slate-400">No critical alerts requiring attention right now.</p>
            </div>
        );
    }

    return (
        <div className="space-y-4">
            {alerts.map(alert => (
                <div key={alert.sku_id} className="glass-card p-6 flex flex-col md:flex-row items-start md:items-center justify-between gap-4 fade-in">
                    <div className="flex items-start gap-4">
                        <div className={`p-3 rounded-lg ${alert.risk_level === 'CRITICAL' ? 'bg-red-500/20 text-red-300' :
                            alert.risk_level === 'WARNING' ? 'bg-amber-500/20 text-amber-300' :
                                'bg-blue-500/20 text-blue-300'
                            }`}>
                            <AlertTriangle className="w-6 h-6" />
                        </div>
                        <div>
                            <div className="flex items-center gap-2 mb-1">
                                <h3 className="font-semibold text-white text-lg">{alert.product_name}</h3>
                                <span className="text-xs px-2 py-0.5 rounded bg-slate-700 text-slate-300 font-mono">
                                    {alert.sku_id.split('_').pop()}
                                </span>
                            </div>
                            <p className="text-slate-300 text-sm mb-2">
                                <span className={alert.risk_level === 'CRITICAL' ? 'text-red-400 font-medium' : 'text-amber-400'}>
                                    {alert.risk_level} Risk
                                </span> • {alert.recommended_action.replace(/_/g, ' ')}
                            </p>
                            <div className="flex items-center gap-4 text-sm text-slate-400">
                                <span>Stock: {alert.current_stock}</span>
                                <span>Price: ₹{alert.selling_price}</span>
                                <span>Impact: {alert.impact_score.toFixed(0)}</span>
                            </div>
                        </div>
                    </div>

                    <div className="flex items-center gap-3 w-full md:w-auto">
                        <button
                            onClick={() => handleDismiss(alert.sku_id)}
                            disabled={!!processingId}
                            className="flex-1 md:flex-none px-4 py-2 border border-slate-600 hover:bg-slate-700 text-slate-300 rounded-lg transition-colors"
                        >
                            Dismiss
                        </button>
                        <button
                            onClick={() => openActionModal(alert)}
                            disabled={!!processingId}
                            className="flex-1 md:flex-none px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors flex items-center justify-center gap-2"
                        >
                            {processingId === alert.sku_id ? (
                                <span className="animate-spin rounded-full h-4 w-4 border-2 border-white border-t-transparent"></span>
                            ) : (
                                <>
                                    Resolve
                                    <ArrowRight className="w-4 h-4" />
                                </>
                            )}
                        </button>
                    </div>
                </div>
            ))}

            {/* Action Modal */}
            {actionModal && (
                <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4 backdrop-blur-sm">
                    <div className="glass-card max-w-md w-full p-6 animate-in zoom-in-95 duration-200">
                        <div className="flex justify-between items-start mb-6">
                            <div>
                                <h3 className="text-xl font-bold text-white mb-1">
                                    {actionModal.type === 'RESTOCK' ? 'Restock Inventory' : 'Adjust Price'}
                                </h3>
                                <p className="text-sm text-slate-400">{actionModal.alert.product_name}</p>
                            </div>
                            <button onClick={() => setActionModal(null)} className="text-slate-400 hover:text-white">
                                <X className="w-5 h-5" />
                            </button>
                        </div>

                        <div className="mb-6">
                            <label className="block text-sm font-medium text-slate-300 mb-2">
                                {actionModal.type === 'RESTOCK' ? 'Quantity to Order' : 'New Price (₹)'}
                            </label>
                            <div className="relative">
                                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                                    {actionModal.type === 'RESTOCK' ? (
                                        <Package className="h-5 w-5 text-slate-500" />
                                    ) : (
                                        <DollarSign className="h-5 w-5 text-slate-500" />
                                    )}
                                </div>
                                <input
                                    type="number"
                                    value={inputValue}
                                    onChange={(e) => setInputValue(parseFloat(e.target.value))}
                                    className="block w-full pl-10 pr-3 py-2 bg-slate-800/50 border border-slate-600 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                                />
                            </div>
                            <p className="mt-2 text-xs text-slate-500">
                                {actionModal.type === 'RESTOCK'
                                    ? `Current Stock: ${actionModal.alert.current_stock}`
                                    : `Current Price: ₹${actionModal.alert.selling_price}`
                                }
                            </p>
                        </div>

                        <div className="flex gap-3">
                            <button
                                onClick={() => setActionModal(null)}
                                className="flex-1 px-4 py-2 border border-slate-600 hover:bg-slate-700 text-slate-300 rounded-lg transition-colors"
                            >
                                Cancel
                            </button>
                            <button
                                onClick={confirmAction}
                                className="flex-1 px-4 py-2 bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg transition-colors"
                            >
                                Confirm Action
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

export default AlertsTab;
