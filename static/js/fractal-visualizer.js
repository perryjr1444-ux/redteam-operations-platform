/**
 * Fractal Execution Tree Visualizer
 * D3.js-based interactive visualization for fractal orchestrator execution
 *
 * Features:
 * - Real-time tree rendering
 * - Node status coloring (pending/running/completed/failed)
 * - Interactive pan & zoom
 * - Click to expand/collapse nodes
 * - Tooltips with execution details
 * - WebSocket updates for live data
 */

class FractalVisualizer {
    constructor(containerId, options = {}) {
        this.containerId = containerId;
        this.container = document.getElementById(containerId);

        // Configuration
        this.config = {
            width: options.width || this.container.clientWidth,
            height: options.height || this.container.clientHeight || 600,
            nodeRadius: options.nodeRadius || 8,
            levelSpacing: options.levelSpacing || 120,
            nodeSpacing: options.nodeSpacing || 30,
            animationDuration: options.animationDuration || 500,
            colors: {
                pending: '#6c757d',
                running: '#0dcaf0',
                completed: '#198754',
                failed: '#dc3545',
                strategic: '#7c3aed',
                tactical: '#2563eb',
                operational: '#059669'
            },
            ...options
        };

        // State
        this.data = null;
        this.svg = null;
        this.g = null;
        this.zoom = null;
        this.root = null;
        this.treeLayout = null;

        // WebSocket
        this.ws = null;
        this.wsUrl = options.wsUrl || `ws://${window.location.host}/ws/execution`;

        this.initialize();
    }

    initialize() {
        // Clear container
        this.container.innerHTML = '';

        // Create SVG
        this.svg = d3.select(`#${this.containerId}`)
            .append('svg')
            .attr('width', this.config.width)
            .attr('height', this.config.height)
            .attr('class', 'fractal-visualizer');

        // Add definitions for gradients and patterns
        this.addDefinitions();

        // Create main group for zoom/pan
        this.g = this.svg.append('g')
            .attr('class', 'tree-container');

        // Setup zoom behavior
        this.zoom = d3.zoom()
            .scaleExtent([0.1, 3])
            .on('zoom', (event) => {
                this.g.attr('transform', event.transform);
            });

        this.svg.call(this.zoom);

        // Create tree layout
        this.treeLayout = d3.tree()
            .nodeSize([this.config.nodeSpacing, this.config.levelSpacing])
            .separation((a, b) => a.parent === b.parent ? 1 : 1.2);

        console.log('[FractalVisualizer] Initialized');
    }

    addDefinitions() {
        const defs = this.svg.append('defs');

        // Glow filter for active nodes
        const filter = defs.append('filter')
            .attr('id', 'glow')
            .attr('x', '-50%')
            .attr('y', '-50%')
            .attr('width', '200%')
            .attr('height', '200%');

        filter.append('feGaussianBlur')
            .attr('stdDeviation', '3')
            .attr('result', 'coloredBlur');

        const feMerge = filter.append('feMerge');
        feMerge.append('feMergeNode').attr('in', 'coloredBlur');
        feMerge.append('feMergeNode').attr('in', 'SourceGraphic');

        // Arrow markers for links
        ['pending', 'running', 'completed', 'failed'].forEach(status => {
            defs.append('marker')
                .attr('id', `arrow-${status}`)
                .attr('viewBox', '0 -5 10 10')
                .attr('refX', 20)
                .attr('refY', 0)
                .attr('markerWidth', 6)
                .attr('markerHeight', 6)
                .attr('orient', 'auto')
                .append('path')
                .attr('d', 'M0,-5L10,0L0,5')
                .attr('fill', this.config.colors[status]);
        });
    }

    async loadData(rootId) {
        try {
            const response = await fetch(`/api/execution/tree/${rootId}`);
            if (!response.ok) {
                throw new Error(`Failed to load execution tree: ${response.statusText}`);
            }

            this.data = await response.json();
            this.render();

        } catch (error) {
            console.error('[FractalVisualizer] Load error:', error);
            this.showError(error.message);
        }
    }

    render() {
        if (!this.data) {
            console.warn('[FractalVisualizer] No data to render');
            return;
        }

        // Convert data to hierarchy
        this.root = d3.hierarchy(this.data, d => d.children);

        // Apply tree layout
        this.treeLayout(this.root);

        // Center the tree
        const centerX = this.config.width / 2;
        const centerY = 50;
        this.root.x0 = centerX;
        this.root.y0 = centerY;

        // Render links
        this.renderLinks();

        // Render nodes
        this.renderNodes();

        // Center view on root
        this.centerOnRoot();

        console.log('[FractalVisualizer] Rendered tree with', this.root.descendants().length, 'nodes');
    }

    renderLinks() {
        const links = this.root.links();

        // Create link generator
        const linkGenerator = d3.linkVertical()
            .x(d => d.x)
            .y(d => d.y);

        // Update selection
        const link = this.g.selectAll('.link')
            .data(links, d => d.target.data.id);

        // Exit
        link.exit()
            .transition()
            .duration(this.config.animationDuration)
            .style('opacity', 0)
            .remove();

        // Enter + Update
        const linkEnter = link.enter()
            .append('path')
            .attr('class', 'link')
            .attr('d', linkGenerator)
            .style('fill', 'none')
            .style('stroke-width', 2)
            .style('opacity', 0);

        linkEnter.merge(link)
            .transition()
            .duration(this.config.animationDuration)
            .attr('d', linkGenerator)
            .style('stroke', d => this.getNodeColor(d.target.data.status))
            .style('opacity', 0.6)
            .attr('marker-end', d => `url(#arrow-${d.target.data.status})`);
    }

    renderNodes() {
        const nodes = this.root.descendants();

        // Update selection
        const node = this.g.selectAll('.node')
            .data(nodes, d => d.data.id);

        // Exit
        node.exit()
            .transition()
            .duration(this.config.animationDuration)
            .style('opacity', 0)
            .remove();

        // Enter
        const nodeEnter = node.enter()
            .append('g')
            .attr('class', 'node')
            .attr('transform', d => `translate(${d.x},${d.y})`)
            .style('opacity', 0)
            .on('click', (event, d) => this.onNodeClick(event, d))
            .on('mouseenter', (event, d) => this.showTooltip(event, d))
            .on('mouseleave', () => this.hideTooltip());

        // Add circles
        nodeEnter.append('circle')
            .attr('r', this.config.nodeRadius)
            .style('fill', d => this.getNodeColor(d.data.status))
            .style('stroke', '#fff')
            .style('stroke-width', 2);

        // Add status icons
        nodeEnter.append('text')
            .attr('class', 'node-icon')
            .attr('text-anchor', 'middle')
            .attr('dy', '0.35em')
            .style('fill', '#fff')
            .style('font-size', '10px')
            .style('pointer-events', 'none')
            .text(d => this.getNodeIcon(d.data.status));

        // Add labels
        nodeEnter.append('text')
            .attr('class', 'node-label')
            .attr('dy', '1.8em')
            .attr('text-anchor', 'middle')
            .style('font-size', '11px')
            .style('fill', '#e0e0e0')
            .text(d => d.data.type || 'Unknown');

        // Add level badges
        nodeEnter.append('text')
            .attr('class', 'level-badge')
            .attr('dy', '-1.2em')
            .attr('text-anchor', 'middle')
            .style('font-size', '9px')
            .style('fill', d => this.getLevelColor(d.data.level))
            .text(d => d.data.level ? d.data.level.charAt(0).toUpperCase() : '');

        // Update + Enter
        nodeEnter.merge(node)
            .transition()
            .duration(this.config.animationDuration)
            .attr('transform', d => `translate(${d.x},${d.y})`)
            .style('opacity', 1);

        // Update circle colors
        this.g.selectAll('.node circle')
            .transition()
            .duration(this.config.animationDuration)
            .style('fill', d => this.getNodeColor(d.data.status))
            .style('filter', d => d.data.status === 'running' ? 'url(#glow)' : 'none');
    }

    getNodeColor(status) {
        return this.config.colors[status] || '#6c757d';
    }

    getLevelColor(level) {
        return this.config.colors[level] || '#6c757d';
    }

    getNodeIcon(status) {
        const icons = {
            pending: '⏳',
            running: '▶',
            completed: '✓',
            failed: '✗'
        };
        return icons[status] || '●';
    }

    onNodeClick(event, d) {
        console.log('[FractalVisualizer] Node clicked:', d.data);

        // Emit custom event
        this.container.dispatchEvent(new CustomEvent('nodeClick', {
            detail: { node: d.data }
        }));

        // Toggle children if exists
        if (d.children || d._children) {
            this.toggleNode(d);
        }
    }

    toggleNode(d) {
        if (d.children) {
            d._children = d.children;
            d.children = null;
        } else {
            d.children = d._children;
            d._children = null;
        }
        this.render();
    }

    showTooltip(event, d) {
        const tooltip = this.getOrCreateTooltip();

        const html = `
            <div class="tooltip-header">${d.data.type}</div>
            <div class="tooltip-body">
                <div><strong>ID:</strong> ${d.data.id}</div>
                <div><strong>Status:</strong> <span class="badge bg-${this.getStatusClass(d.data.status)}">${d.data.status}</span></div>
                <div><strong>Level:</strong> ${d.data.level || 'N/A'}</div>
                ${d.data.result ? `<div><strong>Result:</strong> ${JSON.stringify(d.data.result).substring(0, 50)}...</div>` : ''}
            </div>
        `;

        tooltip
            .style('opacity', 1)
            .html(html)
            .style('left', (event.pageX + 10) + 'px')
            .style('top', (event.pageY - 10) + 'px');
    }

    hideTooltip() {
        this.getOrCreateTooltip()
            .style('opacity', 0);
    }

    getOrCreateTooltip() {
        let tooltip = d3.select('.fractal-tooltip');

        if (tooltip.empty()) {
            tooltip = d3.select('body')
                .append('div')
                .attr('class', 'fractal-tooltip')
                .style('position', 'absolute')
                .style('opacity', 0)
                .style('background', 'rgba(0, 0, 0, 0.9)')
                .style('color', '#fff')
                .style('padding', '10px')
                .style('border-radius', '4px')
                .style('font-size', '12px')
                .style('pointer-events', 'none')
                .style('z-index', 1000);
        }

        return tooltip;
    }

    getStatusClass(status) {
        const classes = {
            pending: 'secondary',
            running: 'info',
            completed: 'success',
            failed: 'danger'
        };
        return classes[status] || 'secondary';
    }

    centerOnRoot() {
        if (!this.root) return;

        const centerX = this.config.width / 2;
        const centerY = 50;

        const transform = d3.zoomIdentity
            .translate(centerX, centerY)
            .scale(0.8);

        this.svg.transition()
            .duration(750)
            .call(this.zoom.transform, transform);
    }

    updateNode(nodeId, updates) {
        if (!this.root) return;

        // Find and update node
        const node = this.findNode(this.root, nodeId);
        if (node) {
            Object.assign(node.data, updates);
            this.render();
        }
    }

    findNode(root, nodeId) {
        if (root.data.id === nodeId) return root;

        if (root.children) {
            for (const child of root.children) {
                const found = this.findNode(child, nodeId);
                if (found) return found;
            }
        }

        return null;
    }

    connectWebSocket() {
        console.log('[FractalVisualizer] Connecting WebSocket:', this.wsUrl);

        this.ws = new WebSocket(this.wsUrl);

        this.ws.onopen = () => {
            console.log('[FractalVisualizer] WebSocket connected');
        };

        this.ws.onmessage = (event) => {
            try {
                const message = JSON.parse(event.data);
                this.handleWebSocketMessage(message);
            } catch (error) {
                console.error('[FractalVisualizer] WebSocket message error:', error);
            }
        };

        this.ws.onerror = (error) => {
            console.error('[FractalVisualizer] WebSocket error:', error);
        };

        this.ws.onclose = () => {
            console.log('[FractalVisualizer] WebSocket closed, reconnecting...');
            setTimeout(() => this.connectWebSocket(), 3000);
        };
    }

    handleWebSocketMessage(message) {
        console.log('[FractalVisualizer] WebSocket message:', message);

        switch (message.type) {
            case 'node_update':
                this.updateNode(message.node_id, message.updates);
                break;
            case 'tree_update':
                this.data = message.tree;
                this.render();
                break;
            default:
                console.warn('[FractalVisualizer] Unknown message type:', message.type);
        }
    }

    showError(message) {
        this.container.innerHTML = `
            <div class="alert alert-danger m-3">
                <i class="bi bi-exclamation-triangle"></i>
                <strong>Visualization Error:</strong> ${message}
            </div>
        `;
    }

    destroy() {
        if (this.ws) {
            this.ws.close();
        }

        if (this.svg) {
            this.svg.remove();
        }

        d3.select('.fractal-tooltip').remove();

        console.log('[FractalVisualizer] Destroyed');
    }

    resize(width, height) {
        this.config.width = width || this.container.clientWidth;
        this.config.height = height || this.container.clientHeight;

        this.svg
            .attr('width', this.config.width)
            .attr('height', this.config.height);

        this.centerOnRoot();
    }
}

// Export for global use
window.FractalVisualizer = FractalVisualizer;

console.log('[FractalVisualizer] Module loaded');
