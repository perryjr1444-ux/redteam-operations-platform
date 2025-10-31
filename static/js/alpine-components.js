/**
 * Alpine.js Reactive Components
 * Modern, lightweight reactive components for Red Team C2
 *
 * Components:
 * - MetricsStore: Global state for live metrics
 * - ExecutionMonitor: Real-time execution tracking
 * - NotificationCenter: Toast notifications
 * - AgentStatus: AI agent health monitoring
 */

// Global Alpine Store for Metrics
document.addEventListener('alpine:init', () => {
    // Metrics Store - Global reactive state
    Alpine.store('metrics', {
        activeExercises: 0,
        systemHealth: 0,
        runningContainers: 0,
        uptime: '0d',
        lastUpdate: null,

        async fetch() {
            try {
                const response = await fetch('/api/metrics/live');
                const data = await response.json();

                this.activeExercises = data.active_exercises || 0;
                this.systemHealth = data.system_health || 0;
                this.runningContainers = data.running_containers || 0;
                this.uptime = data.uptime || '0d';
                this.lastUpdate = new Date();
            } catch (err) {
                console.error('Error fetching metrics:', err);
            }
        },

        startAutoRefresh(intervalMs = 5000) {
            this.fetch();
            setInterval(() => this.fetch(), intervalMs);
        }
    });

    // Agent Status Store - AI Agent health monitoring
    // NOTE: Dashboard pages use 'agentDashboard' store. This store is for base template badges.
    Alpine.store('agents', {
        agents: [],
        healthy: 0,
        unhealthy: 0,
        avgResponseTime: 0,

        async fetch() {
            try {
                const response = await fetch('/api/ai/agents/status');
                const data = await response.json();

                if (data.agents) {
                    this.agents = Object.entries(data.agents).map(([type, status]) => ({
                        type: type,
                        ...status
                    }));

                    this.healthy = this.agents.filter(a => a.is_healthy).length;
                    this.unhealthy = this.agents.filter(a => !a.is_healthy).length;

                    const responseTimes = this.agents.map(a => a.avg_response_time);
                    this.avgResponseTime = responseTimes.reduce((a, b) => a + b, 0) / responseTimes.length || 0;
                }
            } catch (err) {
                console.error('Error fetching agent status:', err);
            }
        },

        startAutoRefresh(intervalMs = 10000) {
            this.fetch();
            setInterval(() => this.fetch(), intervalMs);
        }
    });

    // Execution Monitor Store - Fractal execution tracking
    // NOTE: Dashboard pages use 'executionDashboard' store. This store is for base template badges.
    Alpine.store('execution', {
        activeExecutions: [],
        completedToday: 0,
        avgDuration: 0,

        async fetch() {
            try {
                const response = await fetch('/api/execution/active');
                const data = await response.json();

                this.activeExecutions = data.executions || [];
                this.completedToday = data.completed_today || 0;
                this.avgDuration = data.avg_duration || 0;
            } catch (err) {
                console.error('Error fetching executions:', err);
            }
        },

        startAutoRefresh(intervalMs = 3000) {
            this.fetch();
            setInterval(() => this.fetch(), intervalMs);
        }
    });

    // Notification Store - Toast notifications
    Alpine.store('notifications', {
        items: [],
        maxItems: 5,

        add(message, type = 'info', duration = 5000) {
            const id = Date.now();
            const notification = {
                id,
                message,
                type, // info, success, warning, error
                timestamp: new Date(),
                visible: true
            };

            this.items.unshift(notification);

            // Limit to max items
            if (this.items.length > this.maxItems) {
                this.items = this.items.slice(0, this.maxItems);
            }

            // Auto-remove after duration
            if (duration > 0) {
                setTimeout(() => this.remove(id), duration);
            }
        },

        remove(id) {
            const index = this.items.findIndex(item => item.id === id);
            if (index > -1) {
                this.items.splice(index, 1);
            }
        },

        clear() {
            this.items = [];
        },

        success(message) {
            this.add(message, 'success');
        },

        error(message) {
            this.add(message, 'error', 8000);
        },

        warning(message) {
            this.add(message, 'warning', 6000);
        },

        info(message) {
            this.add(message, 'info');
        }
    });
});

/**
 * Alpine Component: Metric Card
 * Reactive metric card with animated counter
 */
function metricCard(initialValue = 0, suffix = '') {
    return {
        value: initialValue,
        displayValue: initialValue,
        suffix: suffix,

        init() {
            this.$watch('value', (newValue, oldValue) => {
                this.animateCounter(oldValue, newValue);
            });
        },

        animateCounter(start, end, duration = 1000) {
            const increment = (end - start) / (duration / 16);
            let current = start;

            const timer = setInterval(() => {
                current += increment;
                if ((increment > 0 && current >= end) || (increment < 0 && current <= end)) {
                    this.displayValue = end;
                    clearInterval(timer);
                } else {
                    this.displayValue = Math.floor(current);
                }
            }, 16);
        },

        get formattedValue() {
            return this.displayValue + this.suffix;
        }
    };
}

/**
 * Alpine Component: Live Chart
 * Real-time updating Chart.js wrapper
 */
function liveChart(chartType, options = {}) {
    return {
        chart: null,
        chartType: chartType,
        options: options,

        init() {
            this.createChart();
        },

        createChart() {
            const ctx = this.$refs.canvas;
            if (!ctx) return;

            this.chart = new Chart(ctx, {
                type: this.chartType,
                data: this.options.data || {},
                options: this.options.chartOptions || {}
            });
        },

        updateData(newData) {
            if (!this.chart) return;

            this.chart.data = newData;
            this.chart.update('active');
        },

        addDataPoint(label, value) {
            if (!this.chart) return;

            this.chart.data.labels.push(label);
            this.chart.data.datasets[0].data.push(value);

            // Keep only last N points
            const maxPoints = this.options.maxPoints || 20;
            if (this.chart.data.labels.length > maxPoints) {
                this.chart.data.labels.shift();
                this.chart.data.datasets[0].data.shift();
            }

            this.chart.update('active');
        },

        destroy() {
            if (this.chart) {
                this.chart.destroy();
            }
        }
    };
}

/**
 * Alpine Component: Agent Status Card
 * Individual AI agent health status
 */
function agentStatusCard() {
    return {
        agent: {},

        init() {
            // Component initialized
        },

        get statusClass() {
            return this.agent.is_healthy ? 'status-healthy' : 'status-unhealthy';
        },

        get statusIcon() {
            return this.agent.is_healthy ? 'bi-check-circle-fill' : 'bi-exclamation-triangle-fill';
        },

        get uptimeColor() {
            const uptime = this.agent.uptime_percentage || 0;
            if (uptime >= 95) return 'text-success';
            if (uptime >= 80) return 'text-warning';
            return 'text-danger';
        },

        get responseTimeColor() {
            const time = this.agent.avg_response_time || 0;
            if (time < 100) return 'text-success';
            if (time < 500) return 'text-warning';
            return 'text-danger';
        }
    };
}

/**
 * Alpine Component: Execution Tree Visualizer
 * Fractal execution tree with real-time updates
 */
function executionTree() {
    return {
        rootNode: null,
        selectedNode: null,
        expandedNodes: new Set(),

        async loadTree(rootId) {
            try {
                const response = await fetch(`/api/execution/tree/${rootId}`);
                const data = await response.json();
                this.rootNode = data;
            } catch (err) {
                console.error('Error loading execution tree:', err);
            }
        },

        toggleNode(nodeId) {
            if (this.expandedNodes.has(nodeId)) {
                this.expandedNodes.delete(nodeId);
            } else {
                this.expandedNodes.add(nodeId);
            }
        },

        isExpanded(nodeId) {
            return this.expandedNodes.has(nodeId);
        },

        selectNode(node) {
            this.selectedNode = node;
        },

        getStatusClass(status) {
            const statusMap = {
                'pending': 'text-secondary',
                'running': 'text-primary',
                'completed': 'text-success',
                'failed': 'text-danger',
                'cancelled': 'text-warning'
            };
            return statusMap[status] || 'text-muted';
        },

        getStatusIcon(status) {
            const iconMap = {
                'pending': 'bi-clock',
                'running': 'bi-play-circle-fill',
                'completed': 'bi-check-circle-fill',
                'failed': 'bi-x-circle-fill',
                'cancelled': 'bi-dash-circle-fill'
            };
            return iconMap[status] || 'bi-circle';
        }
    };
}

/**
 * Alpine Component: Attack Chain Builder
 * Drag-and-drop attack chain construction
 */
function attackChainBuilder() {
    return {
        availableTools: [],
        chain: {
            name: '',
            steps: []
        },
        draggedTool: null,

        async init() {
            await this.loadTools();
        },

        async loadTools() {
            try {
                const response = await fetch('/api/tools');
                const data = await response.json();
                this.availableTools = data.tools || [];
            } catch (err) {
                console.error('Error loading tools:', err);
            }
        },

        startDrag(tool, event) {
            this.draggedTool = tool;
            event.dataTransfer.effectAllowed = 'copy';
        },

        allowDrop(event) {
            event.preventDefault();
            event.dataTransfer.dropEffect = 'copy';
        },

        drop(event) {
            event.preventDefault();
            if (this.draggedTool) {
                this.addStep(this.draggedTool);
                this.draggedTool = null;
            }
        },

        addStep(tool) {
            this.chain.steps.push({
                id: `step_${this.chain.steps.length + 1}`,
                tool: tool.name,
                args: {},
                parallel: false,
                dependencies: []
            });
        },

        removeStep(index) {
            this.chain.steps.splice(index, 1);
        },

        moveStepUp(index) {
            if (index > 0) {
                [this.chain.steps[index], this.chain.steps[index - 1]] =
                [this.chain.steps[index - 1], this.chain.steps[index]];
            }
        },

        moveStepDown(index) {
            if (index < this.chain.steps.length - 1) {
                [this.chain.steps[index], this.chain.steps[index + 1]] =
                [this.chain.steps[index + 1], this.chain.steps[index]];
            }
        },

        async saveChain() {
            try {
                const response = await fetch('/api/chains', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(this.chain)
                });

                if (response.ok) {
                    Alpine.store('notifications').success('Attack chain saved successfully!');
                    this.resetChain();
                } else {
                    Alpine.store('notifications').error('Failed to save attack chain');
                }
            } catch (err) {
                console.error('Error saving chain:', err);
                Alpine.store('notifications').error('Error saving attack chain');
            }
        },

        resetChain() {
            this.chain = { name: '', steps: [] };
        }
    };
}

// Export components for use in templates
window.AlpineComponents = {
    metricCard,
    liveChart,
    agentStatusCard,
    executionTree,
    attackChainBuilder
};
