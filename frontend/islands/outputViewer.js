/**
 * Output Viewer Island - Dual Terminal/Structured View Toggle
 */

import { h, Component } from 'preact';

export default class OutputViewerIsland extends Component {
  constructor(props) {
    super(props);
    this.state = {
      viewMode: 'structured', // 'terminal' or 'structured'
      results: [],
      selectedResult: null
    };
  }

  componentDidMount() {
    this.fetchResults();
  }

  async fetchResults() {
    try {
      const response = await fetch('/api/results');
      const results = await response.json();
      this.setState({ results });
    } catch (error) {
      console.error('Failed to fetch results:', error);
    }
  }

  toggleView() {
    this.setState({ viewMode: this.state.viewMode === 'terminal' ? 'structured' : 'terminal' });
  }

  selectResult(result) {
    this.setState({ selectedResult: result });
  }

  render() {
    const { viewMode, results, selectedResult } = this.state;

    return h('div', { class: 'output-viewer-island grid grid-cols-1 lg:grid-cols-4 gap-4 h-full' },
      // Results List
      h('div', { class: 'lg:col-span-1 bg-tactical-card rounded-lg border border-tactical-border overflow-hidden' },
        h('div', { class: 'p-4 border-b border-tactical-border' },
          h('h3', { class: 'text-tactical-text font-display' }, 'Execution History')
        ),
        h('div', { class: 'overflow-y-auto max-h-96' },
          results.map(result => this.renderResultItem(result))
        )
      ),

      // Output Display
      h('div', { class: 'lg:col-span-3 bg-tactical-card rounded-lg border border-tactical-border overflow-hidden flex flex-col' },
        // Header with view toggle
        h('div', { class: 'p-4 border-b border-tactical-border flex items-center justify-between' },
          h('h3', { class: 'text-tactical-text font-display' },
            selectedResult ? `${selectedResult.tool} - ${selectedResult.id}` : 'Select a result'
          ),
          h('div', { class: 'flex gap-2' },
            h('button', {
              class: `px-3 py-1 rounded text-sm ${viewMode === 'terminal' ? 'bg-military-green text-tactical-bg' : 'bg-tactical-surface text-tactical-text'}`,
              onClick: () => this.setState({ viewMode: 'terminal' })
            }, 'Terminal'),
            h('button', {
              class: `px-3 py-1 rounded text-sm ${viewMode === 'structured' ? 'bg-military-green text-tactical-bg' : 'bg-tactical-surface text-tactical-text'}`,
              onClick: () => this.setState({ viewMode: 'structured' })
            }, 'Structured')
          )
        ),

        // Content
        h('div', { class: 'flex-1 overflow-auto p-4' },
          selectedResult
            ? viewMode === 'terminal'
              ? this.renderTerminalView(selectedResult)
              : this.renderStructuredView(selectedResult)
            : h('div', { class: 'flex items-center justify-center h-full text-tactical-muted' },
                'Select an execution to view results'
              )
        )
      )
    );
  }

  renderResultItem(result) {
    const statusColors = {
      completed: 'military-green',
      failed: 'military-red',
      running: 'military-amber'
    };

    const color = statusColors[result.status] || 'tactical-muted';

    return h('div', {
      class: `p-3 border-b border-tactical-border cursor-pointer hover:bg-tactical-surface transition-colors ${
        this.state.selectedResult?.id === result.id ? 'bg-tactical-surface' : ''
      }`,
      onClick: () => this.selectResult(result)
    },
      h('div', { class: 'flex items-center justify-between mb-1' },
        h('span', { class: 'text-tactical-text font-semibold text-sm' }, result.tool),
        h('span', { class: `text-xs px-2 py-1 rounded bg-${color} bg-opacity-20 text-${color}` }, result.status)
      ),
      h('p', { class: 'text-tactical-muted text-xs' }, new Date(result.timestamp).toLocaleString())
    );
  }

  renderTerminalView(result) {
    return h('div', { class: 'font-mono text-sm bg-tactical-bg p-4 rounded' },
      result.output.map(line =>
        h('div', { class: 'text-tactical-text whitespace-pre-wrap' }, line.data)
      )
    );
  }

  renderStructuredView(result) {
    if (!result.parsed_data) {
      return h('div', { class: 'text-tactical-muted' }, 'No structured data available');
    }

    return h('div', { class: 'space-y-4' },
      // Summary
      h('div', { class: 'bg-tactical-surface p-4 rounded' },
        h('h4', { class: 'text-military-green font-semibold mb-2' }, 'Summary'),
        h('div', { class: 'grid grid-cols-2 gap-4' },
          h('div', null,
            h('span', { class: 'text-tactical-muted text-sm' }, 'Tool'),
            h('p', { class: 'text-tactical-text' }, result.tool)
          ),
          h('div', null,
            h('span', { class: 'text-tactical-muted text-sm' }, 'Duration'),
            h('p', { class: 'text-tactical-text' }, `${result.duration}s`)
          ),
          h('div', null,
            h('span', { class: 'text-tactical-muted text-sm' }, 'Return Code'),
            h('p', { class: result.return_code === 0 ? 'text-military-green' : 'text-military-red' }, result.return_code)
          ),
          h('div', null,
            h('span', { class: 'text-tactical-muted text-sm' }, 'Status'),
            h('p', { class: 'text-tactical-text' }, result.status)
          )
        )
      ),

      // Parsed Data
      h('div', { class: 'bg-tactical-surface p-4 rounded' },
        h('h4', { class: 'text-military-green font-semibold mb-2' }, 'Parsed Results'),
        h('pre', { class: 'text-tactical-text text-sm overflow-auto' },
          JSON.stringify(result.parsed_data, null, 2)
        )
      )
    );
  }
}
