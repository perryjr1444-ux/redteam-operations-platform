/**
 * Alpine.js Enhanced Components Initialization
 * Auto-starts stores and handles global setup
 */

(function() {
    'use strict';

    // Wait for Alpine to be ready
    document.addEventListener('alpine:init', () => {
        console.log('[Enhanced] Alpine.js initialized');
    });

    // Initialize stores when DOM is ready
    document.addEventListener('DOMContentLoaded', () => {
        console.log('[Enhanced] Initializing Alpine stores...');

        // Check if Alpine is available
        if (typeof Alpine === 'undefined') {
            console.error('[Enhanced] Alpine.js not loaded!');
            return;
        }

        // Start auto-refresh for all stores
        try {
            // Metrics store - 5 second refresh
            if (Alpine.store('metrics')) {
                Alpine.store('metrics').startAutoRefresh(5000);
                console.log('[Enhanced] Metrics store initialized (5s refresh)');
            }

            // Agents store - 10 second refresh
            // NOTE: This is for base template badges. Dashboards use their own stores.
            if (Alpine.store('agents')) {
                Alpine.store('agents').startAutoRefresh(10000);
                console.log('[Enhanced] Agents store initialized (10s refresh)');
            }

            // Execution store - 3 second refresh
            // NOTE: This is for base template badges. Dashboards use their own stores.
            if (Alpine.store('execution')) {
                Alpine.store('execution').startAutoRefresh(3000);
                console.log('[Enhanced] Execution store initialized (3s refresh)');
            }

            // Welcome notification
            setTimeout(() => {
                if (Alpine.store('notifications')) {
                    Alpine.store('notifications').info('Red Team C2 Enhanced UI Loaded');
                }
            }, 500);

            console.log('[Enhanced] All stores initialized successfully');

        } catch (error) {
            console.error('[Enhanced] Error initializing stores:', error);
        }
    });

    // Global error handler for fetch errors
    window.addEventListener('unhandledrejection', (event) => {
        console.error('[Enhanced] Unhandled promise rejection:', event.reason);

        // Show notification if available
        if (typeof Alpine !== 'undefined' && Alpine.store('notifications')) {
            Alpine.store('notifications').error('Network error - check console');
        }
    });

    console.log('[Enhanced] Init script loaded');
})();
