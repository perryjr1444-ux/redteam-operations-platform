/**
 * Chart.js Data Visualizations
 * Real-time animated charts for Red Team metrics
 */

// Cyberpunk color scheme
const chartColors = {
    green: '#00ff00',
    cyan: '#00ffff',
    pink: '#ff00ff',
    red: '#ff0040',
    yellow: '#ffff00',
    bg: 'rgba(10, 14, 26, 0.8)'
};

// Global chart config
Chart.defaults.color = '#00ff00';
Chart.defaults.borderColor = 'rgba(0, 255, 0, 0.1)';
Chart.defaults.font.family = '"JetBrains Mono", monospace';

/**
 * Create Attack Success Rate Pie Chart
 */
function createSuccessRateChart(canvasId, successRate) {
    const ctx = document.getElementById(canvasId);
    if (!ctx) return;

    new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: ['Success', 'Failed'],
            datasets: [{
                data: [successRate, 100 - successRate],
                backgroundColor: [chartColors.green, chartColors.red],
                borderColor: [chartColors.green, chartColors.red],
                borderWidth: 2,
                hoverOffset: 10
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: {
                        color: chartColors.green,
                        font: { size: 12, weight: 'bold' },
                        padding: 15
                    }
                },
                tooltip: {
                    backgroundColor: chartColors.bg,
                    titleColor: chartColors.green,
                    bodyColor: chartColors.cyan,
                    borderColor: chartColors.green,
                    borderWidth: 1,
                    padding: 10
                }
            },
            animation: {
                animateRotate: true,
                animateScale: true,
                duration: 2000,
                easing: 'easeInOutQuart'
            }
        }
    });
}

/**
 * Create Exercise Timeline Chart
 */
function createTimelineChart(canvasId, data) {
    const ctx = document.getElementById(canvasId);
    if (!ctx) return;

    new Chart(ctx, {
        type: 'line',
        data: {
            labels: data.labels,
            datasets: [{
                label: 'Exercises Completed',
                data: data.values,
                borderColor: chartColors.green,
                backgroundColor: 'rgba(0, 255, 0, 0.1)',
                borderWidth: 2,
                fill: true,
                tension: 0.4,
                pointBackgroundColor: chartColors.green,
                pointBorderColor: chartColors.green,
                pointHoverBackgroundColor: chartColors.cyan,
                pointHoverBorderColor: chartColors.cyan,
                pointRadius: 5,
                pointHoverRadius: 8
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: { color: chartColors.green, stepSize: 1 },
                    grid: { color: 'rgba(0, 255, 0, 0.1)' }
                },
                x: {
                    ticks: { color: chartColors.green },
                    grid: { color: 'rgba(0, 255, 0, 0.1)' }
                }
            },
            plugins: {
                legend: {
                    labels: { color: chartColors.green, font: { weight: 'bold' } }
                },
                tooltip: {
                    backgroundColor: chartColors.bg,
                    titleColor: chartColors.green,
                    bodyColor: chartColors.cyan,
                    borderColor: chartColors.green,
                    borderWidth: 1
                }
            },
            animation: {
                duration: 2000,
                easing: 'easeInOutQuart'
            }
        }
    });
}

/**
 * Create Attack Type Distribution Bar Chart
 */
function createAttackTypeChart(canvasId, data) {
    const ctx = document.getElementById(canvasId);
    if (!ctx) return;

    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: data.labels,
            datasets: [{
                label: 'Attack Operations',
                data: data.values,
                backgroundColor: [
                    chartColors.green,
                    chartColors.cyan,
                    chartColors.pink,
                    chartColors.yellow
                ],
                borderColor: [
                    chartColors.green,
                    chartColors.cyan,
                    chartColors.pink,
                    chartColors.yellow
                ],
                borderWidth: 2
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: { color: chartColors.green, stepSize: 1 },
                    grid: { color: 'rgba(0, 255, 0, 0.1)' }
                },
                x: {
                    ticks: { color: chartColors.green },
                    grid: { display: false }
                }
            },
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    backgroundColor: chartColors.bg,
                    titleColor: chartColors.green,
                    bodyColor: chartColors.cyan,
                    borderColor: chartColors.green,
                    borderWidth: 1
                }
            },
            animation: {
                duration: 2000,
                easing: 'easeInOutBounce'
            }
        }
    });
}

/**
 * Animate counter (for metric cards)
 */
function animateCounter(element, target, duration = 2000) {
    const start = parseInt(element.textContent) || 0;
    const increment = (target - start) / (duration / 16);
    let current = start;

    const timer = setInterval(() => {
        current += increment;
        if ((increment > 0 && current >= target) || (increment < 0 && current <= target)) {
            element.textContent = target;
            clearInterval(timer);
        } else {
            element.textContent = Math.floor(current);
        }
    }, 16);
}

/**
 * Update live metrics
 */
function updateLiveMetrics() {
    fetch('/api/metrics/live')
        .then(response => response.json())
        .then(data => {
            // Update counters with animation
            const activeEx = document.getElementById('active-exercises');
            if (activeEx) animateCounter(activeEx, data.active_exercises || 0);

            const systemHealth = document.getElementById('system-health');
            if (systemHealth) systemHealth.textContent = `${data.system_health || 0}%`;

            const containers = document.getElementById('running-containers');
            if (containers) animateCounter(containers, data.running_containers || 0);

            const uptime = document.getElementById('uptime');
            if (uptime) uptime.textContent = data.uptime || '0d';
        })
        .catch(err => console.error('Error updating metrics:', err));
}

// Auto-refresh metrics every 5 seconds
setInterval(updateLiveMetrics, 5000);
