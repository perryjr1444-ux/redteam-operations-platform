/**
 * Attack Chain Builder
 * Visual graph editor for creating complex attack chains
 *
 * Features:
 * - Alpine.js state management
 * - D3.js visual graph rendering
 * - Drag-and-drop step creation
 * - Dependency management
 * - Circular dependency validation
 * - Real-time API integration
 */

// ============================================================================
// Alpine.js Component - State Management
// ============================================================================

document.addEventListener('alpine:init', () => {
    Alpine.data('chainBuilder', () => ({
        // State
        currentChain: {
            id: null,
            name: '',
            description: '',
            category: '',
            risk_level: 'medium',
            steps: [],
            metadata: {},
            created_at: null
        },
        chains: [],
        availableTools: [],
        toolCategories: [],
        toolSearch: '',
        selectedStep: null,
        selectedStepIndex: -1,
        rightPanelTab: 'tools',
        validationErrors: [],
        isLoading: false,
        isSaving: false,
        showLibrary: true,
        zoom: 1,

        // D3 graph instance
        graph: null,

        // Initialize component
        async init() {
            console.log('Chain Builder initialized');
            await this.loadTools();
            await this.loadChains();
            this.$nextTick(() => {
                this.initializeGraph();
            });
        },

        // Load available tools from API
        async loadTools() {
            this.isLoading = true;
            try {
                const response = await fetch('/api/tools');
                const data = await response.json();
                this.availableTools = data.tools || [];
                console.log(`Loaded ${this.availableTools.length} tools`);

                // Organize tools into categories
                this.organizeToolsIntoCategories();
            } catch (error) {
                console.error('Error loading tools:', error);
                this.showNotification('Failed to load tools', 'error');
            } finally {
                this.isLoading = false;
            }
        },

        // Organize tools into categories for UI display
        organizeToolsIntoCategories() {
            const categories = {
                'recon': [],
                'scan': [],
                'exploit': [],
                'post-exploit': []
            };

            this.availableTools.forEach(tool => {
                const type = tool.type || tool.category || 'scan';
                if (categories[type]) {
                    categories[type].push(tool);
                } else {
                    categories['scan'].push(tool);
                }
            });

            this.toolCategories = Object.keys(categories).map(key => ({
                name: key.charAt(0).toUpperCase() + key.slice(1),
                tools: categories[key]
            })).filter(cat => cat.tools.length > 0);
        },

        // Filter tools by search query
        filterTools(tools) {
            if (!this.toolSearch) return tools;
            const query = this.toolSearch.toLowerCase();
            return tools.filter(tool =>
                tool.name.toLowerCase().includes(query) ||
                (tool.description && tool.description.toLowerCase().includes(query))
            );
        },

        // Load saved chains from API
        async loadChains() {
            try {
                const response = await fetch('/api/chains');
                if (!response.ok) throw new Error('Failed to load chains');
                const data = await response.json();
                this.chains = data.chains || [];
                console.log(`Loaded ${this.chains.length} chains`);
            } catch (error) {
                console.error('Error loading chains:', error);
                // Don't show error notification, just log it
            }
        },

        // Initialize D3 graph
        initializeGraph() {
            const container = document.getElementById('chain-canvas');
            if (!container) return;

            this.graph = new ChainGraph('chain-canvas', {
                onStepClick: (stepId) => this.selectStep(stepId),
                onStepDrop: (position) => this.handleCanvasDrop(position),
                onLinkCreate: (sourceId, targetId) => this.createDependency(sourceId, targetId),
                onLinkDelete: (sourceId, targetId) => this.removeDependency(sourceId, targetId)
            });

            this.updateGraph();
        },

        // Add step from tool (called by template)
        addStepFromTool(tool) {
            this.addStep(tool);
            this.rightPanelTab = 'config';
        },

        // Add step to chain
        addStep(tool) {
            const newStep = {
                id: this.generateStepId(),
                tool: tool.name,
                target: '',
                type: tool.type || tool.category || 'scan',
                parameters: {},
                parametersJson: '{}',
                timeout: 300,
                continue_on_error: false,
                description: tool.description || '',
                // Visual properties
                x: Math.random() * 600 + 100,
                y: Math.random() * 400 + 100
            };

            this.currentChain.steps.push(newStep);
            this.updateGraph();
            this.selectStep(newStep.id);
            this.showNotification(`Added ${tool.name}`, 'success');
        },

        // Delete step (called by template buttons)
        deleteStep(index) {
            const step = this.currentChain.steps[index];
            if (!step) return;
            this.removeStep(step.id);
        },

        // Remove step from chain
        removeStep(stepId) {
            const index = this.currentChain.steps.findIndex(s => s.id === stepId);
            if (index === -1) return;

            // Remove dependencies that reference this step
            this.currentChain.steps.forEach(step => {
                step.depends_on = step.depends_on || [];
                step.depends_on = step.depends_on.filter(id => id !== stepId);
            });

            this.currentChain.steps.splice(index, 1);

            if (this.selectedStepIndex === index) {
                this.selectedStep = null;
                this.selectedStepIndex = -1;
            }

            this.updateGraph();
            this.validate();
        },

        // Move step up in order
        moveStepUp(index) {
            if (index === 0) return;
            const steps = this.currentChain.steps;
            [steps[index - 1], steps[index]] = [steps[index], steps[index - 1]];
            this.updateGraph();
        },

        // Move step down in order
        moveStepDown(index) {
            if (index === this.currentChain.steps.length - 1) return;
            const steps = this.currentChain.steps;
            [steps[index], steps[index + 1]] = [steps[index + 1], steps[index]];
            this.updateGraph();
        },

        // Update step parameters from JSON input
        updateStepParameters(index) {
            const step = this.currentChain.steps[index];
            if (!step) return;

            try {
                step.parameters = JSON.parse(step.parametersJson || '{}');
            } catch (error) {
                console.error('Invalid JSON:', error);
                // Keep the existing parameters
            }
        },

        // Select step for editing
        selectStep(index) {
            if (typeof index === 'string') {
                // If passed a step ID, find the index
                index = this.currentChain.steps.findIndex(s => s.id === index);
            }
            if (index === -1 || index >= this.currentChain.steps.length) return;

            this.selectedStepIndex = index;
            this.selectedStep = this.currentChain.steps[index];
            this.rightPanelTab = 'config';

            // Ensure parametersJson is set
            if (!this.selectedStep.parametersJson) {
                this.selectedStep.parametersJson = JSON.stringify(this.selectedStep.parameters || {}, null, 2);
            }

            this.graph?.highlightNode(this.selectedStep.id);
        },

        // Update selected step
        updateSelectedStep() {
            if (this.selectedStepIndex >= 0) {
                this.currentChain.steps[this.selectedStepIndex] = {...this.selectedStep};
                this.updateGraph();
                this.validate();
            }
        },

        // Create dependency between steps
        createDependency(sourceId, targetId) {
            const targetStep = this.currentChain.steps.find(s => s.id === targetId);
            if (!targetStep) return;

            targetStep.depends_on = targetStep.depends_on || [];
            if (!targetStep.depends_on.includes(sourceId)) {
                targetStep.depends_on.push(sourceId);
                this.updateGraph();
                this.validate();
            }
        },

        // Remove dependency
        removeDependency(sourceId, targetId) {
            const targetStep = this.currentChain.steps.find(s => s.id === targetId);
            if (!targetStep) return;

            targetStep.depends_on = targetStep.depends_on || [];
            targetStep.depends_on = targetStep.depends_on.filter(id => id !== sourceId);
            this.updateGraph();
            this.validate();
        },

        // Validate chain
        validate() {
            this.validationErrors = [];

            // Check for empty chain
            if (this.currentChain.steps.length === 0) {
                this.validationErrors.push('Chain must have at least one step');
                return false;
            }

            // Check for circular dependencies
            const circular = this.detectCircularDependencies();
            if (circular.length > 0) {
                this.validationErrors.push(`Circular dependencies detected: ${circular.join(', ')}`);
            }

            // Check for invalid dependencies
            this.currentChain.steps.forEach(step => {
                const deps = step.depends_on || [];
                deps.forEach(depId => {
                    if (!this.currentChain.steps.find(s => s.id === depId)) {
                        this.validationErrors.push(`Step ${step.id} has invalid dependency: ${depId}`);
                    }
                });
            });

            // Update graph with errors
            if (this.graph && circular.length > 0) {
                this.graph.highlightErrors(circular);
            }

            return this.validationErrors.length === 0;
        },

        // Detect circular dependencies using DFS
        detectCircularDependencies() {
            const visited = new Set();
            const recStack = new Set();
            const circular = [];

            const dfs = (stepId, path = []) => {
                if (recStack.has(stepId)) {
                    circular.push([...path, stepId].join(' → '));
                    return true;
                }

                if (visited.has(stepId)) return false;

                visited.add(stepId);
                recStack.add(stepId);

                const step = this.currentChain.steps.find(s => s.id === stepId);
                if (step) {
                    const deps = step.depends_on || [];
                    for (const depId of deps) {
                        if (dfs(depId, [...path, stepId])) {
                            // Continue checking other dependencies
                        }
                    }
                }

                recStack.delete(stepId);
                return false;
            };

            this.currentChain.steps.forEach(step => {
                if (!visited.has(step.id)) {
                    dfs(step.id);
                }
            });

            return circular;
        },

        // Create new chain
        newChain() {
            if (this.currentChain.steps.length > 0) {
                if (!confirm('Create a new chain? Unsaved changes will be lost.')) {
                    return;
                }
            }

            this.currentChain = {
                id: null,
                name: '',
                description: '',
                category: '',
                risk_level: 'medium',
                steps: [],
                metadata: {},
                created_at: null
            };
            this.selectedStep = null;
            this.selectedStepIndex = -1;
            this.validationErrors = [];
            this.updateGraph();
        },

        // Execute chain
        async executeChain() {
            if (!this.validate()) {
                this.showNotification('Please fix validation errors before executing', 'error');
                return;
            }

            if (!this.currentChain.id) {
                this.showNotification('Please save the chain before executing', 'error');
                return;
            }

            try {
                const response = await fetch(`/api/chains/${this.currentChain.id}/execute`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    }
                });

                if (!response.ok) {
                    throw new Error('Failed to execute chain');
                }

                const result = await response.json();
                this.showNotification(`Chain execution started: ${result.execution_id}`, 'success');
            } catch (error) {
                console.error('Error executing chain:', error);
                this.showNotification('Failed to execute chain', 'error');
            }
        },

        // Delete chain
        async deleteChain() {
            if (!this.currentChain.id) {
                this.showNotification('No chain to delete', 'error');
                return;
            }

            if (!confirm(`Delete chain "${this.currentChain.name}"? This cannot be undone.`)) {
                return;
            }

            try {
                const response = await fetch(`/api/chains/${this.currentChain.id}`, {
                    method: 'DELETE'
                });

                if (!response.ok) {
                    throw new Error('Failed to delete chain');
                }

                this.showNotification('Chain deleted', 'success');
                await this.loadChains();
                this.newChain();
            } catch (error) {
                console.error('Error deleting chain:', error);
                this.showNotification('Failed to delete chain', 'error');
            }
        },

        // Save chain to server
        async saveChain() {
            if (!this.validate()) {
                this.showNotification('Please fix validation errors', 'error');
                return;
            }

            if (!this.currentChain.name) {
                this.showNotification('Chain name is required', 'error');
                return;
            }

            this.isSaving = true;

            try {
                // Prepare chain data (remove visual properties)
                const chainData = {
                    name: this.currentChain.name,
                    description: this.currentChain.description,
                    category: this.currentChain.category,
                    risk_level: this.currentChain.risk_level,
                    steps: this.currentChain.steps.map(step => ({
                        tool: step.tool,
                        target: step.target,
                        type: step.type,
                        parameters: step.parameters,
                        timeout: step.timeout,
                        continue_on_error: step.continue_on_error
                    })),
                    metadata: {
                        ...this.currentChain.metadata,
                        created_with: 'chain_builder_ui',
                        step_positions: this.currentChain.steps.map(s => ({
                            id: s.id,
                            x: s.x,
                            y: s.y
                        }))
                    }
                };

                const url = this.currentChain.id ? `/api/chains/${this.currentChain.id}` : '/api/chains';
                const method = this.currentChain.id ? 'PUT' : 'POST';

                const response = await fetch(url, {
                    method: method,
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(chainData)
                });

                if (!response.ok) {
                    throw new Error('Failed to save chain');
                }

                const result = await response.json();
                this.showNotification('Chain saved successfully', 'success');

                // Update chain ID and metadata
                if (result.chain_id) {
                    this.currentChain.id = result.chain_id;
                }
                if (result.created_at) {
                    this.currentChain.created_at = result.created_at;
                }

                // Reload chains list
                await this.loadChains();

            } catch (error) {
                console.error('Error saving chain:', error);
                this.showNotification('Failed to save chain', 'error');
            } finally {
                this.isSaving = false;
            }
        },

        // Load chain from server
        async loadChain(chainId) {
            this.isLoading = true;

            try {
                const response = await fetch(`/api/chains/${chainId}`);
                if (!response.ok) {
                    throw new Error('Failed to load chain');
                }

                const data = await response.json();

                // Restore chain data
                this.currentChain = {
                    id: data.id || chainId,
                    name: data.name,
                    description: data.description,
                    category: data.category,
                    risk_level: data.risk_level,
                    steps: data.steps.map((step, idx) => ({
                        id: this.generateStepId(),
                        tool: step.tool,
                        target: step.target || '',
                        type: step.type || 'scan',
                        parameters: step.parameters || {},
                        parametersJson: JSON.stringify(step.parameters || {}, null, 2),
                        timeout: step.timeout || 300,
                        continue_on_error: step.continue_on_error || false,
                        description: step.description || '',
                        x: 100 + (idx % 3) * 200,
                        y: 100 + Math.floor(idx / 3) * 150
                    })),
                    metadata: data.metadata || {},
                    created_at: data.created_at
                };

                // Restore step positions if available
                if (data.metadata?.step_positions) {
                    data.metadata.step_positions.forEach(pos => {
                        const step = this.currentChain.steps.find(s => s.id === pos.id);
                        if (step) {
                            step.x = pos.x;
                            step.y = pos.y;
                        }
                    });
                }

                this.selectedStep = null;
                this.selectedStepIndex = -1;
                this.updateGraph();
                this.showNotification('Chain loaded', 'success');

            } catch (error) {
                console.error('Error loading chain:', error);
                this.showNotification('Failed to load chain', 'error');
            } finally {
                this.isLoading = false;
            }
        },

        // Update graph visualization
        updateGraph() {
            if (this.graph) {
                this.graph.update(this.currentChain.steps);
            }
        },

        // Handle canvas drop event
        handleCanvasDrop(position) {
            // This would be called when dragging from library
            console.log('Drop at position:', position);
        },

        // Auto-layout steps
        autoLayout() {
            // Simple force-directed layout
            const levels = this.getStepLevels();
            const levelGroups = {};

            levels.forEach((level, stepId) => {
                if (!levelGroups[level]) levelGroups[level] = [];
                levelGroups[level].push(stepId);
            });

            let y = 100;
            Object.keys(levelGroups).sort().forEach(level => {
                const steps = levelGroups[level];
                const spacing = 800 / (steps.length + 1);

                steps.forEach((stepId, index) => {
                    const step = this.currentChain.steps.find(s => s.id === stepId);
                    if (step) {
                        step.x = spacing * (index + 1);
                        step.y = y;
                    }
                });

                y += 150;
            });

            this.updateGraph();
        },

        // Get execution order levels
        getStepLevels() {
            const levels = new Map();

            const calculateLevel = (stepId, visited = new Set()) => {
                if (levels.has(stepId)) return levels.get(stepId);
                if (visited.has(stepId)) return 0; // Circular dependency

                visited.add(stepId);
                const step = this.currentChain.steps.find(s => s.id === stepId);
                const deps = step?.depends_on || [];
                if (!step || deps.length === 0) {
                    levels.set(stepId, 0);
                    return 0;
                }

                const maxDepLevel = Math.max(
                    ...deps.map(depId => calculateLevel(depId, new Set(visited)))
                );
                const level = maxDepLevel + 1;
                levels.set(stepId, level);
                return level;
            };

            this.currentChain.steps.forEach(step => calculateLevel(step.id));
            return levels;
        },

        // Generate unique step ID
        generateStepId() {
            return `step_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
        },

        // Show notification
        showNotification(message, type = 'info') {
            // Create notification element
            const notification = document.createElement('div');
            notification.className = `chain-notification chain-notification-${type}`;
            notification.textContent = message;

            document.body.appendChild(notification);

            setTimeout(() => {
                notification.classList.add('show');
            }, 10);

            setTimeout(() => {
                notification.classList.remove('show');
                setTimeout(() => notification.remove(), 300);
            }, 3000);
        },

        // Export chain as JSON
        exportChain() {
            const dataStr = JSON.stringify(this.currentChain, null, 2);
            const dataUri = 'data:application/json;charset=utf-8,' + encodeURIComponent(dataStr);

            const exportName = `${this.currentChain.name || 'chain'}_${Date.now()}.json`;

            const linkElement = document.createElement('a');
            linkElement.setAttribute('href', dataUri);
            linkElement.setAttribute('download', exportName);
            linkElement.click();
        },

        // Import chain from JSON
        importChain(event) {
            const file = event.target.files[0];
            if (!file) return;

            const reader = new FileReader();
            reader.onload = (e) => {
                try {
                    const imported = JSON.parse(e.target.result);
                    this.currentChain = imported;
                    this.updateGraph();
                    this.validate();
                    this.showNotification('Chain imported', 'success');
                } catch (error) {
                    console.error('Import error:', error);
                    this.showNotification('Failed to import chain', 'error');
                }
            };
            reader.readAsText(file);
        }
    }));
});

// ============================================================================
// D3.js Graph Visualization
// ============================================================================

class ChainGraph {
    constructor(containerId, callbacks = {}) {
        this.containerId = containerId;
        this.callbacks = callbacks;
        this.width = 900;
        this.height = 600;
        this.nodes = [];
        this.links = [];

        this.init();
    }

    init() {
        const container = d3.select(`#${this.containerId}`);
        container.selectAll('*').remove();

        // Create SVG
        this.svg = container.append('svg')
            .attr('width', '100%')
            .attr('height', '100%')
            .attr('viewBox', `0 0 ${this.width} ${this.height}`)
            .style('background', 'var(--darker-bg)');

        // Create zoom behavior
        const zoom = d3.zoom()
            .scaleExtent([0.5, 2])
            .on('zoom', (event) => {
                this.g.attr('transform', event.transform);
            });

        this.svg.call(zoom);

        // Main group for graph elements
        this.g = this.svg.append('g');

        // Layers
        this.linkLayer = this.g.append('g').attr('class', 'links');
        this.nodeLayer = this.g.append('g').attr('class', 'nodes');

        // Arrow marker for dependencies
        this.svg.append('defs').append('marker')
            .attr('id', 'arrowhead')
            .attr('viewBox', '0 -5 10 10')
            .attr('refX', 35)
            .attr('refY', 0)
            .attr('markerWidth', 6)
            .attr('markerHeight', 6)
            .attr('orient', 'auto')
            .append('path')
            .attr('d', 'M0,-5L10,0L0,5')
            .attr('fill', '#00ff00');

        // Error marker
        this.svg.select('defs').append('marker')
            .attr('id', 'arrowhead-error')
            .attr('viewBox', '0 -5 10 10')
            .attr('refX', 35)
            .attr('refY', 0)
            .attr('markerWidth', 6)
            .attr('markerHeight', 6)
            .attr('orient', 'auto')
            .append('path')
            .attr('d', 'M0,-5L10,0L0,5')
            .attr('fill', '#ff0040');

        // Force simulation
        this.simulation = d3.forceSimulation()
            .force('link', d3.forceLink().id(d => d.id).distance(150))
            .force('charge', d3.forceManyBody().strength(-300))
            .force('center', d3.forceCenter(this.width / 2, this.height / 2))
            .force('collision', d3.forceCollide().radius(50));
    }

    update(steps) {
        this.nodes = steps.map(step => ({
            id: step.id,
            tool: step.tool,
            x: step.x,
            y: step.y,
            description: step.description
        }));

        this.links = [];
        steps.forEach(step => {
            step.depends_on.forEach(depId => {
                this.links.push({
                    source: depId,
                    target: step.id
                });
            });
        });

        this.render();
    }

    render() {
        // Update links
        const link = this.linkLayer.selectAll('.link')
            .data(this.links, d => `${d.source.id || d.source}-${d.target.id || d.target}`);

        link.exit().remove();

        const linkEnter = link.enter().append('line')
            .attr('class', 'link')
            .attr('stroke', '#00ff00')
            .attr('stroke-width', 2)
            .attr('marker-end', 'url(#arrowhead)')
            .style('opacity', 0.6);

        const linkMerge = linkEnter.merge(link);

        // Update nodes
        const node = this.nodeLayer.selectAll('.node')
            .data(this.nodes, d => d.id);

        node.exit().remove();

        const nodeEnter = node.enter().append('g')
            .attr('class', 'node')
            .call(d3.drag()
                .on('start', (event, d) => this.dragStarted(event, d))
                .on('drag', (event, d) => this.dragged(event, d))
                .on('end', (event, d) => this.dragEnded(event, d)))
            .on('click', (event, d) => {
                if (this.callbacks.onStepClick) {
                    this.callbacks.onStepClick(d.id);
                }
            });

        // Node circle
        nodeEnter.append('circle')
            .attr('r', 30)
            .attr('fill', 'var(--card-bg)')
            .attr('stroke', '#00ff00')
            .attr('stroke-width', 2)
            .style('cursor', 'pointer');

        // Node icon (tool initial)
        nodeEnter.append('text')
            .attr('class', 'node-icon')
            .attr('text-anchor', 'middle')
            .attr('dy', '.3em')
            .attr('fill', '#00ff00')
            .style('font-size', '18px')
            .style('font-weight', 'bold')
            .style('pointer-events', 'none')
            .text(d => d.tool ? d.tool.substring(0, 2).toUpperCase() : '??');

        // Node label
        nodeEnter.append('text')
            .attr('class', 'node-label')
            .attr('text-anchor', 'middle')
            .attr('dy', '50')
            .attr('fill', '#00ff00')
            .style('font-size', '12px')
            .style('pointer-events', 'none')
            .text(d => d.tool);

        const nodeMerge = nodeEnter.merge(node);

        // Update simulation
        this.simulation.nodes(this.nodes);
        this.simulation.force('link').links(this.links);

        // Position nodes at their saved positions
        this.nodes.forEach(node => {
            if (node.x !== undefined) node.fx = node.x;
            if (node.y !== undefined) node.fy = node.y;
        });

        this.simulation.alpha(0.3).restart();

        this.simulation.on('tick', () => {
            linkMerge
                .attr('x1', d => d.source.x)
                .attr('y1', d => d.source.y)
                .attr('x2', d => d.target.x)
                .attr('y2', d => d.target.y);

            nodeMerge.attr('transform', d => `translate(${d.x},${d.y})`);
        });
    }

    highlightNode(nodeId) {
        this.nodeLayer.selectAll('.node')
            .select('circle')
            .attr('stroke', d => d.id === nodeId ? '#00ffff' : '#00ff00')
            .attr('stroke-width', d => d.id === nodeId ? 3 : 2)
            .style('filter', d => d.id === nodeId ? 'drop-shadow(0 0 10px #00ffff)' : 'none');
    }

    highlightErrors(circularPaths) {
        // Extract step IDs involved in circular dependencies
        const errorSteps = new Set();
        circularPaths.forEach(path => {
            path.split(' → ').forEach(id => errorSteps.add(id));
        });

        // Highlight error nodes
        this.nodeLayer.selectAll('.node')
            .select('circle')
            .attr('stroke', d => errorSteps.has(d.id) ? '#ff0040' : '#00ff00')
            .style('filter', d => errorSteps.has(d.id) ? 'drop-shadow(0 0 10px #ff0040)' : 'none');

        // Highlight error links
        this.linkLayer.selectAll('.link')
            .attr('stroke', d => {
                const sourceId = d.source.id || d.source;
                const targetId = d.target.id || d.target;
                return (errorSteps.has(sourceId) && errorSteps.has(targetId)) ? '#ff0040' : '#00ff00';
            })
            .attr('marker-end', d => {
                const sourceId = d.source.id || d.source;
                const targetId = d.target.id || d.target;
                return (errorSteps.has(sourceId) && errorSteps.has(targetId))
                    ? 'url(#arrowhead-error)'
                    : 'url(#arrowhead)';
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
        // Keep node at dragged position
        d.fx = event.x;
        d.fy = event.y;
    }
}

// Export for global use
window.ChainGraph = ChainGraph;
