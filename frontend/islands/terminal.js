/**
 * Terminal Island - xterm.js WebSocket Terminal
 */

import { h, Component } from 'preact';
import { Terminal } from 'xterm';
import { FitAddon } from 'xterm-addon-fit';
import { WebLinksAddon } from 'xterm-addon-web-links';
import wsService from '../services/websocket.js';
import 'xterm/css/xterm.css';

export default class TerminalIsland extends Component {
  constructor(props) {
    super(props);
    this.state = {
      connected: false,
      executionId: null
    };
    this.terminalRef = null;
    this.terminal = null;
    this.fitAddon = null;
  }

  componentDidMount() {
    this.initTerminal();
    this.connectWebSocket();
  }

  componentWillUnmount() {
    if (this.terminal) {
      this.terminal.dispose();
    }
  }

  initTerminal() {
    // Create terminal instance
    this.terminal = new Terminal({
      cursorBlink: true,
      fontSize: 14,
      fontFamily: 'JetBrains Mono, Fira Code, monospace',
      theme: {
        background: '#0a0f14',
        foreground: '#c9d1d9',
        cursor: '#4caf50',
        cursorAccent: '#0a0f14',
        selection: 'rgba(76, 175, 80, 0.3)',
        black: '#0a0f14',
        red: '#f44336',
        green: '#4caf50',
        yellow: '#ffc107',
        blue: '#2196f3',
        magenta: '#9c27b0',
        cyan: '#00bcd4',
        white: '#c9d1d9',
        brightBlack: '#586e75',
        brightRed: '#e57373',
        brightGreen: '#81c784',
        brightYellow: '#ffd54f',
        brightBlue: '#64b5f6',
        brightMagenta: '#ba68c8',
        brightCyan: '#4dd0e1',
        brightWhite: '#ffffff'
      },
      allowProposedApi: true
    });

    // Add addons
    this.fitAddon = new FitAddon();
    this.terminal.loadAddon(this.fitAddon);
    this.terminal.loadAddon(new WebLinksAddon());

    // Open terminal in container
    this.terminal.open(this.terminalRef);
    this.fitAddon.fit();

    // Welcome message
    this.terminal.writeln('\x1b[1;32m╔═══════════════════════════════════════════════════════════╗\x1b[0m');
    this.terminal.writeln('\x1b[1;32m║         Red Team C2 Terminal - Ready for Combat          ║\x1b[0m');
    this.terminal.writeln('\x1b[1;32m╚═══════════════════════════════════════════════════════════╝\x1b[0m');
    this.terminal.writeln('');
    this.terminal.writeln('\x1b[1;33mType commands or execute attack chains from the UI\x1b[0m');
    this.terminal.writeln('');

    // Handle window resize
    window.addEventListener('resize', () => {
      this.fitAddon.fit();
    });
  }

  connectWebSocket() {
    if (!wsService.socket) {
      wsService.connect();
    }

    // Connection status
    wsService.on('connection', (data) => {
      this.setState({ connected: data.status === 'connected' });

      if (data.status === 'connected') {
        this.terminal.writeln('\x1b[1;32m✓ WebSocket connected\x1b[0m');
      } else if (data.status === 'disconnected') {
        this.terminal.writeln('\x1b[1;31m✗ WebSocket disconnected\x1b[0m');
      }
    });

    // Tool output streaming
    wsService.on('tool_output', (data) => {
      this.handleToolOutput(data);
    });

    wsService.on('tool_complete', (data) => {
      const duration = data.duration ? ` (${data.duration.toFixed(2)}s)` : '';
      const status = data.return_code === 0 ? '\x1b[1;32m✓ COMPLETED' : '\x1b[1;31m✗ FAILED';
      this.terminal.writeln('');
      this.terminal.writeln(`${status}\x1b[0m${duration}`);
      this.terminal.writeln('─'.repeat(60));
      this.terminal.writeln('');
    });

    wsService.on('tool_error', (data) => {
      this.terminal.writeln(`\x1b[1;31m✗ ERROR: ${data.error || data.data}\x1b[0m`);
    });

    // Chain progress
    wsService.on('chain_progress', (data) => {
      if (data.type === 'step_start') {
        this.terminal.writeln('');
        this.terminal.writeln(`\x1b[1;36m▶ Starting: ${data.tool}\x1b[0m`);
        this.terminal.writeln('─'.repeat(60));
      }
    });
  }

  handleToolOutput(data) {
    if (!data || !data.data) return;

    const output = data.data;
    const type = data.type || 'stdout';

    // Color code based on type
    let coloredOutput = output;
    if (type === 'stderr') {
      coloredOutput = `\x1b[1;33m${output}\x1b[0m`; // Yellow for stderr
    } else if (output.includes('ERROR') || output.includes('FAIL')) {
      coloredOutput = `\x1b[1;31m${output}\x1b[0m`; // Red for errors
    } else if (output.includes('SUCCESS') || output.includes('FOUND') || output.includes('OPEN')) {
      coloredOutput = `\x1b[1;32m${output}\x1b[0m`; // Green for success
    }

    this.terminal.writeln(coloredOutput);
  }

  executeTool(tool, args) {
    this.terminal.writeln(`\x1b[1;36m▶ Executing: ${tool}\x1b[0m`);
    this.terminal.writeln('─'.repeat(60));

    wsService.executeTool(tool, args)
      .catch(err => {
        this.terminal.writeln(`\x1b[1;31m✗ Execution failed: ${err.message}\x1b[0m`);
      });
  }

  render() {
    const { connected } = this.state;

    return h('div', { class: 'terminal-island h-full flex flex-col' },
      // Status bar
      h('div', { class: 'flex items-center justify-between px-4 py-2 bg-tactical-surface border-b border-tactical-border' },
        h('div', { class: 'flex items-center gap-2' },
          h('div', { class: `w-2 h-2 rounded-full ${connected ? 'bg-military-green animate-pulse' : 'bg-status-offline'}` }),
          h('span', { class: 'text-sm text-tactical-text font-mono' },
            connected ? 'TERMINAL ACTIVE' : 'DISCONNECTED'
          )
        ),
        h('div', { class: 'flex gap-2' },
          h('button', {
            class: 'px-3 py-1 text-xs bg-tactical-card hover:bg-tactical-border rounded border border-tactical-border text-tactical-text',
            onClick: () => this.terminal.clear()
          }, 'Clear'),
          h('button', {
            class: 'px-3 py-1 text-xs bg-tactical-card hover:bg-tactical-border rounded border border-tactical-border text-tactical-text',
            onClick: () => this.fitAddon.fit()
          }, 'Fit')
        )
      ),

      // Terminal container
      h('div', {
        ref: ref => this.terminalRef = ref,
        class: 'flex-1 p-2 bg-tactical-bg'
      })
    );
  }
}
