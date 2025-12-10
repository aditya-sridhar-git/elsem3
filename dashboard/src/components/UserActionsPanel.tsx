import React, { useEffect, useState } from 'react';
import { CheckCircle, Clock, XCircle, RefreshCw, ShoppingBag, DollarSign, AlertTriangle } from 'lucide-react';

interface UserAction {
    sku_id: string;
    action: string;
    quantity?: number;
    price?: number;
    email_id?: string;
    timestamp: string;
    status: string;
    execution_details?: {
        shopify_updated?: boolean;
        execution_message?: string;
        new_stock_level?: number;
        new_price?: number;
    };
    received_at: string;
}

interface ActionsResponse {
    total_pending?: number;
    total_completed?: number;
    actions: UserAction[];
}

export default function UserActionsPanel() {
    const [pendingActions, setPendingActions] = useState<UserAction[]>([]);
    const [completedActions, setCompletedActions] = useState<UserAction[]>([]);
    const [loading, setLoading] = useState(true);
    const [activeTab, setActiveTab] = useState<'pending' | 'completed'>('pending');

    const fetchActions = async () => {
        setLoading(true);
        try {
            const [pendingRes, completedRes] = await Promise.all([
                fetch('http://localhost:8000/api/user-actions/pending'),
                fetch('http://localhost:8000/api/user-actions/completed')
            ]);

            if (pendingRes.ok) {
                const pendingData: ActionsResponse = await pendingRes.json();
                setPendingActions(pendingData.actions || []);
            }

            if (completedRes.ok) {
                const completedData: ActionsResponse = await completedRes.json();
                setCompletedActions(completedData.actions || []);
            }
        } catch (error) {
            console.error('Failed to fetch user actions:', error);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchActions();
        // Auto-refresh every 30 seconds
        const interval = setInterval(fetchActions, 30000);
        return () => clearInterval(interval);
    }, []);

    const getActionIcon = (action: string) => {
        if (action.includes('RESTOCK')) return <ShoppingBag className="w-5 h-5 text-blue-500" />;
        if (action.includes('PRICE')) return <DollarSign className="w-5 h-5 text-green-500" />;
        if (action.includes('PAUSE')) return <AlertTriangle className="w-5 h-5 text-orange-500" />;
        return <CheckCircle className="w-5 h-5 text-gray-500" />;
    };

    const getActionBadge = (action: string) => {
        if (action.includes('RESTOCK')) return 'bg-blue-100 text-blue-700';
        if (action.includes('PRICE')) return 'bg-green-100 text-green-700';
        if (action.includes('PAUSE')) return 'bg-orange-100 text-orange-700';
        if (action.includes('REJECT')) return 'bg-red-100 text-red-700';
        return 'bg-gray-100 text-gray-700';
    };

    const formatTimestamp = (timestamp: string) => {
        try {
            return new Date(timestamp).toLocaleString();
        } catch {
            return timestamp;
        }
    };

    const renderActionCard = (action: UserAction, isPending: boolean) => (
        <div
            key={`${action.sku_id}-${action.timestamp}`}
            className="bg-white border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow"
        >
            <div className="flex items-start justify-between mb-3">
                <div className="flex items-center gap-3">
                    {getActionIcon(action.action)}
                    <div>
                        <h3 className="font-semibold text-gray-900">{action.sku_id}</h3>
                        <span className={`inline-block px-2 py-1 rounded text-xs font-medium ${getActionBadge(action.action)}`}>
                            {action.action.replace(/_/g, ' ')}
                        </span>
                    </div>
                </div>
                <div className="text-right">
                    {isPending ? (
                        <div className="flex items-center gap-2 text-yellow-600">
                            <Clock className="w-4 h-4" />
                            <span className="text-sm font-medium">Pending</span>
                        </div>
                    ) : (
                        <div className="flex items-center gap-2 text-green-600">
                            <CheckCircle className="w-4 h-4" />
                            <span className="text-sm font-medium">Completed</span>
                        </div>
                    )}
                </div>
            </div>

            <div className="space-y-2 text-sm">
                {action.quantity && (
                    <div className="flex justify-between">
                        <span className="text-gray-600">Quantity:</span>
                        <span className="font-medium">{action.quantity} units</span>
                    </div>
                )}
                {action.price && (
                    <div className="flex justify-between">
                        <span className="text-gray-600">New Price:</span>
                        <span className="font-medium">₹{action.price}</span>
                    </div>
                )}
                {action.execution_details?.new_stock_level && (
                    <div className="flex justify-between">
                        <span className="text-gray-600">New Stock Level:</span>
                        <span className="font-medium text-green-600">{action.execution_details.new_stock_level} units</span>
                    </div>
                )}
                {action.execution_details?.execution_message && (
                    <div className="mt-2 p-2 bg-green-50 rounded text-green-700 text-xs">
                        ✓ {action.execution_details.execution_message}
                    </div>
                )}
                <div className="flex justify-between text-xs text-gray-500 mt-3 pt-3 border-t">
                    <span>Received: {formatTimestamp(action.received_at)}</span>
                </div>
            </div>
        </div>
    );

    return (
        <div className="max-w-6xl mx-auto p-6">
            {/* Header */}
            <div className="mb-6">
                <div className="flex items-center justify-between mb-4">
                    <h1 className="text-3xl font-bold text-gray-900">User Actions</h1>
                    <button
                        onClick={fetchActions}
                        disabled={loading}
                        className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 transition-colors"
                    >
                        <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
                        Refresh
                    </button>
                </div>
                <p className="text-gray-600">
                    Track user responses from email approvals and dashboard actions
                </p>
            </div>

            {/* Stats Cards */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
                <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
                    <div className="flex items-center gap-3">
                        <Clock className="w-8 h-8 text-yellow-600" />
                        <div>
                            <div className="text-2xl font-bold text-yellow-900">{pendingActions.length}</div>
                            <div className="text-sm text-yellow-700">Pending Actions</div>
                        </div>
                    </div>
                </div>
                <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                    <div className="flex items-center gap-3">
                        <CheckCircle className="w-8 h-8 text-green-600" />
                        <div>
                            <div className="text-2xl font-bold text-green-900">{completedActions.length}</div>
                            <div className="text-sm text-green-700">Completed Actions</div>
                        </div>
                    </div>
                </div>
                <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                    <div className="flex items-center gap-3">
                        <ShoppingBag className="w-8 h-8 text-blue-600" />
                        <div>
                            <div className="text-2xl font-bold text-blue-900">
                                {pendingActions.length + completedActions.length}
                            </div>
                            <div className="text-sm text-blue-700">Total Actions</div>
                        </div>
                    </div>
                </div>
            </div>

            {/* Tabs */}
            <div className="flex border-b border-gray-200 mb-6">
                <button
                    onClick={() => setActiveTab('pending')}
                    className={`px-6 py-3 font-medium transition-colors ${activeTab === 'pending'
                            ? 'text-blue-600 border-b-2 border-blue-600'
                            : 'text-gray-600 hover:text-gray-900'
                        }`}
                >
                    Pending ({pendingActions.length})
                </button>
                <button
                    onClick={() => setActiveTab('completed')}
                    className={`px-6 py-3 font-medium transition-colors ${activeTab === 'completed'
                            ? 'text-blue-600 border-b-2 border-blue-600'
                            : 'text-gray-600 hover:text-gray-900'
                        }`}
                >
                    Completed ({completedActions.length})
                </button>
            </div>

            {/* Actions List */}
            {loading ? (
                <div className="flex items-center justify-center py-12">
                    <RefreshCw className="w-8 h-8 text-blue-600 animate-spin" />
                </div>
            ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                    {activeTab === 'pending' ? (
                        pendingActions.length > 0 ? (
                            pendingActions.map(action => renderActionCard(action, true))
                        ) : (
                            <div className="col-span-full text-center py-12 text-gray-500">
                                <Clock className="w-12 h-12 mx-auto mb-3 opacity-50" />
                                <p>No pending actions</p>
                                <p className="text-sm mt-1">User responses will appear here</p>
                            </div>
                        )
                    ) : (
                        completedActions.length > 0 ? (
                            completedActions.map(action => renderActionCard(action, false))
                        ) : (
                            <div className="col-span-full text-center py-12 text-gray-500">
                                <CheckCircle className="w-12 h-12 mx-auto mb-3 opacity-50" />
                                <p>No completed actions yet</p>
                                <p className="text-sm mt-1">Executed actions will appear here</p>
                            </div>
                        )
                    )}
                </div>
            )}

            {/* Info Footer */}
            <div className="mt-8 p-4 bg-blue-50 border border-blue-200 rounded-lg">
                <h3 className="font-semibold text-blue-900 mb-2">📧 How It Works</h3>
                <ul className="text-sm text-blue-800 space-y-1">
                    <li>• Users receive email recommendations from n8n workflow</li>
                    <li>• Users reply with action keywords (e.g., APPROVE_RESTOCK_SKU001)</li>
                    <li>• n8n detects the reply and executes the action</li>
                    <li>• Actions are logged here and dashboard updates automatically</li>
                    <li>• Auto-refreshes every 30 seconds</li>
                </ul>
            </div>
        </div>
    );
}
