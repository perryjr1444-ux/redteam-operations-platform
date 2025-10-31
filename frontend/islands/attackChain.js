/**
 * Attack Chain Builder Island - Drag & Drop Workflow
 */

import { h, Component } from 'preact';
import Sortable from 'sortablejs';
import wsService from '../services/websocket.js';

export default class AttackChainIsland extends Component {
  constructor(props) {
    super(props);
    console.log('[AttackChain] Constructor called');
    this.state = {
      availableTools: [],
      chainSteps: [],
      isExecuting: false,
      executionProgress: null
    };
    this.toolsRef = null;
    this.stepsRef = null;
  }

  componentDidMount() {
    console.log('[AttackChain] componentDidMount called');
    this.fetchTools();
    this.connectWebSocket();

    // Defer Sortable initialization to ensure refs are attached
    setTimeout(() => {
      console.log('[AttackChain] Attempting to initialize Sortable...');
      console.log('[AttackChain] toolsRef:', this.toolsRef);
      console.log('[AttackChain] stepsRef:', this.stepsRef);
      this.initSortable();
    }, 100);
  }

  async fetchTools() {
    console.log('[AttackChain] Fetching tools...');
    try {
      const response = await fetch('/api/tools');
      const tools = await response.json();
      console.log('[AttackChain] Received tools:', tools.length);
      this.setState({ availableTools: tools });
    } catch (error) {
      console.error('[AttackChain] Failed to fetch tools:', error);
    }
  }

  initSortable() {
    // Tool palette (clone on drag)
    if (this.toolsRef) {
      console.log('[AttackChain] Initializing Sortable for tools palette');
      new Sortable(this.toolsRef, {
        group: {
          name: 'tools',
          pull: 'clone',
          put: false
        },
        animation: 150,
        sort: false
      });
    } else {
      console.warn('[AttackChain] toolsRef not found, skipping tools palette Sortable initialization');
    }

    // Chain steps (allow sorting and adding)
    if (this.stepsRef) {
      console.log('[AttackChain] Initializing Sortable for chain steps');
      new Sortable(this.stepsRef, {
        group: 'tools',
        animation: 150,
        onAdd: (evt) => this.handleStepAdd(evt),
        onUpdate: (evt) => this.handleStepReorder(evt)
      });
    } else {
      console.warn('[AttackChain] stepsRef not found, skipping steps Sortable initialization');
    }
  }

  handleStepAdd(evt) {
    const toolIndex = evt.oldIndex;
    const tool = this.state.availableTools[toolIndex];

    if (!tool) return;

    const newStep = {
      id: `step_${Date.now()}`,
      tool: tool.name,
      category: tool.category,
      description: tool.description,
      args: {},
      depends_on: []
    };

    const newSteps = [...this.state.chainSteps];
    newSteps.splice(evt.newIndex, 0, newStep);

    this.setState({ chainSteps: newSteps });
  }

  handleStepReorder(evt) {
    const steps = [...this.state.chainSteps];
    const [moved] = steps.splice(evt.oldIndex, 1);
    steps.splice(evt.newIndex, 0, moved);

    this.setState({ chainSteps: steps });
  }

  removeStep(stepId) {
    this.setState({
      chainSteps: this.state.chainSteps.filter(s => s.id !== stepId)
    });
  }

  updateStepArgs(stepId, args) {
    this.setState({
      chainSteps: this.state.chainSteps.map(step =>
        step.id === stepId ? { ...step, args: { ...step.args, ...args } } : step
      )
    });
  }

  connectWebSocket() {
    if (!wsService.socket) {
      wsService.connect();
    }

    wsService.on('chain_progress', (data) => {
      this.setState({ executionProgress: data });
    });

    wsService.on('chain_complete', (data) => {
      this.setState({ isExecuting: false, executionProgress: null });
      alert('Attack chain completed!');
    });
  }

  async executeChain() {
    if (this.state.chainSteps.length === 0) {
      alert('Add some tools to the chain first!');
      return;
    }

    this.setState({ isExecuting: true });

    const chainConfig = {
      id: `chain_${Date.now()}`,
      name: 'Custom Attack Chain',
      steps: this.state.chainSteps
    };

    try {
      await wsService.executeChain(chainConfig.id, chainConfig);
    } catch (error) {
      alert(`Chain execution failed: ${error.message}`);
      this.setState({ isExecuting: false });
    }
  }

  render() {
    const { availableTools, chainSteps, isExecuting, executionProgress } = this.state;
    console.log('[AttackChain] Rendering with', availableTools.length, 'tools and', chainSteps.length, 'steps');

    return h('div', { class: 'attack-chain-island grid grid-cols-1 lg:grid-cols-3 gap-6' },
      // Tool Palette
      h('div', { class: 'lg:col-span-1' },
        h('div', { class: 'bg-tactical-card rounded-lg border border-tactical-border' },
          h('div', { class: 'p-4 border-b border-tactical-border' },
            h('h3', { class: 'text-tactical-text font-display text-lg' }, 'Tool Palette'),
            h('p', { class: 'text-tactical-muted text-sm mt-1' }, 'Drag tools to build your attack chain')
          ),
          h('div', {
            ref: ref => this.toolsRef = ref,
            class: 'p-4 space-y-2 max-h-96 overflow-y-auto'
          }, availableTools.map(tool => this.renderToolCard(tool)))
        )
      ),

      // Chain Builder
      h('div', { class: 'lg:col-span-2' },
        h('div', { class: 'bg-tactical-card rounded-lg border border-tactical-border' },
          h('div', { class: 'p-4 border-b border-tactical-border flex items-center justify-between' },
            h('div', null,
              h('h3', { class: 'text-tactical-text font-display text-lg' }, 'Attack Chain'),
              h('p', { class: 'text-tactical-muted text-sm mt-1' }, `${chainSteps.length} steps configured`)
            ),
            h('button', {
              class: `px-4 py-2 rounded font-semibold transition-colors ${
                isExecuting
                  ? 'bg-status-warning text-tactical-bg cursor-not-allowed'
                  : 'bg-military-green hover:bg-military-green-dark text-tactical-bg'
              }`,
              onClick: () => this.executeChain(),
              disabled: isExecuting
            }, isExecuting ? 'EXECUTING...' : 'EXECUTE CHAIN')
          ),

          h('div', {
            ref: ref => this.stepsRef = ref,
            class: 'p-4 space-y-3 min-h-64'
          },
            chainSteps.length === 0
              ? h('div', { class: 'flex items-center justify-center h-64 text-tactical-muted' },
                  'Drag tools here to build your attack chain'
                )
              : chainSteps.map((step, idx) => this.renderChainStep(step, idx))
          )
        ),

        // Execution Progress
        executionProgress && h('div', { class: 'mt-4 bg-tactical-card rounded-lg border border-military-amber p-4' },
          h('div', { class: 'flex items-center gap-2 mb-2' },
            h('div', { class: 'w-3 h-3 bg-military-amber rounded-full animate-pulse' }),
            h('span', { class: 'text-military-amber font-semibold' }, 'EXECUTING')
          ),
          h('p', { class: 'text-tactical-text text-sm' },
            executionProgress.step_id ? `Step: ${executionProgress.tool}` : 'Initializing...'
          )
        )
      )
    );
  }

  renderToolCard(tool) {
    const categoryColors = {
      information_gathering: 'blue',
      vulnerability_analysis: 'yellow',
      web_application: 'green',
      exploitation: 'red',
      post_exploitation: 'purple'
    };

    const color = categoryColors[tool.category] || 'gray';

    return h('div', {
      class: 'p-3 bg-tactical-surface border border-tactical-border rounded cursor-move hover:border-military-green transition-colors',
      'data-tool': tool.name
    },
      h('div', { class: 'flex items-center justify-between mb-1' },
        h('span', { class: 'text-tactical-text font-semibold text-sm' }, tool.name),
        h('span', { class: `text-xs px-2 py-1 rounded bg-${color}-900 text-${color}-300` },
          tool.category.replace('_', ' ')
        )
      ),
      h('p', { class: 'text-tactical-muted text-xs' }, tool.description)
    );
  }

  renderChainStep(step, index) {
    const categoryColors = {
      information_gathering: 'blue',
      vulnerability_analysis: 'yellow',
      web_application: 'green',
      exploitation: 'red',
      post_exploitation: 'purple'
    };

    const color = categoryColors[step.category] || 'gray';

    return h('div', { class: 'p-4 bg-tactical-surface border border-tactical-border rounded hover:border-military-green transition-colors' },
      h('div', { class: 'flex items-start justify-between mb-3' },
        h('div', { class: 'flex items-center gap-2' },
          h('span', { class: 'text-military-green font-bold' }, `${index + 1}.`),
          h('span', { class: 'text-tactical-text font-semibold' }, step.tool),
          h('span', {
            class: `text-xs px-2 py-1 rounded ml-2`,
            style: `background-color: rgb(${color === 'blue' ? '30 58 138' : color === 'yellow' ? '113 63 18' : color === 'green' ? '20 83 45' : color === 'red' ? '127 29 29' : color === 'purple' ? '88 28 135' : '31 41 55'}); color: rgb(${color === 'blue' ? '147 197 253' : color === 'yellow' ? '253 224 71' : color === 'green' ? '134 239 172' : color === 'red' ? '252 165 165' : color === 'purple' ? '216 180 254' : '156 163 175'});`
          }, step.category ? step.category.replace('_', ' ').toUpperCase() : 'TOOL')
        ),
        h('button', {
          class: 'text-military-red hover:text-red-400 transition-colors',
          onClick: () => this.removeStep(step.id)
        }, h('i', { class: 'bi bi-trash' }))
      ),

      // Argument inputs (simplified)
      h('div', { class: 'ml-6 space-y-2' },
        h('input', {
          type: 'text',
          placeholder: 'Target (e.g., example.com)',
          class: 'w-full px-3 py-1 bg-tactical-bg border border-tactical-border rounded text-tactical-text text-sm',
          value: step.args.target || '',
          onInput: (e) => this.updateStepArgs(step.id, { target: e.target.value })
        }),
        h('input', {
          type: 'text',
          placeholder: 'Additional arguments',
          class: 'w-full px-3 py-1 bg-tactical-bg border border-tactical-border rounded text-tactical-text text-sm',
          value: step.args.extra || '',
          onInput: (e) => this.updateStepArgs(step.id, { extra: e.target.value })
        })
      )
    );
  }
}
