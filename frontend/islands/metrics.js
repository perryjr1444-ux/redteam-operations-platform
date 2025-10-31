/**
 * Metrics Dashboard Island - D3.js Live Metrics
 */

import { h, Component } from 'preact';
import * as d3 from 'd3';
import wsService from '../services/websocket.js';

export default class MetricsIsland extends Component {
  constructor(props) {
    super(props);
    this.state = {
      metrics: {
        activeExercises: 0,
        systemHealth: 0,
        runningTools: 0,
        completedChains: 0,
        successRate: 0
      },
      history: []
    };
    this.chartRef = null;
    this.updateInterval = null;
  }

  componentDidMount() {
    this.fetchMetrics();
    this.initChart();
    this.connectWebSocket();

    // Update every 5 seconds
    this.updateInterval = setInterval(() => this.fetchMetrics(), 5000);
  }

  componentWillUnmount() {
    if (this.updateInterval) {
      clearInterval(this.updateInterval);
    }
  }

  async fetchMetrics() {
    try {
      const response = await fetch('/api/metrics');
      const data = await response.json();

      this.setState({
        metrics: data,
        history: [...this.state.history, {
          timestamp: new Date(),
          ...data
        }].slice(-50) // Keep last 50 data points
      });

      this.updateChart();
    } catch (error) {
      console.error('Failed to fetch metrics:', error);
    }
  }

  connectWebSocket() {
    if (!wsService.socket) {
      wsService.connect();
    }

    // Real-time metric updates
    wsService.on('metric_update', (data) => {
      this.setState({
        metrics: { ...this.state.metrics, ...data }
      });
    });
  }

  initChart() {
    if (!this.chartRef) return;

    const width = this.chartRef.clientWidth;
    const height = 200;
    const margin = { top: 20, right: 30, bottom: 30, left: 50 };

    const svg = d3.select(this.chartRef)
      .append('svg')
      .attr('width', width)
      .attr('height', height);

    this.svg = svg;
    this.chartWidth = width;
    this.chartHeight = height;
    this.chartMargin = margin;
  }

  updateChart() {
    if (!this.svg || this.state.history.length < 2) return;

    const { history } = this.state;
    const { chartWidth, chartHeight, chartMargin } = this;

    const width = chartWidth - chartMargin.left - chartMargin.right;
    const height = chartHeight - chartMargin.top - chartMargin.bottom;

    // Clear existing
    this.svg.selectAll('*').remove();

    // Create scales
    const x = d3.scaleTime()
      .domain(d3.extent(history, d => d.timestamp))
      .range([chartMargin.left, width + chartMargin.left]);

    const y = d3.scaleLinear()
      .domain([0, d3.max(history, d => d.activeExercises) || 10])
      .range([height + chartMargin.top, chartMargin.top]);

    // Create line generator
    const line = d3.line()
      .x(d => x(d.timestamp))
      .y(d => y(d.activeExercises))
      .curve(d3.curveMonotoneX);

    // Draw grid
    this.svg.append('g')
      .attr('class', 'grid')
      .attr('transform', `translate(0,${height + chartMargin.top})`)
      .call(d3.axisBottom(x).tickSize(-height).tickFormat(''))
      .style('stroke', '#2a3f5f')
      .style('stroke-opacity', 0.3);

    // Draw line
    this.svg.append('path')
      .datum(history)
      .attr('fill', 'none')
      .attr('stroke', '#4caf50')
      .attr('stroke-width', 2)
      .attr('d', line);

    // Draw dots
    this.svg.selectAll('.dot')
      .data(history)
      .enter().append('circle')
      .attr('class', 'dot')
      .attr('cx', d => x(d.timestamp))
      .attr('cy', d => y(d.activeExercises))
      .attr('r', 3)
      .attr('fill', '#4caf50')
      .attr('stroke', '#0a0f14')
      .attr('stroke-width', 2);

    // Add axes
    this.svg.append('g')
      .attr('transform', `translate(0,${height + chartMargin.top})`)
      .call(d3.axisBottom(x).ticks(5))
      .style('color', '#8b949e');

    this.svg.append('g')
      .attr('transform', `translate(${chartMargin.left},0)`)
      .call(d3.axisLeft(y))
      .style('color', '#8b949e');
  }

  render() {
    const { metrics } = this.state;

    return h('div', { class: 'metrics-island' },
      // Metric cards
      h('div', { class: 'grid grid-cols-2 md:grid-cols-4 gap-4 mb-6' },
        this.renderMetricCard('Active Exercises', metrics.activeExercises, 'shield-check', 'military-green'),
        this.renderMetricCard('System Health', `${metrics.systemHealth}%`, 'heart-pulse', metrics.systemHealth > 80 ? 'military-green' : 'military-amber'),
        this.renderMetricCard('Running Tools', metrics.runningTools, 'boxes', 'military-green'),
        this.renderMetricCard('Success Rate', `${metrics.successRate}%`, 'graph-up', metrics.successRate > 70 ? 'military-green' : 'military-red')
      ),

      // Chart
      h('div', { class: 'bg-tactical-card rounded-lg border border-tactical-border p-4' },
        h('h3', { class: 'text-tactical-text font-display text-lg mb-4' }, 'Activity Timeline'),
        h('div', { ref: ref => this.chartRef = ref })
      )
    );
  }

  renderMetricCard(label, value, icon, color) {
    return h('div', { class: 'bg-tactical-card rounded-lg border border-tactical-border p-4 hover:border-military-green transition-colors' },
      h('div', { class: 'flex items-center justify-between mb-2' },
        h('span', { class: 'text-tactical-muted text-sm font-mono' }, label),
        h('i', { class: `bi bi-${icon} text-${color}` })
      ),
      h('div', { class: `text-3xl font-bold text-${color}` }, value)
    );
  }
}
