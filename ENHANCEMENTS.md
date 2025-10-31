[8m# Red Team Web App Enhancements

## Overview
The Red Team Command Center has been enhanced with a cyberpunk/hacker aesthetic and real-time terminal emulation for live container output streaming.

## What's New

### 1. **Cyberpunk Theme** 🎨
- **Neon Green (#00ff00)** primary color scheme with glowing effects
- **Scanline animation** overlay for authentic CRT monitor effect
- **Pulsing metric cards** with animated values
- **Glitch effects** on headers
- **Terminal-style fonts** (JetBrains Mono, Fira Code)
- **Grid background pattern** with subtle green glow

**Files:**
- `/static/css/cyberpunk.css` - Complete theme stylesheet

### 2. **Real-Time Terminal Emulation** 💻
- **xterm.js integration** for browser-based terminal
- **WebSocket streaming** for live container log output
- **Sliding sidebar panel** that appears on the right side
- **ANSI color support** for formatted terminal output
- **Auto-connect** when launching attacks

**Features:**
- Real-time log streaming from containers
- Terminal controls: Clear, Disconnect
- Responsive design (mobile-friendly)
- Dark overlay when terminal is open

**Files:**
- `/app/websocket_terminal.py` - WebSocket server for terminal streaming
- `/static/js/terminal.js` - Terminal component with xterm.js
- `/templates/attacks.html` - Enhanced with terminal sidebar

### 3. **Interactive Data Visualizations** 📊
- **Chart.js integration** with cyberpunk color scheme
- **Animated counters** for metric cards
- **Timeline charts** for exercise activity
- **Success rate pie charts** with neon colors
- **Auto-updating metrics** every 5 seconds

**Chart Types:**
- Success Rate Doughnut Chart
- Exercise Timeline Line Chart
- Attack Type Distribution Bar Chart

**Files:**
- `/static/js/charts.js` - Chart configurations and animations
- `/templates/dashboard.html` - Enhanced with metric cards and charts

### 4. **WebSocket Support** 🔌
- **New endpoint:** `ws://localhost:5172/ws/terminal/{container_id}`
- **TerminalStreamer class** manages WebSocket connections
- **Live log following** with `podman logs -f`
- **Automatic reconnection** support

**Files:**
- `/app/websocket_terminal.py` - WebSocket handler
- `/app/main.py` - Added WebSocket route

## How to Use

### Access the Application
```bash
# Application is running at:
http://localhost:5172
```

### Launch an Attack with Live Terminal

1. Navigate to **Attacks** page
2. Fill out any attack form (Nmap, SQLMap, Metasploit, Custom)
3. Click **Launch** button
4. Terminal sidebar automatically opens on the right
5. Watch **real-time output** stream from the container

### View Logs for Existing Containers

1. Go to **Attacks** page
2. Scroll to **Active Attack Containers** table
3. Click the **📄** (logs) button
4. Terminal sidebar opens with live streaming

### Dashboard Metrics

1. Navigate to **Dashboard**
2. Watch **animated metric cards** count up
3. View **cyberpunk-themed charts** with glowing effects
4. Metrics **auto-refresh** every 5 seconds

## Testing the Enhancements

### Test Terminal with MCP Container

```bash
# The terminal can connect to any running container
# For example, test with mcp-nmap:
curl -X POST http://localhost:5172/api/attacks/nmap \
  -F "target=scanme.nmap.org" \
  -F "scan_type=quick"

# Then view the logs in the web interface
```

### Test WebSocket Directly (Optional)

```javascript
// Open browser console on http://localhost:5172/attacks
const ws = new WebSocket('ws://localhost:5172/ws/terminal/mcp-nmap');
ws.onmessage = (event) => console.log(event.data);
ws.onopen = () => console.log('Connected!');
```

## Architecture

```
┌─────────────────┐
│   Browser UI    │
│  (Terminal)     │
└────────┬────────┘
         │ WebSocket
         ↓
┌─────────────────┐
│  FastAPI Server │
│  /ws/terminal/  │
└────────┬────────┘
         │ subprocess
         ↓
┌─────────────────┐
│  Podman Logs    │
│  (Container)    │
└─────────────────┘
```

## Libraries Added

- **xterm.js** (v5.3.0) - Terminal emulator
- **xterm-addon-fit** (v0.8.0) - Responsive terminal sizing
- **Chart.js** (v4.4.0) - Data visualizations
- **Notyf** (v3) - Toast notifications
- **websockets** (v14.1) - Python WebSocket library

## Color Palette

```css
--neon-green: #00ff00   /* Primary */
--neon-cyan: #00ffff    /* Secondary */
--neon-pink: #ff00ff    /* Accent */
--neon-red: #ff0040     /* Danger */
--dark-bg: #0a0e1a      /* Background */
--darker-bg: #050810    /* Cards */
```

## File Changes Summary

**New Files:**
- `/app/websocket_terminal.py`
- `/static/css/cyberpunk.css`
- `/static/js/terminal.js`
- `/static/js/charts.js`

**Modified Files:**
- `/app/main.py` - Added WebSocket endpoint
- `/templates/base.html` - Added library imports
- `/templates/attacks.html` - Added terminal sidebar
- `/templates/dashboard.html` - Updated metrics and charts
- `/requirements.txt` - Added websockets

## Performance Notes

- Terminal WebSocket connections use minimal bandwidth (text streaming only)
- Charts use hardware-accelerated CSS animations
- Metrics auto-update uses efficient fetch API
- Scanline effect uses CSS animation (GPU-accelerated)

## Browser Compatibility

- ✅ Chrome/Edge (recommended)
- ✅ Firefox
- ✅ Safari (WebKit)
- ⚠️ IE11 (not supported - WebSocket required)

## Future Enhancements (Optional)

- [ ] Sound effects for terminal events
- [ ] Terminal command input (interactive shell)
- [ ] Export terminal logs to file
- [ ] Multiple terminal tabs
- [ ] Terminal themes selector
- [ ] Keyboard shortcuts (Ctrl+T for terminal)
- [ ] Real-time attack statistics
- [ ] 3D data visualization with Three.js

---

**Status:** ✅ All enhancements complete and tested
**App URL:** http://localhost:5172
**Container:** `redteam-app` (running on port 5172)
[0m