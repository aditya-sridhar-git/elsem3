// API client for backend communication

import axios from 'axios';
import type { AgentStatusResponse, MetricsSummary, SKURecommendation, Alert } from '../types';

const API_BASE_URL = 'http://localhost:8000/api';

const apiClient = axios.create({
    baseURL: API_BASE_URL,
    timeout: 10000,
    headers: {
        'Content-Type': 'application/json',
    },
});

export const api = {
    // Health check
    checkHealth: async () => {
        const response = await apiClient.get('/health');
        return response.data;
    },

    // Get agent status
    getAgentStatus: async (): Promise<AgentStatusResponse> => {
        const response = await apiClient.get('/agents/status');
        return response.data;
    },

    // Run agents
    runAgents: async () => {
        const response = await apiClient.post('/agents/run');
        return response.data;
    },

    // Get metrics summary
    getMetricsSummary: async (): Promise<MetricsSummary> => {
        const response = await apiClient.get('/metrics/summary');
        return response.data;
    },

    // Get recommendations
    getRecommendations: async (): Promise<SKURecommendation[]> => {
        const response = await apiClient.get('/recommendations');
        return response.data;
    },

    // Get SKU details
    getSKUDetails: async (skuId: string) => {
        const response = await apiClient.get(`/sku/${skuId}`);
        return response.data;
    },

    // Get Alerts
    getAlerts: async (): Promise<Alert[]> => {
        const response = await apiClient.get('/alerts');
        return response.data;
    },

    executeAction: async (skuId: string, actionType: string, value?: number, originalValue?: number) => {
        const response = await apiClient.post('/alerts/action', {
            sku_id: skuId,
            action_type: actionType,
            value: value,
            original_value: originalValue
        });
        return response.data;
    },

    // Seasonal Analysis
    getSeasonalAnalysis: async (): Promise<any> => {
        const response = await apiClient.get('/seasonal/analysis');
        return response.data;
    },

    // Ad Gateway
    getAdCampaigns: async (): Promise<any> => {
        const response = await apiClient.get('/ads/campaigns');
        return response.data;
    },

    getAdMetrics: async (): Promise<any> => {
        const response = await apiClient.get('/ads/metrics/summary');
        return response.data;
    },

    connectAdPlatform: async (credentials: any) => {
        const response = await apiClient.post('/ads/connect', credentials);
        return response.data;
    },

    createCampaign: async (data: any) => {
        const response = await apiClient.post('/ads/campaigns', data);
        return response.data;
    },

    toggleCampaign: async (campaignId: string, action: 'pause' | 'resume') => {
        const response = await apiClient.post(`/ads/campaigns/${campaignId}/${action}`);
        return response.data;
    }
};

export default api;
