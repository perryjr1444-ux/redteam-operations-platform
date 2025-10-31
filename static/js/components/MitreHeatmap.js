/**
 * MITRE ATT&CK Heatmap Component
 * D3.js-based visualization for MITRE ATT&CK matrix with execution counts
 */

class MitreHeatmap {
    constructor(containerId, options = {}) {
        this.containerId = containerId;
        this.container = d3.select(`#${containerId}`);

        // Configuration
        this.options = {
            width: options.width || 1400,
            height: options.height || 800,
            margin: { top: 80, right: 20, bottom: 60, left: 120 },
            cellPadding: 2,
            ...options
        };

        // Color scales
        this.colorScaleReal = d3.scaleLinear()
            .domain([0, 10])  // Will be updated based on data
            .range(['#1a1a2e', '#ff0055'])
            .interpolate(d3.interpolateRgb);

        this.placeholderColor = 'rgba(255, 255, 255, 0.05)';

        // Data storage
        this.data = null;
        this.svg = null;
        this.tooltip = null;

        // Initialize container
        this.init();
    }

    /**
     * Initialize the SVG container and tooltip
     */
    init() {
        // Clear existing content
        this.container.selectAll('*').remove();

        // Create tooltip
        this.tooltip = d3.select('body')
            .append('div')
            .attr('class', 'mitre-tooltip')
            .style('position', 'absolute')
            .style('visibility', 'hidden')
            .style('background-color', 'rgba(0, 0, 0, 0.9)')
            .style('color', '#00ff9f')
            .style('padding', '12px')
            .style('border-radius', '4px')
            .style('border', '1px solid #00ff9f')
            .style('font-family', 'monospace')
            .style('font-size', '12px')
            .style('pointer-events', 'none')
            .style('z-index', '1000')
            .style('box-shadow', '0 0 10px rgba(0, 255, 159, 0.3)');

        // Create SVG
        this.svg = this.container
            .append('svg')
            .attr('width', this.options.width)
            .attr('height', this.options.height)
            .style('background-color', 'transparent');

        // Create main group
        this.mainGroup = this.svg.append('g')
            .attr('transform', `translate(${this.options.margin.left}, ${this.options.margin.top})`);
    }

    /**
     * Calculate dimensions based on data
     */
    calculateDimensions(data) {
        const numTactics = data.tactics.length;
        const maxTechniquesPerTactic = Math.max(...data.tactics.map(tactic => {
            return Object.values(data.techniques).filter(t => t.tactic === tactic).length;
        }));

        const availableWidth = this.options.width - this.options.margin.left - this.options.margin.right;
        const availableHeight = this.options.height - this.options.margin.top - this.options.margin.bottom;

        const cellWidth = (availableWidth / numTactics) - this.options.cellPadding;
        const cellHeight = Math.min(
            (availableHeight / maxTechniquesPerTactic) - this.options.cellPadding,
            30
        );

        return { cellWidth, cellHeight, maxTechniquesPerTactic };
    }

    /**
     * Render the heatmap with given data
     */
    render(data) {
        this.data = data;

        // Validate data
        if (!data || !data.tactics || !data.techniques) {
            console.error('Invalid data format');
            return;
        }

        // Update color scale domain based on actual data
        const maxCount = Math.max(...Object.values(data.techniques)
            .filter(t => t.real)
            .map(t => t.count), 1);
        this.colorScaleReal.domain([0, maxCount]);

        // Calculate dimensions
        const dims = this.calculateDimensions(data);

        // Clear previous render
        this.mainGroup.selectAll('*').remove();

        // Render tactics (columns)
        this.renderTactics(data.tactics, dims);

        // Render technique cells
        this.renderTechniques(data, dims);

        // Render legend
        this.renderLegend(dims, maxCount);

        // Render title
        this.renderTitle();
    }

    /**
     * Render tactic headers
     */
    renderTactics(tactics, dims) {
        const tacticGroup = this.mainGroup.append('g')
            .attr('class', 'tactics-group');

        tactics.forEach((tactic, i) => {
            const x = i * (dims.cellWidth + this.options.cellPadding);

            // Tactic background
            tacticGroup.append('rect')
                .attr('x', x)
                .attr('y', -60)
                .attr('width', dims.cellWidth)
                .attr('height', 50)
                .attr('fill', 'rgba(0, 255, 159, 0.1)')
                .attr('stroke', '#00ff9f')
                .attr('stroke-width', 1)
                .attr('rx', 4);

            // Tactic text
            tacticGroup.append('text')
                .attr('x', x + dims.cellWidth / 2)
                .attr('y', -30)
                .attr('text-anchor', 'middle')
                .attr('dominant-baseline', 'middle')
                .attr('fill', '#00ff9f')
                .attr('font-family', 'monospace')
                .attr('font-size', '11px')
                .attr('font-weight', 'bold')
                .text(tactic)
                .call(this.wrapText, dims.cellWidth - 10);
        });
    }

    /**
     * Render technique cells
     */
    renderTechniques(data, dims) {
        const techniqueGroup = this.mainGroup.append('g')
            .attr('class', 'techniques-group');

        // Group techniques by tactic
        const techniquesByTactic = {};
        data.tactics.forEach(tactic => {
            techniquesByTactic[tactic] = Object.entries(data.techniques)
                .filter(([_, tech]) => tech.tactic === tactic)
                .map(([id, tech]) => ({ id, ...tech }));
        });

        // Render cells
        data.tactics.forEach((tactic, tacticIndex) => {
            const techniques = techniquesByTactic[tactic] || [];
            const x = tacticIndex * (dims.cellWidth + this.options.cellPadding);

            techniques.forEach((technique, techIndex) => {
                const y = techIndex * (dims.cellHeight + this.options.cellPadding);

                // Determine cell color
                const cellColor = technique.real
                    ? this.colorScaleReal(technique.count)
                    : this.placeholderColor;

                // Create cell
                const cell = techniqueGroup.append('g')
                    .attr('class', 'technique-cell')
                    .attr('transform', `translate(${x}, ${y})`);

                // Cell rectangle
                const rect = cell.append('rect')
                    .attr('width', dims.cellWidth)
                    .attr('height', dims.cellHeight)
                    .attr('fill', cellColor)
                    .attr('stroke', technique.real ? '#ff0055' : '#333')
                    .attr('stroke-width', 0.5)
                    .attr('rx', 2)
                    .style('cursor', 'pointer')
                    .style('transition', 'all 0.2s');

                // Cell label (technique ID)
                cell.append('text')
                    .attr('x', dims.cellWidth / 2)
                    .attr('y', dims.cellHeight / 2)
                    .attr('text-anchor', 'middle')
                    .attr('dominant-baseline', 'middle')
                    .attr('fill', technique.real && technique.count > 5 ? '#fff' : '#888')
                    .attr('font-family', 'monospace')
                    .attr('font-size', '9px')
                    .attr('font-weight', technique.real ? 'bold' : 'normal')
                    .text(technique.id)
                    .style('pointer-events', 'none');

                // Hover effects
                cell.on('mouseover', (event) => {
                    // Highlight cell
                    rect.attr('stroke-width', 2)
                        .attr('stroke', '#00ff9f')
                        .attr('filter', 'brightness(1.3)');

                    // Show tooltip
                    this.showTooltip(event, technique);
                })
                .on('mousemove', (event) => {
                    this.tooltip
                        .style('top', (event.pageY - 10) + 'px')
                        .style('left', (event.pageX + 10) + 'px');
                })
                .on('mouseout', () => {
                    // Reset cell
                    rect.attr('stroke-width', 0.5)
                        .attr('stroke', technique.real ? '#ff0055' : '#333')
                        .attr('filter', 'none');

                    // Hide tooltip
                    this.tooltip.style('visibility', 'hidden');
                });
            });
        });
    }

    /**
     * Show tooltip with technique information
     */
    showTooltip(event, technique) {
        const tooltipContent = `
            <div style="line-height: 1.6;">
                <div style="color: #ff0055; font-weight: bold; margin-bottom: 8px;">
                    ${technique.id}: ${technique.name}
                </div>
                <div style="color: #00ff9f;">
                    Tactic: ${technique.tactic}
                </div>
                <div style="color: ${technique.real ? '#00ff9f' : '#888'};">
                    Executions: ${technique.count}
                </div>
                <div style="color: ${technique.real ? '#00ff9f' : '#ff0055'}; margin-top: 4px;">
                    ${technique.real ? '✓ Real Data' : '○ Placeholder'}
                </div>
            </div>
        `;

        this.tooltip
            .html(tooltipContent)
            .style('visibility', 'visible')
            .style('top', (event.pageY - 10) + 'px')
            .style('left', (event.pageX + 10) + 'px');
    }

    /**
     * Render legend
     */
    renderLegend(dims, maxCount) {
        const legendGroup = this.mainGroup.append('g')
            .attr('class', 'legend-group')
            .attr('transform', `translate(0, ${dims.maxTechniquesPerTactic * (dims.cellHeight + this.options.cellPadding) + 20})`);

        // Gradient legend for real data
        const gradientWidth = 200;
        const gradientHeight = 20;

        // Create gradient definition
        const defs = this.svg.append('defs');
        const gradient = defs.append('linearGradient')
            .attr('id', 'heatmap-gradient')
            .attr('x1', '0%')
            .attr('x2', '100%')
            .attr('y1', '0%')
            .attr('y2', '0%');

        gradient.append('stop')
            .attr('offset', '0%')
            .attr('stop-color', '#1a1a2e');

        gradient.append('stop')
            .attr('offset', '100%')
            .attr('stop-color', '#ff0055');

        // Gradient rectangle
        legendGroup.append('rect')
            .attr('x', 0)
            .attr('y', 0)
            .attr('width', gradientWidth)
            .attr('height', gradientHeight)
            .attr('fill', 'url(#heatmap-gradient)')
            .attr('stroke', '#00ff9f')
            .attr('stroke-width', 1);

        // Gradient labels
        legendGroup.append('text')
            .attr('x', 0)
            .attr('y', gradientHeight + 15)
            .attr('fill', '#00ff9f')
            .attr('font-family', 'monospace')
            .attr('font-size', '10px')
            .text('0');

        legendGroup.append('text')
            .attr('x', gradientWidth)
            .attr('y', gradientHeight + 15)
            .attr('text-anchor', 'end')
            .attr('fill', '#00ff9f')
            .attr('font-family', 'monospace')
            .attr('font-size', '10px')
            .text(maxCount);

        legendGroup.append('text')
            .attr('x', gradientWidth / 2)
            .attr('y', -5)
            .attr('text-anchor', 'middle')
            .attr('fill', '#00ff9f')
            .attr('font-family', 'monospace')
            .attr('font-size', '11px')
            .attr('font-weight', 'bold')
            .text('Execution Count');

        // Placeholder indicator
        const placeholderX = gradientWidth + 40;

        legendGroup.append('rect')
            .attr('x', placeholderX)
            .attr('y', 0)
            .attr('width', gradientHeight)
            .attr('height', gradientHeight)
            .attr('fill', this.placeholderColor)
            .attr('stroke', '#333')
            .attr('stroke-width', 1);

        legendGroup.append('text')
            .attr('x', placeholderX + gradientHeight + 10)
            .attr('y', gradientHeight / 2)
            .attr('dominant-baseline', 'middle')
            .attr('fill', '#888')
            .attr('font-family', 'monospace')
            .attr('font-size', '10px')
            .text('Placeholder (No Data)');
    }

    /**
     * Render title
     */
    renderTitle() {
        this.svg.append('text')
            .attr('x', this.options.width / 2)
            .attr('y', 30)
            .attr('text-anchor', 'middle')
            .attr('fill', '#00ff9f')
            .attr('font-family', 'monospace')
            .attr('font-size', '18px')
            .attr('font-weight', 'bold')
            .text('MITRE ATT&CK Execution Heatmap');

        this.svg.append('text')
            .attr('x', this.options.width / 2)
            .attr('y', 50)
            .attr('text-anchor', 'middle')
            .attr('fill', '#888')
            .attr('font-family', 'monospace')
            .attr('font-size', '11px')
            .text('Technique Execution Frequency by Tactic');
    }

    /**
     * Wrap text to fit within a given width
     */
    wrapText(text, width) {
        text.each(function() {
            const text = d3.select(this);
            const words = text.text().split(/\s+/).reverse();
            let word;
            let line = [];
            let lineNumber = 0;
            const lineHeight = 1.1;
            const y = text.attr('y');
            const dy = parseFloat(text.attr('dy') || 0);
            let tspan = text.text(null).append('tspan')
                .attr('x', text.attr('x'))
                .attr('y', y)
                .attr('dy', dy + 'em');

            while (word = words.pop()) {
                line.push(word);
                tspan.text(line.join(' '));
                if (tspan.node().getComputedTextLength() > width) {
                    line.pop();
                    tspan.text(line.join(' '));
                    line = [word];
                    tspan = text.append('tspan')
                        .attr('x', text.attr('x'))
                        .attr('y', y)
                        .attr('dy', ++lineNumber * lineHeight + dy + 'em')
                        .text(word);
                }
            }
        });
    }

    /**
     * Export the heatmap as SVG
     */
    exportSVG() {
        const svgNode = this.svg.node();
        const serializer = new XMLSerializer();
        const svgString = serializer.serializeToString(svgNode);

        // Create blob and download
        const blob = new Blob([svgString], { type: 'image/svg+xml;charset=utf-8' });
        const url = URL.createObjectURL(blob);

        const link = document.createElement('a');
        link.href = url;
        link.download = `mitre_heatmap_${new Date().getTime()}.svg`;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);

        URL.revokeObjectURL(url);
    }

    /**
     * Resize the heatmap
     */
    resize(width, height) {
        this.options.width = width;
        this.options.height = height;

        this.svg
            .attr('width', width)
            .attr('height', height);

        // Re-render if data exists
        if (this.data) {
            this.render(this.data);
        }
    }

    /**
     * Update data and re-render
     */
    update(data) {
        this.render(data);
    }

    /**
     * Destroy the component and clean up
     */
    destroy() {
        if (this.tooltip) {
            this.tooltip.remove();
        }
        if (this.container) {
            this.container.selectAll('*').remove();
        }
    }
}

// Export to global scope
window.MitreHeatmap = MitreHeatmap;
