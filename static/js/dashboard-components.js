/**
 * Dashboard Alpine.js Components
 * Phase 5.3: Dashboard-specific reactive components and stores
 *
 * Components:
 * - Agent Dashboard Store (5s refresh)
 * - Execution Dashboard Store (3s refresh)
 * - Analytics Dashboard Store (10s refresh)
 * - Widget Factory Functions
 * - Refresh Control Components
 * - Color Mapping Utilities
 * - Chart.js Wrappers
 * - Error Handling Components
 */

// =============================================================================
// ALPINE STORES
// =============================================================================

document.addEventListener('alpine:init', () => {
    /**
     * Agent Dashboard Store
     * Manages agent status, tasks, and metrics with auto-refresh
     */
    Alpine.store('agentDashboard', {
        data: {
            agents: [],
            tasks: [],
            metrics: {
                totalAgents: 0,
                healthyAgents: 0,
                activeTasks: 0,
                avgResponseTime: 0,
                uptime: 0
            }
        },
        lastUpdate: null,
        refreshInterval: 5000,
        isPaused: false,
        isLoading: false,
        error: null,
        intervalId: null,

        async fetch() {
            if (this.isPaused) return;

            this.isLoading = true;
            this.error = null;

            try {
                const response = await fetch('/api/dashboard/agents/status');

                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                }

                const data = await response.json();
                this.data = data;
                this.lastUpdate = new Date();

                // Calculate metrics from agent data
                if (data.agents && Array.isArray(data.agents)) {
                    this.data.metrics.totalAgents = data.agents.length;
                    this.data.metrics.healthyAgents = data.agents.filter(a => a.is_healthy).length;

                    const responseTimes = data.agents.map(a => a.avg_response_time || 0);
                    this.data.metrics.avgResponseTime = responseTimes.length > 0
                        ? responseTimes.reduce((a, b) => a + b, 0) / responseTimes.length
                        : 0;
                }

                if (data.tasks && Array.isArray(data.tasks)) {
                    this.data.metrics.activeTasks = data.tasks.filter(t => t.status === 'running' || t.status === 'pending').length;
                }

            } catch (err) {
                console.error('Error fetching agent dashboard data:', err);
                this.error = err.message;
            } finally {
                this.isLoading = false;
            }
        },

        startAutoRefresh(interval = 5000) {
            this.refreshInterval = interval;
            this.fetch();

            if (this.intervalId) {
                clearInterval(this.intervalId);
            }

            this.intervalId = setInterval(() => this.fetch(), interval);
        },

        stopAutoRefresh() {
            if (this.intervalId) {
                clearInterval(this.intervalId);
                this.intervalId = null;
            }
        },

        pause() {
            this.isPaused = true;
        },

        resume() {
            this.isPaused = false;
            this.fetch();
        },

        manualRefresh() {
            this.fetch();
        },

        updateRefreshInterval(newInterval) {
            this.refreshInterval = newInterval;
            this.stopAutoRefresh();
            this.startAutoRefresh(newInterval);
        }
    });

    /**
     * Execution Dashboard Store
     * Manages fractal execution tracking with fast refresh (3s)
     */
    Alpine.store('executionDashboard', {
        data: {
            executions: [],
            layers: {
                meta: [],
                exercise: [],
                chain: [],
                tool: [],
                container: []
            },
            metrics: {
                activeExecutions: 0,
                completedToday: 0,
                failedToday: 0,
                avgDuration: 0,
                successRate: 0
            }
        },
        lastUpdate: null,
        refreshInterval: 3000,
        isPaused: false,
        isLoading: false,
        error: null,
        intervalId: null,

        async fetch() {
            if (this.isPaused) return;

            this.isLoading = true;
            this.error = null;

            try {
                const response = await fetch('/api/dashboard/execution/status');

                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                }

                const data = await response.json();
                this.data = data;
                this.lastUpdate = new Date();

                // Calculate metrics
                if (data.executions && Array.isArray(data.executions)) {
                    this.data.metrics.activeExecutions = data.executions.filter(
                        e => e.status === 'running' || e.status === 'pending'
                    ).length;

                    // Calculate success rate
                    const completed = data.executions.filter(e => e.status === 'completed').length;
                    const failed = data.executions.filter(e => e.status === 'failed').length;
                    const total = completed + failed;
                    this.data.metrics.successRate = total > 0 ? (completed / total) * 100 : 0;
                }

                // Organize by layers
                if (data.executions) {
                    this.data.layers = {
                        meta: data.executions.filter(e => e.layer === 'meta'),
                        exercise: data.executions.filter(e => e.layer === 'exercise'),
                        chain: data.executions.filter(e => e.layer === 'chain'),
                        tool: data.executions.filter(e => e.layer === 'tool'),
                        container: data.executions.filter(e => e.layer === 'container')
                    };
                }

            } catch (err) {
                console.error('Error fetching execution dashboard data:', err);
                this.error = err.message;
            } finally {
                this.isLoading = false;
            }
        },

        startAutoRefresh(interval = 3000) {
            this.refreshInterval = interval;
            this.fetch();

            if (this.intervalId) {
                clearInterval(this.intervalId);
            }

            this.intervalId = setInterval(() => this.fetch(), interval);
        },

        stopAutoRefresh() {
            if (this.intervalId) {
                clearInterval(this.intervalId);
                this.intervalId = null;
            }
        },

        pause() {
            this.isPaused = true;
        },

        resume() {
            this.isPaused = false;
            this.fetch();
        },

        manualRefresh() {
            this.fetch();
        },

        updateRefreshInterval(newInterval) {
            this.refreshInterval = newInterval;
            this.stopAutoRefresh();
            this.startAutoRefresh(newInterval);
        }
    });

    /**
     * Analytics Dashboard Store
     * Manages security analytics and posture with slower refresh (10s)
     */
    Alpine.store('analyticsDashboard', {
        data: {
            security: {
                posture: 0,
                vulnerabilities: [],
                threats: [],
                findings: []
            },
            performance: {
                toolUsage: [],
                chainEfficiency: [],
                agentPerformance: []
            },
            trends: {
                executionVolume: [],
                successRate: [],
                responseTime: []
            },
            metrics: {
                totalFindings: 0,
                criticalFindings: 0,
                postureScore: 0,
                averageRiskScore: 0
            }
        },
        lastUpdate: null,
        refreshInterval: 10000,
        isPaused: false,
        isLoading: false,
        error: null,
        intervalId: null,

        async fetch() {
            if (this.isPaused) return;

            this.isLoading = true;
            this.error = null;

            try {
                const response = await fetch('/api/dashboard/analytics/status');

                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                }

                const data = await response.json();
                this.data = data;
                this.lastUpdate = new Date();

                // Calculate metrics
                if (data.security && data.security.vulnerabilities) {
                    this.data.metrics.totalFindings = data.security.vulnerabilities.length;
                    this.data.metrics.criticalFindings = data.security.vulnerabilities.filter(
                        v => v.severity === 'critical' || v.severity === 'high'
                    ).length;
                }

                if (data.security && data.security.posture !== undefined) {
                    this.data.metrics.postureScore = data.security.posture;
                }

            } catch (err) {
                console.error('Error fetching analytics dashboard data:', err);
                this.error = err.message;
            } finally {
                this.isLoading = false;
            }
        },

        startAutoRefresh(interval = 10000) {
            this.refreshInterval = interval;
            this.fetch();

            if (this.intervalId) {
                clearInterval(this.intervalId);
            }

            this.intervalId = setInterval(() => this.fetch(), interval);
        },

        stopAutoRefresh() {
            if (this.intervalId) {
                clearInterval(this.intervalId);
                this.intervalId = null;
            }
        },

        pause() {
            this.isPaused = true;
        },

        resume() {
            this.isPaused = false;
            this.fetch();
        },

        manualRefresh() {
            this.fetch();
        },

        updateRefreshInterval(newInterval) {
            this.refreshInterval = newInterval;
            this.stopAutoRefresh();
            this.startAutoRefresh(newInterval);
        }
    });
});

// =============================================================================
// WIDGET FACTORY FUNCTIONS
// =============================================================================

/**
 * Agent Health Card Component
 * Displays individual agent health with color-coded status
 */
function agentHealthCard(agentType) {
    return {
        agentType: agentType,
        color: getAgentColor(agentType),

        init() {
            // Subscribe to agent store updates
            this.$watch('$store.agentDashboard.data', () => {
                this.updateDisplay();
            });
        },

        updateDisplay() {
            // Trigger Alpine reactivity
            this.$nextTick(() => {
                // Force re-render if needed
            });
        },

        get agent() {
            const agents = this.$store.agentDashboard.data.agents || [];
            return agents.find(a => a.type === this.agentType) || null;
        },

        get status() {
            return this.agent ? this.agent.status : 'unknown';
        },

        get isHealthy() {
            return this.agent ? this.agent.is_healthy : false;
        },

        get metrics() {
            if (!this.agent) return {};
            return {
                responseTime: this.agent.avg_response_time || 0,
                uptime: this.agent.uptime_percentage || 0,
                tasksCompleted: this.agent.tasks_completed || 0,
                tasksActive: this.agent.tasks_active || 0
            };
        },

        get statusClass() {
            return this.isHealthy ? 'status-healthy' : 'status-unhealthy';
        },

        get statusIcon() {
            return this.isHealthy ? 'bi-check-circle-fill' : 'bi-exclamation-triangle-fill';
        },

        get responseTimeColor() {
            const time = this.metrics.responseTime;
            if (time < 100) return 'text-success';
            if (time < 500) return 'text-warning';
            return 'text-danger';
        },

        get uptimeColor() {
            const uptime = this.metrics.uptime;
            if (uptime >= 95) return 'text-success';
            if (uptime >= 80) return 'text-warning';
            return 'text-danger';
        }
    };
}

/**
 * Execution Metric Card Component
 * Displays execution layer metrics with fractal visualization
 */
function executionMetricCard(metricType) {
    return {
        metricType: metricType,
        color: getExecutionColor(metricType),

        init() {
            this.$watch('$store.executionDashboard.data', () => {
                this.updateDisplay();
            });
        },

        updateDisplay() {
            this.$nextTick(() => {
                // Update visualization if needed
            });
        },

        get layerData() {
            const layers = this.$store.executionDashboard.data.layers || {};
            return layers[this.metricType] || [];
        },

        get metrics() {
            const data = this.layerData;
            return {
                total: data.length,
                active: data.filter(e => e.status === 'running').length,
                completed: data.filter(e => e.status === 'completed').length,
                failed: data.filter(e => e.status === 'failed').length,
                pending: data.filter(e => e.status === 'pending').length
            };
        },

        get successRate() {
            const total = this.metrics.completed + this.metrics.failed;
            if (total === 0) return 0;
            return (this.metrics.completed / total) * 100;
        },

        get statusDistribution() {
            const total = this.metrics.total;
            if (total === 0) return {};

            return {
                active: (this.metrics.active / total) * 100,
                completed: (this.metrics.completed / total) * 100,
                failed: (this.metrics.failed / total) * 100,
                pending: (this.metrics.pending / total) * 100
            };
        },

        get avgDuration() {
            const completedExecs = this.layerData.filter(e => e.status === 'completed' && e.duration);
            if (completedExecs.length === 0) return 0;

            const totalDuration = completedExecs.reduce((sum, e) => sum + e.duration, 0);
            return totalDuration / completedExecs.length;
        }
    };
}

/**
 * Security Posture Card Component
 * Displays overall security posture with threat indicators
 */
function securityPostureCard() {
    return {
        init() {
            this.$watch('$store.analyticsDashboard.data', () => {
                this.updateDisplay();
            });
        },

        updateDisplay() {
            this.$nextTick(() => {
                // Update gauges and charts
            });
        },

        get postureScore() {
            return this.$store.analyticsDashboard.data.security?.posture || 0;
        },

        get postureGrade() {
            const score = this.postureScore;
            if (score >= 90) return 'A';
            if (score >= 80) return 'B';
            if (score >= 70) return 'C';
            if (score >= 60) return 'D';
            return 'F';
        },

        get postureColor() {
            const score = this.postureScore;
            if (score >= 90) return '#06ffa5';
            if (score >= 80) return '#00d4ff';
            if (score >= 70) return '#ffd23f';
            if (score >= 60) return '#ff6b35';
            return '#ff0055';
        },

        get vulnerabilities() {
            return this.$store.analyticsDashboard.data.security?.vulnerabilities || [];
        },

        get threats() {
            return this.$store.analyticsDashboard.data.security?.threats || [];
        },

        get findingsBySeverity() {
            const vulns = this.vulnerabilities;
            return {
                critical: vulns.filter(v => v.severity === 'critical').length,
                high: vulns.filter(v => v.severity === 'high').length,
                medium: vulns.filter(v => v.severity === 'medium').length,
                low: vulns.filter(v => v.severity === 'low').length
            };
        },

        get criticalCount() {
            return this.findingsBySeverity.critical;
        },

        get hasActiveThreats() {
            return this.threats.length > 0;
        }
    };
}

/**
 * Task Queue Visualization Component
 * Real-time task queue with priority indicators
 */
function taskQueueVisualization() {
    return {
        maxDisplayed: 10,

        init() {
            this.$watch('$store.agentDashboard.data.tasks', () => {
                this.updateQueue();
            });
        },

        updateQueue() {
            this.$nextTick(() => {
                // Trigger animations
            });
        },

        get tasks() {
            return this.$store.agentDashboard.data.tasks || [];
        },

        get displayedTasks() {
            return this.tasks
                .sort((a, b) => b.priority - a.priority)
                .slice(0, this.maxDisplayed);
        },

        get queueMetrics() {
            return {
                total: this.tasks.length,
                pending: this.tasks.filter(t => t.status === 'pending').length,
                running: this.tasks.filter(t => t.status === 'running').length,
                highPriority: this.tasks.filter(t => t.priority >= 7).length
            };
        },

        getPriorityClass(priority) {
            if (priority >= 9) return 'priority-critical';
            if (priority >= 7) return 'priority-high';
            if (priority >= 5) return 'priority-medium';
            return 'priority-low';
        },

        getPriorityColor(priority) {
            if (priority >= 9) return '#ff0055';
            if (priority >= 7) return '#ff6b35';
            if (priority >= 5) return '#ffd23f';
            return '#06ffa5';
        },

        getStatusIcon(status) {
            const icons = {
                'pending': 'bi-clock',
                'running': 'bi-play-circle-fill',
                'completed': 'bi-check-circle-fill',
                'failed': 'bi-x-circle-fill'
            };
            return icons[status] || 'bi-circle';
        }
    };
}

// =============================================================================
// REFRESH CONTROL COMPONENT
// =============================================================================

/**
 * Refresh Control Component
 * Controls auto-refresh intervals and manual refresh for dashboard stores
 */
function refreshControl(storeName, defaultInterval = 5000) {
    return {
        storeName: storeName,
        intervals: [
            { value: 1000, label: '1s' },
            { value: 3000, label: '3s' },
            { value: 5000, label: '5s' },
            { value: 10000, label: '10s' },
            { value: 15000, label: '15s' },
            { value: 30000, label: '30s' },
            { value: 60000, label: '1m' }
        ],
        currentInterval: defaultInterval,
        isPaused: false,

        init() {
            // Initialize with current store state
            const store = this.getStore();
            if (store) {
                this.currentInterval = store.refreshInterval;
                this.isPaused = store.isPaused;
            }
        },

        getStore() {
            return Alpine.store(this.storeName);
        },

        get lastUpdate() {
            const store = this.getStore();
            if (!store || !store.lastUpdate) return null;
            return store.lastUpdate;
        },

        get formattedLastUpdate() {
            if (!this.lastUpdate) return 'Never';

            const now = new Date();
            const diff = Math.floor((now - this.lastUpdate) / 1000); // seconds

            if (diff < 60) return `${diff}s ago`;
            if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
            return `${Math.floor(diff / 3600)}h ago`;
        },

        get isLoading() {
            const store = this.getStore();
            return store ? store.isLoading : false;
        },

        get error() {
            const store = this.getStore();
            return store ? store.error : null;
        },

        setInterval(ms) {
            this.currentInterval = ms;
            const store = this.getStore();
            if (store) {
                store.updateRefreshInterval(ms);
            }
        },

        toggle() {
            this.isPaused = !this.isPaused;
            const store = this.getStore();

            if (store) {
                if (this.isPaused) {
                    store.pause();
                } else {
                    store.resume();
                }
            }
        },

        manualRefresh() {
            const store = this.getStore();
            if (store) {
                store.manualRefresh();
            }
        },

        get buttonIcon() {
            if (this.isLoading) return 'bi-arrow-clockwise spin';
            if (this.isPaused) return 'bi-play-fill';
            return 'bi-pause-fill';
        },

        get statusText() {
            if (this.isLoading) return 'Refreshing...';
            if (this.isPaused) return 'Paused';
            return 'Auto-refresh';
        }
    };
}

// =============================================================================
// COLOR MAPPING UTILITIES
// =============================================================================

/**
 * Get color for agent type
 */
function getAgentColor(agentType) {
    const colors = {
        'coordinator': '#00ff9f',
        'planner': '#ff6b9d',
        'analyzer': '#ffd700',
        'advisor': '#00d4ff',
        'optimizer': '#b794f6',
        'executor': '#06ffa5',
        'monitor': '#ff9e64'
    };
    return colors[agentType] || '#ffffff';
}

/**
 * Get color for execution layer
 */
function getExecutionColor(layer) {
    const colors = {
        'meta': '#9d4edd',
        'exercise': '#0096ff',
        'chain': '#00d9ff',
        'tool': '#22d3ee',
        'container': '#06b6d4'
    };
    return colors[layer] || '#ffffff';
}

/**
 * Get color for severity level
 */
function getSeverityColor(severity) {
    const colors = {
        'critical': '#ff0055',
        'high': '#ff6b35',
        'medium': '#ffd23f',
        'low': '#06ffa5',
        'info': '#00d4ff'
    };
    return colors[severity] || '#ffffff';
}

/**
 * Get color for property type (from design system)
 */
function getPropertyColor(propertyType) {
    const colors = {
        'evasion': '#00ff9f',
        'stealth': '#ff6b9d',
        'persistence': '#b794f6',
        'speed': '#00d4ff',
        'automation': '#ffd700'
    };
    return colors[propertyType] || '#ffffff';
}

/**
 * Get color for status
 */
function getStatusColor(status) {
    const colors = {
        'running': '#0096ff',
        'completed': '#06ffa5',
        'failed': '#ff0055',
        'pending': '#ffd23f',
        'cancelled': '#808080'
    };
    return colors[status] || '#ffffff';
}

// =============================================================================
// CHART.JS WRAPPERS
// =============================================================================

/**
 * Create Property-themed Chart
 * Generic chart creator with property-based theming
 */
function createPropertyChart(canvasId, type, propertyType, data) {
    const color = getPropertyColor(propertyType);
    const ctx = document.getElementById(canvasId);
    if (!ctx) {
        console.error(`Canvas element not found: ${canvasId}`);
        return null;
    }

    const chartData = typeof data === 'function' ? data(color) : data;

    return new Chart(ctx.getContext('2d'), {
        type: type,
        data: chartData,
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    labels: {
                        color: '#ffffff',
                        font: {
                            family: "'JetBrains Mono', monospace",
                            size: 11
                        }
                    }
                },
                tooltip: {
                    backgroundColor: 'rgba(0, 0, 0, 0.8)',
                    titleColor: color,
                    bodyColor: '#ffffff',
                    borderColor: color,
                    borderWidth: 1,
                    font: {
                        family: "'JetBrains Mono', monospace"
                    }
                }
            },
            scales: type === 'line' || type === 'bar' ? {
                x: {
                    grid: {
                        color: 'rgba(255, 255, 255, 0.1)'
                    },
                    ticks: {
                        color: '#999999',
                        font: {
                            family: "'JetBrains Mono', monospace",
                            size: 10
                        }
                    }
                },
                y: {
                    grid: {
                        color: 'rgba(255, 255, 255, 0.1)'
                    },
                    ticks: {
                        color: '#999999',
                        font: {
                            family: "'JetBrains Mono', monospace",
                            size: 10
                        }
                    }
                }
            } : {},
            animation: {
                duration: 750,
                easing: 'easeInOutQuart'
            }
        }
    });
}

/**
 * Create Line Chart with property theming
 */
function createLineChart(canvasId, propertyType, data) {
    const color = getPropertyColor(propertyType);

    const chartData = {
        labels: data.labels || [],
        datasets: [{
            label: data.label || 'Value',
            data: data.values || [],
            borderColor: color,
            backgroundColor: `${color}20`,
            borderWidth: 2,
            fill: true,
            tension: 0.4,
            pointBackgroundColor: color,
            pointBorderColor: '#ffffff',
            pointBorderWidth: 2,
            pointRadius: 4,
            pointHoverRadius: 6
        }]
    };

    return createPropertyChart(canvasId, 'line', propertyType, chartData);
}

/**
 * Create Bar Chart with property theming
 */
function createBarChart(canvasId, propertyType, data) {
    const color = getPropertyColor(propertyType);

    const chartData = {
        labels: data.labels || [],
        datasets: [{
            label: data.label || 'Value',
            data: data.values || [],
            backgroundColor: `${color}80`,
            borderColor: color,
            borderWidth: 2,
            borderRadius: 4
        }]
    };

    return createPropertyChart(canvasId, 'bar', propertyType, chartData);
}

/**
 * Create Gauge Chart (doughnut with center text)
 */
function createGaugeChart(canvasId, propertyType, value, max = 100) {
    const color = getPropertyColor(propertyType);
    const percentage = (value / max) * 100;

    const chartData = {
        labels: ['Value', 'Remaining'],
        datasets: [{
            data: [value, max - value],
            backgroundColor: [color, 'rgba(255, 255, 255, 0.1)'],
            borderColor: ['#ffffff', 'transparent'],
            borderWidth: 2
        }]
    };

    const ctx = document.getElementById(canvasId);
    if (!ctx) {
        console.error(`Canvas element not found: ${canvasId}`);
        return null;
    }

    const chart = new Chart(ctx.getContext('2d'), {
        type: 'doughnut',
        data: chartData,
        options: {
            responsive: true,
            maintainAspectRatio: false,
            cutout: '70%',
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    enabled: true,
                    backgroundColor: 'rgba(0, 0, 0, 0.8)',
                    titleColor: color,
                    bodyColor: '#ffffff',
                    borderColor: color,
                    borderWidth: 1
                }
            },
            animation: {
                duration: 1000,
                easing: 'easeInOutQuart'
            }
        },
        plugins: [{
            id: 'centerText',
            beforeDraw: (chart) => {
                const ctx = chart.ctx;
                const width = chart.width;
                const height = chart.height;

                ctx.restore();
                ctx.font = 'bold 32px "JetBrains Mono"';
                ctx.textBaseline = 'middle';
                ctx.fillStyle = color;

                const text = `${Math.round(percentage)}%`;
                const textX = Math.round((width - ctx.measureText(text).width) / 2);
                const textY = height / 2;

                ctx.fillText(text, textX, textY);
                ctx.save();
            }
        }]
    });

    return chart;
}

/**
 * Create Pie Chart with property theming
 */
function createPieChart(canvasId, propertyType, data) {
    const baseColor = getPropertyColor(propertyType);

    // Generate color variants
    const colors = data.values.map((_, index) => {
        const hue = parseInt(baseColor.slice(1, 3), 16);
        const sat = parseInt(baseColor.slice(3, 5), 16);
        const light = parseInt(baseColor.slice(5, 7), 16);

        const offset = (index * 30) % 360;
        return `hsl(${hue + offset}, ${sat}%, ${light}%)`;
    });

    const chartData = {
        labels: data.labels || [],
        datasets: [{
            data: data.values || [],
            backgroundColor: colors,
            borderColor: '#ffffff',
            borderWidth: 2
        }]
    };

    return createPropertyChart(canvasId, 'pie', propertyType, chartData);
}

/**
 * Create Stacked Bar Chart for execution layers
 */
function createStackedBarChart(canvasId, data) {
    const ctx = document.getElementById(canvasId);
    if (!ctx) {
        console.error(`Canvas element not found: ${canvasId}`);
        return null;
    }

    const layers = ['meta', 'exercise', 'chain', 'tool', 'container'];
    const datasets = layers.map(layer => ({
        label: layer.charAt(0).toUpperCase() + layer.slice(1),
        data: data.values[layer] || [],
        backgroundColor: `${getExecutionColor(layer)}80`,
        borderColor: getExecutionColor(layer),
        borderWidth: 2
    }));

    return new Chart(ctx.getContext('2d'), {
        type: 'bar',
        data: {
            labels: data.labels || [],
            datasets: datasets
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    labels: {
                        color: '#ffffff',
                        font: {
                            family: "'JetBrains Mono', monospace",
                            size: 11
                        }
                    }
                }
            },
            scales: {
                x: {
                    stacked: true,
                    grid: {
                        color: 'rgba(255, 255, 255, 0.1)'
                    },
                    ticks: {
                        color: '#999999',
                        font: {
                            family: "'JetBrains Mono', monospace"
                        }
                    }
                },
                y: {
                    stacked: true,
                    grid: {
                        color: 'rgba(255, 255, 255, 0.1)'
                    },
                    ticks: {
                        color: '#999999',
                        font: {
                            family: "'JetBrains Mono', monospace"
                        }
                    }
                }
            }
        }
    });
}

// =============================================================================
// ERROR HANDLING & LOADING STATES
// =============================================================================

/**
 * Dashboard Card Component with Loading/Error States
 */
function dashboardCard() {
    return {
        loading: false,
        error: null,
        data: null,

        async loadData(endpoint) {
            this.loading = true;
            this.error = null;

            try {
                const response = await fetch(endpoint);

                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                }

                this.data = await response.json();
            } catch (e) {
                console.error(`Error loading data from ${endpoint}:`, e);
                this.error = e.message;
            } finally {
                this.loading = false;
            }
        },

        retry() {
            if (this.lastEndpoint) {
                this.loadData(this.lastEndpoint);
            }
        },

        get hasError() {
            return this.error !== null;
        },

        get hasData() {
            return this.data !== null && !this.loading && !this.error;
        },

        get isEmpty() {
            return this.hasData && (
                (Array.isArray(this.data) && this.data.length === 0) ||
                (typeof this.data === 'object' && Object.keys(this.data).length === 0)
            );
        }
    };
}

/**
 * Data Table Component with Sorting/Filtering
 */
function dataTable(initialData = []) {
    return {
        data: initialData,
        sortColumn: null,
        sortDirection: 'asc',
        filterText: '',
        page: 1,
        pageSize: 10,

        init() {
            // Initialize
        },

        get filteredData() {
            if (!this.filterText) return this.data;

            const filter = this.filterText.toLowerCase();
            return this.data.filter(row => {
                return Object.values(row).some(value =>
                    String(value).toLowerCase().includes(filter)
                );
            });
        },

        get sortedData() {
            if (!this.sortColumn) return this.filteredData;

            return [...this.filteredData].sort((a, b) => {
                const aVal = a[this.sortColumn];
                const bVal = b[this.sortColumn];

                const result = aVal < bVal ? -1 : aVal > bVal ? 1 : 0;
                return this.sortDirection === 'asc' ? result : -result;
            });
        },

        get paginatedData() {
            const start = (this.page - 1) * this.pageSize;
            const end = start + this.pageSize;
            return this.sortedData.slice(start, end);
        },

        get totalPages() {
            return Math.ceil(this.sortedData.length / this.pageSize);
        },

        sort(column) {
            if (this.sortColumn === column) {
                this.sortDirection = this.sortDirection === 'asc' ? 'desc' : 'asc';
            } else {
                this.sortColumn = column;
                this.sortDirection = 'asc';
            }
        },

        nextPage() {
            if (this.page < this.totalPages) {
                this.page++;
            }
        },

        prevPage() {
            if (this.page > 1) {
                this.page--;
            }
        },

        getSortIcon(column) {
            if (this.sortColumn !== column) return 'bi-arrow-down-up';
            return this.sortDirection === 'asc' ? 'bi-sort-up' : 'bi-sort-down';
        }
    };
}

// =============================================================================
// EXPORT COMPONENTS
// =============================================================================

/**
 * Export all dashboard components for use in templates
 */
window.dashboardComponents = {
    // Widget Factory Functions
    agentHealthCard,
    executionMetricCard,
    securityPostureCard,
    taskQueueVisualization,

    // Refresh Control
    refreshControl,

    // Color Utilities
    getAgentColor,
    getExecutionColor,
    getSeverityColor,
    getPropertyColor,
    getStatusColor,

    // Chart Wrappers
    createPropertyChart,
    createLineChart,
    createBarChart,
    createGaugeChart,
    createPieChart,
    createStackedBarChart,

    // Utility Components
    dashboardCard,
    dataTable
};

// Initialize stores on page load
document.addEventListener('DOMContentLoaded', () => {
    console.log('Dashboard Components loaded');
});
