/**
 * Islands Entry Point
 *
 * Initializes all island components on page load
 */

// Import Tailwind CSS
import './main.css';

console.log('[Islands] Script loading...');

import { initializeIslands } from './lib/island.js';
import TerminalIsland from './islands/terminal.js';
import MetricsIsland from './islands/metrics.js';
import AttackChainIsland from './islands/attackChain.js';
import OutputViewerIsland from './islands/outputViewer.js';
import ThreatMapIsland from './islands/threatMap.js';
import wsService from './services/websocket.js';

console.log('[Islands] All imports loaded successfully');

// Register all islands
const islands = {
    terminal: TerminalIsland,
    metrics: MetricsIsland,
    attackChain: AttackChainIsland,
    outputViewer: OutputViewerIsland,
    threatMap: ThreatMapIsland
};

console.log('[Islands] Registered islands:', Object.keys(islands));

// Connect WebSocket once globally (shared by all islands)
wsService.connect();

// Initialize on DOMContentLoaded
console.log('[Islands] Calling initializeIslands...');
initializeIslands(islands);
console.log('[Islands] initializeIslands called');
