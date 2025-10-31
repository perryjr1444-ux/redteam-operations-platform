/**
 * Enhanced Chart.js Visualizations
 * Advanced, interactive charts for Red Team analytics
 *
 * Features:
 * - Real-time streaming data
 * - Interactive tooltips
 * - Zoom and pan
 * - Export functionality
 * - Responsive design
 */

// Enhanced cyberpunk color scheme
const enhancedChartColors = {
    primary: '#00ff00',
    secondary: '#00ffff',
    accent: '#ff00ff',
    danger: '#ff0040',
    warning: '#ffff00',
    success: '#00ff88',
    info: '#00aaff',
    bg: 'rgba(10, 14, 26, 0.95)',
    bgLight: 'rgba(0, 255, 0, 0.05)',
    grid: 'rgba(0, 255, 0, 0.1)',
    text: '#00ff00'
};

// Enhanced chart defaults
Chart.defaults.color = enhancedChartColors.text;
Chart.defaults.borderColor = enhancedChartColors.grid;
Chart.defaults.font.family = '"JetBrains Mono", "Courier New", monospace';
Chart.defaults.font.size = 12;

/**
 * Real-time streaming line chart
 * Perfect for live execution monitoring
 */
class StreamingChart {
    constructor(canvasId, options = {}) {
        this.canvasId = canvasId;
        this.maxDataPoints = options.maxDataPoints || 50;
        this.updateInterval = options.updateInterval || 1000;
        this.dataFetchUrl = options.dataFetchUrl;
        this.chart = null;
        this.timer = null;

        this.init(options);
    }

    init(options) {
        const ctx = document.getElementById(this.canvasId);
        if (!ctx) return;

        this.chart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [{
                    label: options.label || 'Value',
                    data: [],
                    borderColor: enhancedChartColors.primary,
                    backgroundColor: enhancedChartColors.bgLight,
                    borderWidth: 2,
                    fill: true,
                    tension: 0.4,
                    pointRadius: 0,
                    pointHoverRadius: 5,
                    pointHoverBackgroundColor: enhancedChartColors.secondary,
                    pointHoverBorderColor: enhancedChartColors.secondary
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                animation: {
                    duration: 300
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            color: enhancedChartColors.text,
                            font: { size: 11 }
                        },
                        grid: {
                            color: enhancedChartColors.grid,
                            drawBorder: false
                        }
                    },
                    x: {
                        ticks: {
                            color: enhancedChartColors.text,
                            font: { size: 11 },
                            maxRotation: 0,
                            autoSkip: true,
                            maxTicksLimit: 10
                        },
                        grid: {
                            display: false
                        }
                    }
                },
                plugins: {
                    legend: {
                        display: true,
                        position: 'top',
                        labels: {
                            color: enhancedChartColors.text,
                            font: { size: 12, weight: 'bold' },
                            padding: 15,
                            usePointStyle: true
                        }
                    },
                    tooltip: {
                        backgroundColor: enhancedChartColors.bg,
                        titleColor: enhancedChartColors.primary,
                        bodyColor: enhancedChartColors.secondary,
                        borderColor: enhancedChartColors.primary,
                        borderWidth: 1,
                        padding: 12,
                        displayColors: false,
                        callbacks: {
                            title: (items) => {
                                return `Time: ${items[0].label}`;
                            },
                            label: (item) => {
                                return `${item.dataset.label}: ${item.parsed.y}`;
                            }
                        }
                    }
                },
                interaction: {
                    intersect: false,
                    mode: 'index'
                }
            }
        });
    }

    addDataPoint(label, value) {
        if (!this.chart) return;

        this.chart.data.labels.push(label);
        this.chart.data.datasets[0].data.push(value);

        // Keep only last N points
        if (this.chart.data.labels.length > this.maxDataPoints) {
            this.chart.data.labels.shift();
            this.chart.data.datasets[0].data.shift();
        }

        this.chart.update('none'); // Disable animation for smooth streaming
    }

    async fetchAndUpdate() {
        if (!this.dataFetchUrl) return;

        try {
            const response = await fetch(this.dataFetchUrl);
            const data = await response.json();

            const timestamp = new Date().toLocaleTimeString();
            this.addDataPoint(timestamp, data.value);
        } catch (err) {
            console.error('Error fetching chart data:', err);
        }
    }

    startAutoUpdate() {
        this.fetchAndUpdate();
        this.timer = setInterval(() => this.fetchAndUpdate(), this.updateInterval);
    }

    stopAutoUpdate() {
        if (this.timer) {
            clearInterval(this.timer);
            this.timer = null;
        }
    }

    destroy() {
        this.stopAutoUpdate();
        if (this.chart) {
            this.chart.destroy();
        }
    }
}

/**
 * Multi-series comparison chart
 * Compare multiple metrics side-by-side
 */
function createMultiSeriesChart(canvasId, data, options = {}) {
    const ctx = document.getElementById(canvasId);
    if (!ctx) return null;

    const datasets = data.series.map((series, index) => {
        const colors = [
            enhancedChartColors.primary,
            enhancedChartColors.secondary,
            enhancedChartColors.accent,
            enhancedChartColors.warning
        ];
        const color = colors[index % colors.length];

        return {
            label: series.name,
            data: series.values,
            borderColor: color,
            backgroundColor: color.replace(')', ', 0.1)').replace('rgb', 'rgba'),
            borderWidth: 2,
            fill: true,
            tension: 0.4
        };
    });

    return new Chart(ctx, {
        type: options.type || 'line',
        data: {
            labels: data.labels,
            datasets: datasets
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: { color: enhancedChartColors.text },
                    grid: { color: enhancedChartColors.grid }
                },
                x: {
                    ticks: { color: enhancedChartColors.text },
                    grid: { display: false }
                }
            },
            plugins: {
                legend: {
                    labels: {
                        color: enhancedChartColors.text,
                        font: { weight: 'bold' },
                        usePointStyle: true
                    }
                },
                tooltip: {
                    backgroundColor: enhancedChartColors.bg,
                    titleColor: enhancedChartColors.primary,
                    bodyColor: enhancedChartColors.secondary,
                    borderColor: enhancedChartColors.primary,
                    borderWidth: 1
                }
            }
        }
    });
}

/**
 * Radial gauge chart
 * Perfect for health scores, success rates
 */
function createRadialGaugeChart(canvasId, value, options = {}) {
    const ctx = document.getElementById(canvasId);
    if (!ctx) return null;

    const maxValue = options.maxValue || 100;
    const label = options.label || 'Score';

    // Determine color based on value
    let color = enhancedChartColors.primary;
    if (value < 50) color = enhancedChartColors.danger;
    else if (value < 75) color = enhancedChartColors.warning;

    return new Chart(ctx, {
        type: 'doughnut',
        data: {
            datasets: [{
                data: [value, maxValue - value],
                backgroundColor: [color, enhancedChartColors.bgLight],
                borderColor: [color, enhancedChartColors.grid],
                borderWidth: 2,
                circumference: 270,
                rotation: 225
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            cutout: '75%',
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    enabled: false
                }
            }
        },
        plugins: [{
            id: 'gaugeText',
            afterDraw: (chart) => {
                const { ctx, chartArea: { width, height } } = chart;

                ctx.save();
                ctx.font = 'bold 32px "JetBrains Mono"';
                ctx.fillStyle = color;
                ctx.textAlign = 'center';
                ctx.textBaseline = 'middle';
                ctx.fillText(`${value}%`, width / 2, height / 2);

                ctx.font = '14px "JetBrains Mono"';
                ctx.fillStyle = enhancedChartColors.text;
                ctx.fillText(label, width / 2, height / 2 + 30);
                ctx.restore();
            }
        }]
    });
}

/**
 * Heatmap chart for attack coverage
 * Shows coverage across MITRE ATT&CK tactics
 */
function createHeatmapChart(canvasId, data) {
    const ctx = document.getElementById(canvasId);
    if (!ctx) return null;

    // Transform data for heatmap
    const datasets = data.rows.map((row, rowIndex) => {
        return {
            label: row.label,
            data: row.values.map((value, colIndex) => ({
                x: data.columns[colIndex],
                y: row.label,
                v: value
            })),
            backgroundColor: (context) => {
                const value = context.parsed?.v || 0;
                const alpha = value / 10; // Assuming 0-10 scale
                return `rgba(0, 255, 0, ${alpha})`;
            },
            borderColor: enhancedChartColors.grid,
            borderWidth: 1,
            width: ({ chart }) => (chart.chartArea.width / data.columns.length) - 2,
            height: ({ chart }) => (chart.chartArea.height / data.rows.length) - 2
        };
    });

    return new Chart(ctx, {
        type: 'matrix',
        data: { datasets },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                x: {
                    type: 'category',
                    labels: data.columns,
                    ticks: { color: enhancedChartColors.text },
                    grid: { display: false }
                },
                y: {
                    type: 'category',
                    labels: data.rows.map(r => r.label),
                    ticks: { color: enhancedChartColors.text },
                    grid: { display: false }
                }
            },
            plugins: {
                legend: { display: false },
                tooltip: {
                    callbacks: {
                        title: () => '',
                        label: (context) => {
                            const { x, y, v } = context.parsed;
                            return `${y} - ${x}: ${v}`;
                        }
                    }
                }
            }
        }
    });
}

/**
 * Export chart as PNG image
 */
function exportChartImage(chart, filename = 'chart.png') {
    const url = chart.toBase64Image();
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    link.click();
}

/**
 * Create responsive chart that adapts to container
 */
function createResponsiveChart(canvasId, config) {
    const ctx = document.getElementById(canvasId);
    if (!ctx) return null;

    // Add responsive options
    config.options = config.options || {};
    config.options.responsive = true;
    config.options.maintainAspectRatio = false;

    const chart = new Chart(ctx, config);

    // Handle window resize
    let resizeTimer;
    window.addEventListener('resize', () => {
        clearTimeout(resizeTimer);
        resizeTimer = setTimeout(() => {
            chart.resize();
        }, 250);
    });

    return chart;
}

// Export for global use
window.ChartEnhancements = {
    StreamingChart,
    createMultiSeriesChart,
    createRadialGaugeChart,
    createHeatmapChart,
    exportChartImage,
    createResponsiveChart,
    colors: enhancedChartColors
};
