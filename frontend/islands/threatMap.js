/**
 * Threat Map Island - Network Topology Visualization
 */

import { h, Component } from 'preact';
import * as d3 from 'd3';

export default class ThreatMapIsland extends Component {
  constructor(props) {
    super(props);
    this.state = {
      nodes: [],
      links: [],
      selectedNode: null
    };
    this.svgRef = null;
    this.simulation = null;
  }

  componentDidMount() {
    this.fetchTopology();
  }

  async fetchTopology() {
    try {
      const response = await fetch('/api/topology');
      const data = await response.json();

      this.setState({
        nodes: data.nodes || [],
        links: data.links || []
      });

      this.initVisualization();
    } catch (error) {
      console.error('Failed to fetch topology:', error);
      // Demo data
      this.setState({
        nodes: [
          { id: 'attacker', type: 'attacker', label: 'Red Team C2' },
          { id: 'target1', type: 'target', label: 'Web Server', ip: '192.168.1.10', status: 'compromised' },
          { id: 'target2', type: 'target', label: 'Database', ip: '192.168.1.20', status: 'scanning' },
          { id: 'target3', type: 'target', label: 'File Server', ip: '192.168.1.30', status: 'unknown' }
        ],
        links: [
          { source: 'attacker', target: 'target1', type: 'exploit' },
          { source: 'attacker', target: 'target2', type: 'scan' },
          { source: 'target1', target: 'target2', type: 'connection' }
        ]
      });
      this.initVisualization();
    }
  }

  initVisualization() {
    if (!this.svgRef) return;

    const width = this.svgRef.clientWidth;
    const height = this.svgRef.clientHeight;

    // Clear existing
    d3.select(this.svgRef).selectAll('*').remove();

    const svg = d3.select(this.svgRef)
      .append('svg')
      .attr('width', width)
      .attr('height', height);

    // Create force simulation
    this.simulation = d3.forceSimulation(this.state.nodes)
      .force('link', d3.forceLink(this.state.links).id(d => d.id).distance(150))
      .force('charge', d3.forceManyBody().strength(-300))
      .force('center', d3.forceCenter(width / 2, height / 2))
      .force('collision', d3.forceCollide().radius(50));

    // Draw links
    const link = svg.append('g')
      .selectAll('line')
      .data(this.state.links)
      .enter().append('line')
      .attr('stroke', d => {
        if (d.type === 'exploit') return '#f44336';
        if (d.type === 'scan') return '#ffc107';
        return '#2a3f5f';
      })
      .attr('stroke-width', 2)
      .attr('stroke-dasharray', d => d.type === 'scan' ? '5,5' : null);

    // Draw nodes
    const node = svg.append('g')
      .selectAll('g')
      .data(this.state.nodes)
      .enter().append('g')
      .call(d3.drag()
        .on('start', (event, d) => this.dragStarted(event, d))
        .on('drag', (event, d) => this.dragged(event, d))
        .on('end', (event, d) => this.dragEnded(event, d))
      )
      .on('click', (event, d) => this.selectNode(d));

    // Node circles
    node.append('circle')
      .attr('r', d => d.type === 'attacker' ? 25 : 20)
      .attr('fill', d => {
        if (d.type === 'attacker') return '#4caf50';
        if (d.status === 'compromised') return '#f44336';
        if (d.status === 'scanning') return '#ffc107';
        return '#2196f3';
      })
      .attr('stroke', '#0a0f14')
      .attr('stroke-width', 3);

    // Node icons
    node.append('text')
      .attr('text-anchor', 'middle')
      .attr('dy', 5)
      .attr('font-size', 16)
      .attr('fill', '#0a0f14')
      .text(d => d.type === 'attacker' ? '⚔' : '🖥');

    // Node labels
    node.append('text')
      .attr('text-anchor', 'middle')
      .attr('dy', 35)
      .attr('font-size', 12)
      .attr('fill', '#c9d1d9')
      .text(d => d.label);

    // Update positions on tick
    this.simulation.on('tick', () => {
      link
        .attr('x1', d => d.source.x)
        .attr('y1', d => d.source.y)
        .attr('x2', d => d.target.x)
        .attr('y2', d => d.target.y);

      node.attr('transform', d => `translate(${d.x},${d.y})`);
    });
  }

  dragStarted(event, d) {
    if (!event.active) this.simulation.alphaTarget(0.3).restart();
    d.fx = d.x;
    d.fy = d.y;
  }

  dragged(event, d) {
    d.fx = event.x;
    d.fy = event.y;
  }

  dragEnded(event, d) {
    if (!event.active) this.simulation.alphaTarget(0);
    d.fx = null;
    d.fy = null;
  }

  selectNode(node) {
    this.setState({ selectedNode: node });
  }

  render() {
    const { selectedNode } = this.state;

    return h('div', { class: 'threat-map-island flex flex-col h-full' },
      // Header
      h('div', { class: 'p-4 bg-tactical-card border-b border-tactical-border' },
        h('h3', { class: 'text-tactical-text font-display text-lg' }, 'Network Topology Map'),
        h('p', { class: 'text-tactical-muted text-sm mt-1' }, 'Interactive network visualization and attack paths')
      ),

      // Map and Details
      h('div', { class: 'flex-1 grid grid-cols-1 lg:grid-cols-3 gap-4 p-4' },
        // Map
        h('div', { class: 'lg:col-span-2 bg-tactical-bg rounded-lg border border-tactical-border relative' },
          h('div', {
            ref: ref => this.svgRef = ref,
            class: 'w-full h-96'
          }),

          // Legend
          h('div', { class: 'absolute bottom-4 left-4 bg-tactical-card border border-tactical-border rounded p-3' },
            h('div', { class: 'text-xs space-y-1' },
              h('div', { class: 'flex items-center gap-2' },
                h('div', { class: 'w-3 h-3 rounded-full bg-military-green' }),
                h('span', { class: 'text-tactical-text' }, 'Attacker')
              ),
              h('div', { class: 'flex items-center gap-2' },
                h('div', { class: 'w-3 h-3 rounded-full bg-military-red' }),
                h('span', { class: 'text-tactical-text' }, 'Compromised')
              ),
              h('div', { class: 'flex items-center gap-2' },
                h('div', { class: 'w-3 h-3 rounded-full bg-military-amber' }),
                h('span', { class: 'text-tactical-text' }, 'Scanning')
              ),
              h('div', { class: 'flex items-center gap-2' },
                h('div', { class: 'w-3 h-3 rounded-full bg-blue-500' }),
                h('span', { class: 'text-tactical-text' }, 'Unknown')
              )
            )
          )
        ),

        // Node Details
        h('div', { class: 'bg-tactical-card rounded-lg border border-tactical-border p-4' },
          selectedNode
            ? h('div', { class: 'space-y-4' },
                h('h4', { class: 'text-military-green font-semibold text-lg' }, selectedNode.label),
                h('div', { class: 'space-y-2' },
                  h('div', null,
                    h('span', { class: 'text-tactical-muted text-sm' }, 'Type'),
                    h('p', { class: 'text-tactical-text' }, selectedNode.type)
                  ),
                  selectedNode.ip && h('div', null,
                    h('span', { class: 'text-tactical-muted text-sm' }, 'IP Address'),
                    h('p', { class: 'text-tactical-text font-mono' }, selectedNode.ip)
                  ),
                  selectedNode.status && h('div', null,
                    h('span', { class: 'text-tactical-muted text-sm' }, 'Status'),
                    h('p', { class: 'text-tactical-text capitalize' }, selectedNode.status)
                  )
                ),
                h('button', {
                  class: 'w-full px-4 py-2 bg-military-green hover:bg-military-green-dark text-tactical-bg rounded font-semibold transition-colors',
                  onClick: () => alert(`Targeting ${selectedNode.label}`)
                }, 'Launch Attack')
              )
            : h('div', { class: 'flex items-center justify-center h-full text-tactical-muted' },
                'Click a node to view details'
              )
        )
      )
    );
  }
}
