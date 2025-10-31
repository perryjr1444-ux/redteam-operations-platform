/**
 * Terminal Component using xterm.js
 * Real-time container output streaming
 */

class ContainerTerminal {
    constructor(containerId, elementId) {
        this.containerId = containerId;
        this.elementId = elementId;
        this.term = null;
        this.socket = null;
        this.fitAddon = null;
    }

    async init() {
        // Initialize xterm.js
        this.term = new Terminal({
            cursorBlink: true,
            fontSize: 14,
            fontFamily: '"JetBrains Mono", "Fira Code", monospace',
            theme: {
                background: '#0a0e1a',
                foreground: '#00ff00',
                cursor: '#00ff00',
                selection: '#00ff0044',
                black: '#000000',
                red: '#ff0000',
                green: '#00ff00',
                yellow: '#ffff00',
                blue: '#0000ff',
                magenta: '#ff00ff',
                cyan: '#00ffff',
                white: '#ffffff',
                brightBlack: '#555555',
                brightRed: '#ff5555',
                brightGreen: '#55ff55',
                brightYellow: '#ffff55',
                brightBlue: '#5555ff',
                brightMagenta: '#ff55ff',
                brightCyan: '#55ffff',
                brightWhite: '#ffffff'
            },
            allowTransparency: true,
            scrollback: 10000,
        });

        // Add fit addon for responsive sizing
        this.fitAddon = new FitAddon.FitAddon();
        this.term.loadAddon(this.fitAddon);

        // Open terminal in DOM
        const element = document.getElementById(this.elementId);
        this.term.open(element);

        // Fit to container
        this.fitAddon.fit();

        // Resize handler
        window.addEventListener('resize', () => {
            this.fitAddon.fit();
        });

        // Connect to WebSocket
        this.connect();
    }

    connect() {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/ws/terminal/${this.containerId}`;

        this.socket = new WebSocket(wsUrl);

        this.socket.onopen = () => {
            this.term.write('\x1b[36m[Terminal] Connected to container stream\x1b[0m\r\n');
        };

        this.socket.onmessage = (event) => {
            // Write data to terminal with ANSI color support
            this.term.write(event.data);
        };

        this.socket.onerror = (error) => {
            this.term.write('\x1b[31m[Terminal] Connection error\x1b[0m\r\n');
            console.error('WebSocket error:', error);
        };

        this.socket.onclose = () => {
            this.term.write('\r\n\x1b[33m[Terminal] Connection closed\x1b[0m\r\n');
        };
    }

    disconnect() {
        if (this.socket) {
            this.socket.close();
        }
        if (this.term) {
            this.term.dispose();
        }
    }

    clear() {
        if (this.term) {
            this.term.clear();
        }
    }
}

// Global terminal instances
const terminals = {};

// Initialize terminal for container
function initTerminal(containerId, elementId = 'terminal') {
    if (terminals[containerId]) {
        terminals[containerId].disconnect();
    }

    const terminal = new ContainerTerminal(containerId, elementId);
    terminal.init();
    terminals[containerId] = terminal;

    return terminal;
}

// Cleanup terminal
function closeTerminal(containerId) {
    if (terminals[containerId]) {
        terminals[containerId].disconnect();
        delete terminals[containerId];
    }
}
