/**
 * Chain Execution Monitor - Real-time WebSocket-based monitoring
 *
 * Features:
 * - Live progress updates
 * - Step-by-step execution logs
 * - Real-time status changes
 * - Error highlighting
 * - Auto-reconnect on connection loss
 *
 * Usage:
 * <div x-data="chainMonitor('exec_abc123')">
 *   <!-- Monitor UI here -->
 * </div>
 */

/**
 * Chain Execution Monitor Alpine.js Component
 * @param {string} executionId - Chain execution ID to monitor
 * @returns {object} Alpine.js component data
 */
function chainMonitor(executionId) {
    return {
        // Connection state
        executionId: executionId,
        ws: null,
        connected: false,
        reconnecting: false,
        reconnectAttempts: 0,
        maxReconnectAttempts: 5,
        reconnectDelay: 2000,

        // Execution data
        status: 'pending',
        chainName: '',
        totalSteps: 0,
        completedSteps: 0,
        failedSteps: 0,
        skippedSteps: 0,
        progress: 0,
        startTime: null,
        endTime: null,
        duration: null,
        errorMessage: null,

        // Step execution log
        steps: [],
        activeStepIndex: null,

        // UI state
        autoScroll: true,
        showDetails: true,
        filter: 'all', // all, completed, failed, pending

        /**
         * Initialize component
         */
        init() {
            console.log(`[ChainMonitor] Initializing for execution: ${this.executionId}`);
            this.connect();

            // Cleanup on component destroy
            this.$watch('connected', (value) => {
                if (value) {
                    console.log('[ChainMonitor] Connected to WebSocket');
                } else {
                    console.log('[ChainMonitor] Disconnected from WebSocket');
                }
            });
        },

        /**
         * Connect to WebSocket
         */
        connect() {
            if (this.ws && this.ws.readyState === WebSocket.OPEN) {
                console.log('[ChainMonitor] Already connected');
                return;
            }

            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            const wsUrl = `${protocol}//${window.location.host}/ws/chain-execution/${this.executionId}`;

            console.log(`[ChainMonitor] Connecting to: ${wsUrl}`);

            try {
                this.ws = new WebSocket(wsUrl);

                this.ws.onopen = () => {
                    this.connected = true;
                    this.reconnecting = false;
                    this.reconnectAttempts = 0;
                    console.log('[ChainMonitor] WebSocket connected');
                };

                this.ws.onmessage = (event) => {
                    this.handleMessage(event.data);
                };

                this.ws.onerror = (error) => {
                    console.error('[ChainMonitor] WebSocket error:', error);
                };

                this.ws.onclose = (event) => {
                    this.connected = false;
                    console.log(`[ChainMonitor] WebSocket closed: ${event.code} - ${event.reason}`);

                    // Attempt to reconnect if not a normal closure
                    if (event.code !== 1000 && this.reconnectAttempts < this.maxReconnectAttempts) {
                        this.scheduleReconnect();
                    }
                };
            } catch (error) {
                console.error('[ChainMonitor] Failed to create WebSocket:', error);
                this.scheduleReconnect();
            }
        },

        /**
         * Disconnect from WebSocket
         */
        disconnect() {
            if (this.ws) {
                console.log('[ChainMonitor] Disconnecting WebSocket');
                this.ws.close(1000, 'Client disconnect');
                this.ws = null;
                this.connected = false;
            }
        },

        /**
         * Schedule reconnection attempt
         */
        scheduleReconnect() {
            if (this.reconnectAttempts >= this.maxReconnectAttempts) {
                console.error('[ChainMonitor] Max reconnect attempts reached');
                return;
            }

            this.reconnecting = true;
            this.reconnectAttempts++;

            const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1);
            console.log(`[ChainMonitor] Reconnecting in ${delay}ms (attempt ${this.reconnectAttempts}/${this.maxReconnectAttempts})`);

            setTimeout(() => {
                this.connect();
            }, delay);
        },

        /**
         * Handle incoming WebSocket message
         * @param {string} data - Raw message data
         */
        handleMessage(data) {
            try {
                const message = JSON.parse(data);
                console.log('[ChainMonitor] Received:', message);

                switch (message.type) {
                    case 'execution_update':
                        this.handleExecutionUpdate(message.data);
                        break;
                    case 'step_start':
                        this.handleStepStart(message.data);
                        break;
                    case 'step_complete':
                        this.handleStepComplete(message.data);
                        break;
                    case 'step_failed':
                        this.handleStepFailed(message.data);
                        break;
                    case 'execution_complete':
                        this.handleExecutionComplete(message.data);
                        break;
                    case 'execution_failed':
                        this.handleExecutionFailed(message.data);
                        break;
                    case 'error':
                        this.handleError(message.data);
                        break;
                    case 'ping':
                        // Respond to keepalive
                        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
                            this.ws.send(JSON.stringify({ type: 'pong' }));
                        }
                        break;
                    default:
                        console.warn('[ChainMonitor] Unknown message type:', message.type);
                }
            } catch (error) {
                console.error('[ChainMonitor] Failed to parse message:', error);
            }
        },

        /**
         * Handle execution status update
         */
        handleExecutionUpdate(data) {
            this.status = data.status || this.status;
            this.chainName = data.chain_name || this.chainName;
            this.totalSteps = data.total_steps || this.totalSteps;
            this.completedSteps = data.completed_steps || this.completedSteps;
            this.failedSteps = data.failed_steps || this.failedSteps;
            this.skippedSteps = data.skipped_steps || this.skippedSteps;
            this.startTime = data.start_time || this.startTime;
            this.endTime = data.end_time || this.endTime;
            this.duration = data.duration || this.duration;

            // Calculate progress
            if (this.totalSteps > 0) {
                this.progress = Math.round(
                    ((this.completedSteps + this.failedSteps + this.skippedSteps) / this.totalSteps) * 100
                );
            }
        },

        /**
         * Handle step start event
         */
        handleStepStart(data) {
            const stepIndex = data.step_index;

            // Update or add step
            if (this.steps[stepIndex]) {
                this.steps[stepIndex].status = 'running';
                this.steps[stepIndex].start_time = data.start_time;
            } else {
                this.steps.push({
                    index: stepIndex,
                    name: data.step_name,
                    tool: data.tool,
                    status: 'running',
                    start_time: data.start_time,
                    end_time: null,
                    duration: null,
                    output: [],
                    error: null
                });
            }

            this.activeStepIndex = stepIndex;
            this.status = 'running';
            this.scrollToBottom();
        },

        /**
         * Handle step completion
         */
        handleStepComplete(data) {
            const stepIndex = data.step_index;

            if (this.steps[stepIndex]) {
                this.steps[stepIndex].status = 'completed';
                this.steps[stepIndex].end_time = data.end_time;
                this.steps[stepIndex].duration = data.duration;
                this.steps[stepIndex].output = data.output || [];

                this.completedSteps++;
                this.updateProgress();
            }

            this.scrollToBottom();
        },

        /**
         * Handle step failure
         */
        handleStepFailed(data) {
            const stepIndex = data.step_index;

            if (this.steps[stepIndex]) {
                this.steps[stepIndex].status = 'failed';
                this.steps[stepIndex].end_time = data.end_time;
                this.steps[stepIndex].duration = data.duration;
                this.steps[stepIndex].error = data.error;
                this.steps[stepIndex].output = data.output || [];

                this.failedSteps++;
                this.updateProgress();
            }

            this.scrollToBottom();
        },

        /**
         * Handle execution completion
         */
        handleExecutionComplete(data) {
            this.status = 'completed';
            this.endTime = data.end_time;
            this.duration = data.duration;
            this.progress = 100;
            this.activeStepIndex = null;

            console.log('[ChainMonitor] Execution completed successfully');

            // Show notification
            if (window.Alpine && window.Alpine.store) {
                const notificationStore = window.Alpine.store('notifications');
                if (notificationStore) {
                    notificationStore.add({
                        type: 'success',
                        message: `Chain execution completed: ${this.chainName}`,
                        duration: 5000
                    });
                }
            }
        },

        /**
         * Handle execution failure
         */
        handleExecutionFailed(data) {
            this.status = 'failed';
            this.endTime = data.end_time;
            this.duration = data.duration;
            this.errorMessage = data.error;
            this.activeStepIndex = null;

            console.error('[ChainMonitor] Execution failed:', data.error);

            // Show notification
            if (window.Alpine && window.Alpine.store) {
                const notificationStore = window.Alpine.store('notifications');
                if (notificationStore) {
                    notificationStore.add({
                        type: 'error',
                        message: `Chain execution failed: ${data.error}`,
                        duration: 10000
                    });
                }
            }
        },

        /**
         * Handle error message
         */
        handleError(data) {
            console.error('[ChainMonitor] Error:', data.message);
            this.errorMessage = data.message;
        },

        /**
         * Update progress percentage
         */
        updateProgress() {
            if (this.totalSteps > 0) {
                this.progress = Math.round(
                    ((this.completedSteps + this.failedSteps + this.skippedSteps) / this.totalSteps) * 100
                );
            }
        },

        /**
         * Scroll to bottom of log (if auto-scroll enabled)
         */
        scrollToBottom() {
            if (this.autoScroll) {
                this.$nextTick(() => {
                    const logContainer = this.$refs.logContainer;
                    if (logContainer) {
                        logContainer.scrollTop = logContainer.scrollHeight;
                    }
                });
            }
        },

        /**
         * Get filtered steps based on current filter
         */
        get filteredSteps() {
            if (this.filter === 'all') {
                return this.steps;
            }
            return this.steps.filter(step => step.status === this.filter);
        },

        /**
         * Get status badge color class
         */
        getStatusClass(status) {
            const classes = {
                'pending': 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300',
                'running': 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-300',
                'completed': 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-300',
                'failed': 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-300',
                'skipped': 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-300',
                'cancelled': 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300'
            };
            return classes[status] || classes['pending'];
        },

        /**
         * Get progress bar color class
         */
        getProgressBarClass() {
            if (this.status === 'failed') {
                return 'bg-red-600';
            } else if (this.status === 'completed') {
                return 'bg-green-600';
            } else if (this.status === 'running') {
                return 'bg-blue-600';
            }
            return 'bg-gray-600';
        },

        /**
         * Format duration in seconds to human-readable format
         */
        formatDuration(seconds) {
            if (!seconds) return '-';

            if (seconds < 60) {
                return `${seconds.toFixed(1)}s`;
            } else if (seconds < 3600) {
                const minutes = Math.floor(seconds / 60);
                const secs = Math.floor(seconds % 60);
                return `${minutes}m ${secs}s`;
            } else {
                const hours = Math.floor(seconds / 3600);
                const minutes = Math.floor((seconds % 3600) / 60);
                return `${hours}h ${minutes}m`;
            }
        },

        /**
         * Format timestamp to human-readable format
         */
        formatTimestamp(timestamp) {
            if (!timestamp) return '-';
            const date = new Date(timestamp);
            return date.toLocaleTimeString();
        },

        /**
         * Toggle auto-scroll
         */
        toggleAutoScroll() {
            this.autoScroll = !this.autoScroll;
            if (this.autoScroll) {
                this.scrollToBottom();
            }
        },

        /**
         * Toggle details visibility
         */
        toggleDetails() {
            this.showDetails = !this.showDetails;
        },

        /**
         * Set filter
         */
        setFilter(filter) {
            this.filter = filter;
        },

        /**
         * Cleanup on destroy
         */
        destroy() {
            console.log('[ChainMonitor] Destroying component');
            this.disconnect();
        }
    };
}

// Export for module usage
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { chainMonitor };
}
