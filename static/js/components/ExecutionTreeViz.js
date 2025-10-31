/**
 * ExecutionTreeViz.js
 * D3.js hierarchical tree visualization for 5-layer fractal execution
 * Supports zoom, pan, collapse, bottleneck detection, and export
 */

class ExecutionTreeViz {
  constructor(containerId, options = {}) {
    this.containerId = containerId;
    this.container = document.getElementById(containerId);

    if (!this.container) {
      console.error(`Container #${containerId} not found`);
      return;
    }

    // Configuration
    this.width = options.width || 800;
    this.height = options.height || 400;
    this.nodeRadius = 8;
    this.duration = 750; // Animation duration

    // Layer colors
    this.layerColors = {
      meta: '#9d4edd',
      exercise: '#0096ff',
      chain: '#00d9ff',
      tool: '#22d3ee',
      container: '#06b6d4'
    };

    // Status colors
    this.statusColors = {
      completed: '#198754',
      running: '#ffc107',
      failed: '#dc3545',
      pending: '#6c757d'
    };

    // Data tracking
    this.root = null;
    this.treeData = null;
    this.nodeId = 0;
    this.meanDuration = 0;
    this.stdDevDuration = 0;

    // Initialize visualization
    this.init();
  }

  init() {
    // Clear container
    this.container.innerHTML = '';

    // Create SVG with viewBox for responsiveness
    this.svg = d3.select(`#${this.containerId}`)
      .append('svg')
      .attr('width', '100%')
      .attr('height', '100%')
      .attr('viewBox', `0 0 ${this.width} ${this.height}`)
      .attr('preserveAspectRatio', 'xMidYMid meet');

    // Add zoom behavior
    this.zoom = d3.zoom()
      .scaleExtent([0.1, 3])
      .on('zoom', (event) => {
        this.g.attr('transform', event.transform);
      });

    this.svg.call(this.zoom);

    // Create main group for tree
    this.g = this.svg.append('g')
      .attr('transform', `translate(${this.width / 8}, ${this.height / 2})`);

    // Add defs for filters and patterns
    this.addDefs();

    // Create tree layout
    this.treemap = d3.tree()
      .size([this.height, this.width * 0.8])
      .nodeSize([30, 180]);

    // Create tooltip
    this.createTooltip();

    // Create controls
    this.createControls();

    // Create minimap
    this.createMinimap();
  }

  addDefs() {
    const defs = this.svg.append('defs');

    // Glow filter for bottlenecks
    const filter = defs.append('filter')
      .attr('id', 'glow')
      .attr('x', '-50%')
      .attr('y', '-50%')
      .attr('width', '200%')
      .attr('height', '200%');

    filter.append('feGaussianBlur')
      .attr('stdDeviation', '4')
      .attr('result', 'coloredBlur');

    const feMerge = filter.append('feMerge');
    feMerge.append('feMergeNode').attr('in', 'coloredBlur');
    feMerge.append('feMergeNode').attr('in', 'SourceGraphic');

    // Gradient for status indicators
    const gradient = defs.append('radialGradient')
      .attr('id', 'runningGradient');
    gradient.append('stop')
      .attr('offset', '0%')
      .attr('stop-color', '#ffc107')
      .attr('stop-opacity', 1);
    gradient.append('stop')
      .attr('offset', '100%')
      .attr('stop-color', '#ffc107')
      .attr('stop-opacity', 0.3);
  }

  createTooltip() {
    this.tooltip = d3.select('body')
      .append('div')
      .attr('class', 'execution-tree-tooltip')
      .style('position', 'absolute')
      .style('visibility', 'hidden')
      .style('background', 'rgba(0, 0, 0, 0.9)')
      .style('color', '#fff')
      .style('padding', '10px')
      .style('border-radius', '4px')
      .style('font-size', '12px')
      .style('pointer-events', 'none')
      .style('z-index', '1000')
      .style('max-width', '250px')
      .style('box-shadow', '0 4px 6px rgba(0, 0, 0, 0.3)');
  }

  createControls() {
    const controls = d3.select(`#${this.containerId}`)
      .append('div')
      .attr('class', 'tree-controls')
      .style('position', 'absolute')
      .style('top', '10px')
      .style('right', '10px')
      .style('display', 'flex')
      .style('gap', '8px')
      .style('z-index', '100');

    // Zoom in
    controls.append('button')
      .attr('class', 'tree-control-btn')
      .style('padding', '6px 12px')
      .style('background', '#1e293b')
      .style('border', '1px solid #334155')
      .style('color', '#a1a1aa')
      .style('border-radius', '4px')
      .style('cursor', 'pointer')
      .html('<i class="bi bi-zoom-in"></i>')
      .on('click', () => this.zoomIn());

    // Zoom out
    controls.append('button')
      .attr('class', 'tree-control-btn')
      .style('padding', '6px 12px')
      .style('background', '#1e293b')
      .style('border', '1px solid #334155')
      .style('color', '#a1a1aa')
      .style('border-radius', '4px')
      .style('cursor', 'pointer')
      .html('<i class="bi bi-zoom-out"></i>')
      .on('click', () => this.zoomOut());

    // Reset view
    controls.append('button')
      .attr('class', 'tree-control-btn')
      .style('padding', '6px 12px')
      .style('background', '#1e293b')
      .style('border', '1px solid #334155')
      .style('color', '#a1a1aa')
      .style('border-radius', '4px')
      .style('cursor', 'pointer')
      .html('<i class="bi bi-arrows-fullscreen"></i>')
      .on('click', () => this.resetView());

    // Expand all
    controls.append('button')
      .attr('class', 'tree-control-btn')
      .style('padding', '6px 12px')
      .style('background', '#1e293b')
      .style('border', '1px solid #334155')
      .style('color', '#a1a1aa')
      .style('border-radius', '4px')
      .style('cursor', 'pointer')
      .html('<i class="bi bi-arrows-expand"></i>')
      .on('click', () => this.expandAll());

    // Collapse all
    controls.append('button')
      .attr('class', 'tree-control-btn')
      .style('padding', '6px 12px')
      .style('background', '#1e293b')
      .style('border', '1px solid #334155')
      .style('color', '#a1a1aa')
      .style('border-radius', '4px')
      .style('cursor', 'pointer')
      .html('<i class="bi bi-arrows-collapse"></i>')
      .on('click', () => this.collapseAll());

    // Export PNG
    controls.append('button')
      .attr('class', 'tree-control-btn')
      .style('padding', '6px 12px')
      .style('background', '#1e293b')
      .style('border', '1px solid #334155')
      .style('color', '#a1a1aa')
      .style('border-radius', '4px')
      .style('cursor', 'pointer')
      .html('<i class="bi bi-download"></i> PNG')
      .on('click', () => this.exportPNG());

    // Export SVG
    controls.append('button')
      .attr('class', 'tree-control-btn')
      .style('padding', '6px 12px')
      .style('background', '#1e293b')
      .style('border', '1px solid #334155')
      .style('color', '#a1a1aa')
      .style('border-radius', '4px')
      .style('cursor', 'pointer')
      .html('<i class="bi bi-filetype-svg"></i>')
      .on('click', () => this.exportSVG());
  }

  createMinimap() {
    const minimapWidth = 150;
    const minimapHeight = 100;

    this.minimap = this.svg.append('g')
      .attr('class', 'minimap')
      .attr('transform', `translate(${this.width - minimapWidth - 10}, 10)`);

    this.minimap.append('rect')
      .attr('width', minimapWidth)
      .attr('height', minimapHeight)
      .attr('fill', 'rgba(0, 0, 0, 0.3)')
      .attr('stroke', '#334155')
      .attr('stroke-width', 1)
      .attr('rx', 4);

    this.minimapTree = this.minimap.append('g')
      .attr('transform', `translate(5, 5)`);

    this.minimapViewport = this.minimap.append('rect')
      .attr('class', 'minimap-viewport')
      .attr('fill', 'none')
      .attr('stroke', '#00d9ff')
      .attr('stroke-width', 2)
      .attr('rx', 2);
  }

  loadData(data) {
    if (!data) {
      console.warn('No data provided to ExecutionTreeViz');
      return;
    }

    this.treeData = data;

    // Calculate statistics for bottleneck detection
    this.calculateDurationStats(data);

    // Create hierarchy
    this.root = d3.hierarchy(data, d => d.children);
    this.root.x0 = this.height / 2;
    this.root.y0 = 0;

    // Collapse all children initially (except first level)
    if (this.root.children) {
      this.root.children.forEach(child => this.collapse(child));
    }

    // Render tree
    this.update(this.root);
    this.updateMinimap();
  }

  calculateDurationStats(node) {
    const durations = [];

    const collectDurations = (n) => {
      if (n.duration) durations.push(n.duration);
      if (n.children) {
        n.children.forEach(child => collectDurations(child));
      }
    };

    collectDurations(node);

    if (durations.length > 0) {
      this.meanDuration = d3.mean(durations);
      this.stdDevDuration = d3.deviation(durations);
    }
  }

  isBottleneck(duration) {
    if (!this.stdDevDuration || !this.meanDuration) return false;
    return duration > (this.meanDuration + 2 * this.stdDevDuration);
  }

  collapse(d) {
    if (d.children) {
      d._children = d.children;
      d._children.forEach(child => this.collapse(child));
      d.children = null;
    }
  }

  expand(d) {
    if (d._children) {
      d.children = d._children;
      d._children = null;
    }
  }

  expandAll() {
    const expandNode = (d) => {
      if (d._children) {
        d.children = d._children;
        d._children = null;
      }
      if (d.children) {
        d.children.forEach(expandNode);
      }
    };
    expandNode(this.root);
    this.update(this.root);
    this.updateMinimap();
  }

  collapseAll() {
    if (this.root.children) {
      this.root.children.forEach(child => {
        this.collapse(child);
      });
    }
    this.update(this.root);
    this.updateMinimap();
  }

  update(source) {
    // Compute new tree layout
    const treeData = this.treemap(this.root);
    const nodes = treeData.descendants();
    const links = treeData.descendants().slice(1);

    // Normalize for fixed-depth (horizontal layout)
    nodes.forEach(d => { d.y = d.depth * 180; });

    // Update nodes
    const node = this.g.selectAll('g.node')
      .data(nodes, d => d.id || (d.id = ++this.nodeId));

    // Enter new nodes
    const nodeEnter = node.enter().append('g')
      .attr('class', 'node')
      .attr('transform', d => `translate(${source.y0},${source.x0})`)
      .on('click', (event, d) => this.handleNodeClick(event, d))
      .on('mouseover', (event, d) => this.showTooltip(event, d))
      .on('mouseout', () => this.hideTooltip());

    // Add circles for nodes
    nodeEnter.append('circle')
      .attr('class', 'node-circle')
      .attr('r', 1e-6)
      .style('fill', d => d._children ? this.layerColors[d.data.layer] : '#fff')
      .style('stroke', d => this.layerColors[d.data.layer])
      .style('stroke-width', d => d.data.status === 'running' ? 3 : 2)
      .style('filter', d => this.isBottleneck(d.data.duration) ? 'url(#glow)' : 'none');

    // Add status indicator
    nodeEnter.append('circle')
      .attr('class', 'status-indicator')
      .attr('r', 4)
      .attr('cx', 8)
      .attr('cy', -8)
      .style('fill', d => this.statusColors[d.data.status])
      .style('opacity', 0);

    // Add labels
    nodeEnter.append('text')
      .attr('dy', '0.31em')
      .attr('x', d => d.children || d._children ? -13 : 13)
      .attr('text-anchor', d => d.children || d._children ? 'end' : 'start')
      .text(d => d.data.name)
      .style('fill', '#a1a1aa')
      .style('font-size', '11px')
      .style('opacity', 0);

    // Update existing nodes
    const nodeUpdate = nodeEnter.merge(node);

    nodeUpdate.transition()
      .duration(this.duration)
      .attr('transform', d => `translate(${d.y},${d.x})`);

    nodeUpdate.select('circle.node-circle')
      .transition()
      .duration(this.duration)
      .attr('r', d => this.getNodeRadius(d.data.duration))
      .style('fill', d => {
        if (d.data.status === 'running') return 'url(#runningGradient)';
        return d._children ? this.layerColors[d.data.layer] : '#fff';
      })
      .style('stroke', d => {
        if (this.isBottleneck(d.data.duration)) return '#dc3545';
        return this.layerColors[d.data.layer];
      })
      .style('stroke-width', d => {
        if (this.isBottleneck(d.data.duration)) return 4;
        if (d.data.status === 'running') return 3;
        return 2;
      })
      .style('filter', d => this.isBottleneck(d.data.duration) ? 'url(#glow)' : 'none');

    nodeUpdate.select('circle.status-indicator')
      .transition()
      .duration(this.duration)
      .style('fill', d => this.statusColors[d.data.status])
      .style('opacity', 1);

    nodeUpdate.select('text')
      .transition()
      .duration(this.duration)
      .attr('x', d => d.children || d._children ? -13 : 13)
      .attr('text-anchor', d => d.children || d._children ? 'end' : 'start')
      .style('opacity', 1);

    // Remove exiting nodes
    const nodeExit = node.exit().transition()
      .duration(this.duration)
      .attr('transform', d => `translate(${source.y},${source.x})`)
      .remove();

    nodeExit.select('circle.node-circle')
      .attr('r', 1e-6);

    nodeExit.select('text')
      .style('opacity', 0);

    // Update links
    const link = this.g.selectAll('path.link')
      .data(links, d => d.id);

    // Enter new links
    const linkEnter = link.enter().insert('path', 'g')
      .attr('class', 'link')
      .attr('d', d => {
        const o = { x: source.x0, y: source.y0 };
        return this.diagonal(o, o);
      })
      .style('fill', 'none')
      .style('stroke', '#334155')
      .style('stroke-width', 2);

    // Update existing links
    const linkUpdate = linkEnter.merge(link);

    linkUpdate.transition()
      .duration(this.duration)
      .attr('d', d => this.diagonal(d, d.parent))
      .style('stroke', d => {
        // Color link by child's layer
        return this.layerColors[d.data.layer] + '80'; // 50% opacity
      });

    // Remove exiting links
    link.exit().transition()
      .duration(this.duration)
      .attr('d', d => {
        const o = { x: source.x, y: source.y };
        return this.diagonal(o, o);
      })
      .remove();

    // Store old positions for transition
    nodes.forEach(d => {
      d.x0 = d.x;
      d.y0 = d.y;
    });
  }

  diagonal(s, d) {
    // Creates curved path from parent to child
    return `M ${s.y} ${s.x}
            C ${(s.y + d.y) / 2} ${s.x},
              ${(s.y + d.y) / 2} ${d.x},
              ${d.y} ${d.x}`;
  }

  getNodeRadius(duration) {
    if (!duration) return this.nodeRadius;
    // Scale radius based on duration (6-14px range)
    const scale = d3.scaleLinear()
      .domain([0, this.meanDuration * 2])
      .range([6, 14])
      .clamp(true);
    return scale(duration);
  }

  handleNodeClick(event, d) {
    if (d.children) {
      d._children = d.children;
      d.children = null;
    } else if (d._children) {
      d.children = d._children;
      d._children = null;
    }
    this.update(d);
    this.updateMinimap();
  }

  showTooltip(event, d) {
    const isBottleneck = this.isBottleneck(d.data.duration);

    let content = `
      <div style="font-weight: bold; margin-bottom: 5px; color: ${this.layerColors[d.data.layer]}">
        ${d.data.name}
      </div>
      <div style="margin: 3px 0;">
        <span style="color: #6c757d;">Layer:</span>
        <span style="text-transform: capitalize;">${d.data.layer}</span>
      </div>
      <div style="margin: 3px 0;">
        <span style="color: #6c757d;">Status:</span>
        <span style="color: ${this.statusColors[d.data.status]}">${d.data.status}</span>
      </div>
      <div style="margin: 3px 0;">
        <span style="color: #6c757d;">Duration:</span>
        <span>${d.data.duration ? d.data.duration.toFixed(2) + 's' : 'N/A'}</span>
      </div>
    `;

    if (isBottleneck) {
      content += `
        <div style="margin-top: 8px; padding: 4px; background: #dc3545; border-radius: 3px; font-weight: bold;">
          <i class="bi bi-exclamation-triangle"></i> Bottleneck Detected
        </div>
      `;
    }

    if (d.children || d._children) {
      const childCount = (d.children || d._children).length;
      content += `
        <div style="margin-top: 5px; color: #6c757d; font-size: 10px;">
          Click to ${d.children ? 'collapse' : 'expand'} (${childCount} children)
        </div>
      `;
    }

    this.tooltip
      .html(content)
      .style('visibility', 'visible')
      .style('top', (event.pageY - 10) + 'px')
      .style('left', (event.pageX + 10) + 'px');
  }

  hideTooltip() {
    this.tooltip.style('visibility', 'hidden');
  }

  updateMinimap() {
    if (!this.root) return;

    const minimapScale = 0.08;
    this.minimapTree.selectAll('*').remove();

    const treeData = this.treemap(this.root);
    const nodes = treeData.descendants();
    const links = treeData.descendants().slice(1);

    nodes.forEach(d => { d.y = d.depth * 180; });

    // Draw links
    this.minimapTree.selectAll('path.minimap-link')
      .data(links)
      .enter()
      .append('path')
      .attr('class', 'minimap-link')
      .attr('d', d => {
        const sx = d.parent.y * minimapScale;
        const sy = d.parent.x * minimapScale;
        const dx = d.y * minimapScale;
        const dy = d.x * minimapScale;
        return `M ${sx} ${sy} L ${dx} ${dy}`;
      })
      .style('fill', 'none')
      .style('stroke', '#334155')
      .style('stroke-width', 1);

    // Draw nodes
    this.minimapTree.selectAll('circle.minimap-node')
      .data(nodes)
      .enter()
      .append('circle')
      .attr('class', 'minimap-node')
      .attr('cx', d => d.y * minimapScale)
      .attr('cy', d => d.x * minimapScale)
      .attr('r', 2)
      .style('fill', d => this.layerColors[d.data.layer]);
  }

  zoomIn() {
    this.svg.transition().call(this.zoom.scaleBy, 1.3);
  }

  zoomOut() {
    this.svg.transition().call(this.zoom.scaleBy, 0.7);
  }

  resetView() {
    this.svg.transition().call(
      this.zoom.transform,
      d3.zoomIdentity.translate(this.width / 8, this.height / 2)
    );
  }

  exportPNG() {
    const svgElement = this.svg.node();
    const svgString = new XMLSerializer().serializeToString(svgElement);

    const canvas = document.createElement('canvas');
    canvas.width = this.width * 2;
    canvas.height = this.height * 2;
    const ctx = canvas.getContext('2d');

    const img = new Image();
    const blob = new Blob([svgString], { type: 'image/svg+xml;charset=utf-8' });
    const url = URL.createObjectURL(blob);

    img.onload = () => {
      ctx.fillStyle = '#0a0f1e';
      ctx.fillRect(0, 0, canvas.width, canvas.height);
      ctx.drawImage(img, 0, 0, canvas.width, canvas.height);

      canvas.toBlob((blob) => {
        const link = document.createElement('a');
        link.download = `execution-tree-${Date.now()}.png`;
        link.href = URL.createObjectURL(blob);
        link.click();
        URL.revokeObjectURL(url);
      });
    };

    img.src = url;
  }

  exportSVG() {
    const svgElement = this.svg.node();
    const svgString = new XMLSerializer().serializeToString(svgElement);
    const blob = new Blob([svgString], { type: 'image/svg+xml;charset=utf-8' });
    const url = URL.createObjectURL(blob);

    const link = document.createElement('a');
    link.download = `execution-tree-${Date.now()}.svg`;
    link.href = url;
    link.click();

    URL.revokeObjectURL(url);
  }
}

// Export to window for global access
window.ExecutionTreeViz = ExecutionTreeViz;
