import React from 'react';
import {
    Chart as ChartJS,
    CategoryScale,
    LinearScale,
    BarElement,
    Title,
    Tooltip,
    Legend,
    ArcElement,
} from 'chart.js';
import { Bar, Doughnut } from 'react-chartjs-2';
import type { MetricsSummary, SKURecommendation } from '../types';

ChartJS.register(
    CategoryScale,
    LinearScale,
    BarElement,
    Title,
    Tooltip,
    Legend,
    ArcElement
);

interface MetricsChartProps {
    metrics: MetricsSummary;
    recommendations: SKURecommendation[];
}

const MetricsChart: React.FC<MetricsChartProps> = ({ metrics, recommendations }) => {
    // Risk level distribution
    const riskData = {
        labels: ['Critical', 'Warning', 'Safe'],
        datasets: [
            {
                label: 'Risk Distribution',
                data: [
                    metrics.total_critical_risk,
                    metrics.total_warning_risk,
                    metrics.total_safe,
                ],
                backgroundColor: [
                    'rgba(239, 68, 68, 0.8)',
                    'rgba(245, 158, 11, 0.8)',
                    'rgba(16, 185, 129, 0.8)',
                ],
                borderColor: [
                    'rgba(239, 68, 68, 1)',
                    'rgba(245, 158, 11, 1)',
                    'rgba(16, 185, 129, 1)',
                ],
                borderWidth: 2,
            },
        ],
    };

    // Category wise profit/loss
    const categoryData = recommendations.reduce((acc: any, item) => {
        if (!acc[item.category]) {
            acc[item.category] = { profit: 0, loss: 0 };
        }
        if (item.profit_per_unit > 0) {
            acc[item.category].profit += item.profit_per_unit;
        } else {
            acc[item.category].loss += Math.abs(item.profit_per_unit);
        }
        return acc;
    }, {});

    const categoryChartData = {
        labels: Object.keys(categoryData),
        datasets: [
            {
                label: 'Profit',
                data: Object.values(categoryData).map((cat: any) => cat.profit),
                backgroundColor: 'rgba(16, 185, 129, 0.8)',
                borderColor: 'rgba(16, 185, 129, 1)',
                borderWidth: 2,
            },
            {
                label: 'Loss',
                data: Object.values(categoryData).map((cat: any) => cat.loss),
                backgroundColor: 'rgba(239, 68, 68, 0.8)',
                borderColor: 'rgba(239, 68, 68, 1)',
                borderWidth: 2,
            },
        ],
    };

    const chartOptions = {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            legend: {
                position: 'top' as const,
                labels: {
                    color: '#cbd5e1',
                    font: {
                        size: 12,
                        family: 'Inter',
                    },
                },
            },
            title: {
                display: false,
            },
        },
        scales: {
            x: {
                ticks: { color: '#94a3b8' },
                grid: { color: 'rgba(148, 163, 184, 0.1)' },
            },
            y: {
                ticks: { color: '#94a3b8' },
                grid: { color: 'rgba(148, 163, 184, 0.1)' },
            },
        },
    };

    const doughnutOptions = {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            legend: {
                position: 'bottom' as const,
                labels: {
                    color: '#cbd5e1',
                    font: {
                        size: 12,
                        family: 'Inter',
                    },
                },
            },
        },
    };

    return (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Risk Distribution */}
            <div className="glass-card p-6 fade-in">
                <h3 className="text-lg font-semibold text-white mb-4">Risk Distribution</h3>
                <div className="h-64">
                    <Doughnut data={riskData} options={doughnutOptions} />
                </div>
            </div>

            {/* Category Profit/Loss */}
            <div className="glass-card p-6 fade-in">
                <h3 className="text-lg font-semibold text-white mb-4">Profit/Loss by Category</h3>
                <div className="h-64">
                    <Bar data={categoryChartData} options={chartOptions} />
                </div>
            </div>
        </div>
    );
};

export default MetricsChart;
