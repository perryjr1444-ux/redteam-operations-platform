# Chain Execution Monitor - Usage Guide

## Overview

Real-time WebSocket-based monitoring for attack chain executions with live progress updates, step-by-step execution logs, and error highlighting.

## Features

- **Live Progress Bar** - Visual progress indicator showing completion percentage
- **Step-by-Step Execution Log** - Detailed view of each step with status, duration, and output
- **Real-time Status Updates** - Automatic status transitions (pending → running → completed/failed)
- **Error Highlighting** - Failed steps are clearly marked with error messages
- **Auto-reconnect** - Automatic reconnection on connection loss
- **Alpine.js Integration** - Reactive UI with minimal JavaScript

## Files Created

### 1. `/app/static/js/chain-monitor.js` (473 lines)
Alpine.js component for real-time WebSocket monitoring.

**Key Functions:**
- `chainMonitor(executionId)` - Main Alpine.js component
- WebSocket connection management with auto-reconnect
- Message handlers for execution updates, step events, and errors
- Progress calculation and UI state management

### 2. `/app/websocket_chain_monitor.py` (303 lines)
WebSocket chain execution monitor service.

**Key Classes:**
- `ChainExecutionMonitor` - Manages WebSocket connections and broadcasts

**Key Methods:**
- `connect()` / `disconnect()` - WebSocket lifecycle management
- `broadcast()` - Send messages to all connected clients
- `send_step_start()` - Notify step start
- `send_step_complete()` - Notify step completion
- `send_step_failed()` - Notify step failure
- `send_execution_complete()` - Notify execution completion
- `monitor_execution()` - Poll execution status and emit updates

### 3. `/app/chain_executor_ws.py` (389 lines)
Chain executor with WebSocket integration (optional standalone executor).

**Key Classes:**
- `ChainExecutorWithWebSocket` - Execute chains with real-time updates

### 4. `/app/main.py` (Modified - now 1097 lines)
Added WebSocket endpoint for chain execution monitoring.

**Additions:**
- Import `chain_monitor` from `websocket_chain_monitor`
- `@app.websocket("/ws/chain-execution/{execution_id}")` endpoint
- JSON import for message parsing

### 5. `/app/routes/api_enhanced.py` (Modified - now 1392 lines)
Integrated WebSocket notifications into chain execution.

**Additions:**
- Import `chain_monitor`
- Updated `execute_chain_background()` to emit WebSocket events:
  - Execution updates
  - Step start/complete/failed notifications
  - Completion/failure notifications

## Usage

### HTML Template Example

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Chain Execution Monitor</title>
    <script defer src="https://cdn.jsdelivr.net/npm/alpinejs@3.x.x/dist/cdn.min.js"></script>
    <script src="/static/js/chain-monitor.js"></script>
    <style>
        .status-badge {
            padding: 4px 12px;
            border-radius: 4px;
            font-size: 12px;
            font-weight: 600;
        }
        .progress-bar {
            height: 8px;
            background: #e5e7eb;
            border-radius: 4px;
            overflow: hidden;
        }
        .progress-fill {
            height: 100%;
            transition: width 0.3s ease;
        }
        .step-log {
            max-height: 400px;
            overflow-y: auto;
            font-family: monospace;
            font-size: 13px;
        }
    </style>
</head>
<body>
    <div x-data="chainMonitor('exec_abc123')" class="p-4">
        <!-- Connection Status -->
        <div class="mb-4">
            <span x-show="connected" class="text-green-600">● Connected</span>
            <span x-show="!connected && !reconnecting" class="text-red-600">● Disconnected</span>
            <span x-show="reconnecting" class="text-yellow-600">● Reconnecting...</span>
        </div>

        <!-- Execution Header -->
        <div class="mb-4">
            <h2 class="text-2xl font-bold" x-text="chainName || 'Loading...'"></h2>
            <p class="text-gray-600" x-text="'Execution ID: ' + executionId"></p>
        </div>

        <!-- Status Badge -->
        <div class="mb-4">
            <span class="status-badge" :class="getStatusClass(status)" x-text="status.toUpperCase()"></span>
        </div>

        <!-- Progress Bar -->
        <div class="mb-4">
            <div class="flex justify-between mb-2">
                <span class="text-sm font-medium">Progress</span>
                <span class="text-sm" x-text="progress + '%'"></span>
            </div>
            <div class="progress-bar">
                <div class="progress-fill" :class="getProgressBarClass()" :style="'width: ' + progress + '%'"></div>
            </div>
        </div>

        <!-- Stats -->
        <div class="grid grid-cols-4 gap-4 mb-4">
            <div>
                <div class="text-sm text-gray-600">Total Steps</div>
                <div class="text-2xl font-bold" x-text="totalSteps"></div>
            </div>
            <div>
                <div class="text-sm text-gray-600">Completed</div>
                <div class="text-2xl font-bold text-green-600" x-text="completedSteps"></div>
            </div>
            <div>
                <div class="text-sm text-gray-600">Failed</div>
                <div class="text-2xl font-bold text-red-600" x-text="failedSteps"></div>
            </div>
            <div>
                <div class="text-sm text-gray-600">Duration</div>
                <div class="text-2xl font-bold" x-text="formatDuration(duration)"></div>
            </div>
        </div>

        <!-- Error Message -->
        <div x-show="errorMessage" class="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
            <strong>Error:</strong> <span x-text="errorMessage"></span>
        </div>

        <!-- Step Filters -->
        <div class="mb-4 flex gap-2">
            <button @click="setFilter('all')" class="px-3 py-1 rounded" :class="filter === 'all' ? 'bg-blue-600 text-white' : 'bg-gray-200'">All</button>
            <button @click="setFilter('completed')" class="px-3 py-1 rounded" :class="filter === 'completed' ? 'bg-green-600 text-white' : 'bg-gray-200'">Completed</button>
            <button @click="setFilter('failed')" class="px-3 py-1 rounded" :class="filter === 'failed' ? 'bg-red-600 text-white' : 'bg-gray-200'">Failed</button>
            <button @click="setFilter('running')" class="px-3 py-1 rounded" :class="filter === 'running' ? 'bg-blue-600 text-white' : 'bg-gray-200'">Running</button>
        </div>

        <!-- Step Log -->
        <div class="step-log border rounded p-4" x-ref="logContainer">
            <template x-for="step in filteredSteps" :key="step.index">
                <div class="mb-4 pb-4 border-b last:border-b-0">
                    <div class="flex justify-between items-center mb-2">
                        <div>
                            <span class="font-bold" x-text="'Step ' + (step.index + 1) + ': ' + step.name"></span>
                            <span class="text-gray-600 text-sm ml-2" x-text="'(' + step.tool + ')'"></span>
                        </div>
                        <div class="flex items-center gap-2">
                            <span class="status-badge text-xs" :class="getStatusClass(step.status)" x-text="step.status"></span>
                            <span class="text-sm text-gray-600" x-text="formatDuration(step.duration)"></span>
                        </div>
                    </div>

                    <!-- Step Output -->
                    <div x-show="step.output && step.output.length > 0" class="bg-gray-100 p-2 rounded text-xs">
                        <template x-for="line in step.output" :key="line">
                            <div x-text="line"></div>
                        </template>
                    </div>

                    <!-- Step Error -->
                    <div x-show="step.error" class="bg-red-100 text-red-700 p-2 rounded text-xs mt-2">
                        <strong>Error:</strong> <span x-text="step.error"></span>
                    </div>
                </div>
            </template>

            <!-- Empty State -->
            <div x-show="steps.length === 0" class="text-center text-gray-500">
                Waiting for execution to start...
            </div>
        </div>

        <!-- Controls -->
        <div class="mt-4 flex gap-2">
            <button @click="toggleAutoScroll()" class="px-4 py-2 rounded" :class="autoScroll ? 'bg-blue-600 text-white' : 'bg-gray-200'">
                Auto-scroll: <span x-text="autoScroll ? 'ON' : 'OFF'"></span>
            </button>
            <button @click="connect()" x-show="!connected" class="px-4 py-2 bg-green-600 text-white rounded">
                Reconnect
            </button>
        </div>
    </div>
</body>
</html>
```

### JavaScript Integration

```javascript
// Initialize chain monitor for a specific execution
function initChainMonitor(executionId) {
    return {
        ...chainMonitor(executionId),

        // Add custom event handlers
        init() {
            this.connect();

            // Listen for execution complete
            this.$watch('status', (status) => {
                if (status === 'completed') {
                    console.log('Execution completed!');
                    // Trigger custom action
                }
            });
        }
    };
}
```

### API Usage

#### Start Chain Execution

```bash
# Execute a chain and get execution_id
curl -X POST http://localhost:8000/api/chains/chain_abc123/execute \
  -H "Content-Type: application/json" \
  -d '{"context": {"target": "192.168.1.100"}}'

# Response:
{
  "execution_id": "exec_xyz789",
  "chain_id": "chain_abc123",
  "status": "pending",
  ...
}
```

#### Connect to WebSocket

```javascript
// Connect to monitor execution
const ws = new WebSocket('ws://localhost:8000/ws/chain-execution/exec_xyz789');

ws.onmessage = (event) => {
    const message = JSON.parse(event.data);
    console.log('Received:', message);
};
```

## WebSocket Message Types

### 1. Execution Update
```json
{
  "type": "execution_update",
  "data": {
    "execution_id": "exec_xyz789",
    "status": "running",
    "total_steps": 5,
    "completed_steps": 2,
    "failed_steps": 0
  }
}
```

### 2. Step Start
```json
{
  "type": "step_start",
  "data": {
    "step_index": 0,
    "step_name": "Port Scan",
    "tool": "nmap",
    "start_time": "2025-10-22T12:00:00Z"
  }
}
```

### 3. Step Complete
```json
{
  "type": "step_complete",
  "data": {
    "step_index": 0,
    "end_time": "2025-10-22T12:01:00Z",
    "duration": 60.5,
    "output": ["Nmap scan completed", "Found 5 open ports"]
  }
}
```

### 4. Step Failed
```json
{
  "type": "step_failed",
  "data": {
    "step_index": 1,
    "end_time": "2025-10-22T12:02:00Z",
    "duration": 30.2,
    "error": "Connection timeout",
    "output": ["Attempting connection...", "Timeout after 30s"]
  }
}
```

### 5. Execution Complete
```json
{
  "type": "execution_complete",
  "data": {
    "end_time": "2025-10-22T12:05:00Z",
    "duration": 300.5
  }
}
```

### 6. Execution Failed
```json
{
  "type": "execution_failed",
  "data": {
    "end_time": "2025-10-22T12:03:00Z",
    "duration": 180.0,
    "error": "Critical step failed"
  }
}
```

## Configuration

### WebSocket Polling Interval

Edit `/app/websocket_chain_monitor.py`:

```python
# Poll every 2 seconds (default)
await asyncio.sleep(2)

# Change to 1 second for faster updates
await asyncio.sleep(1)
```

### Auto-reconnect Settings

Edit `/app/static/js/chain-monitor.js`:

```javascript
// Default settings
maxReconnectAttempts: 5,
reconnectDelay: 2000, // 2 seconds

// Increase max attempts
maxReconnectAttempts: 10,
reconnectDelay: 3000, // 3 seconds
```

## Testing

### Manual Test

1. Start the application:
```bash
cd /opt/projects/redteam_py_app
python -m uvicorn app.main:app --reload
```

2. Create a test chain execution:
```bash
curl -X POST http://localhost:8000/api/chains/test_chain/execute \
  -H "Content-Type: application/json" \
  -d '{}'
```

3. Open browser and connect to WebSocket:
```javascript
const ws = new WebSocket('ws://localhost:8000/ws/chain-execution/exec_abc123');
ws.onmessage = (e) => console.log(JSON.parse(e.data));
```

## Architecture

```
┌─────────────────┐
│  Frontend UI    │
│  (Alpine.js)    │
└────────┬────────┘
         │ WebSocket
         ↓
┌─────────────────┐
│  WebSocket      │
│  Endpoint       │
│  /ws/chain-     │
│  execution/{id} │
└────────┬────────┘
         │
         ↓
┌─────────────────┐      ┌──────────────┐
│ ChainExecution  │─────→│  Database    │
│ Monitor         │      │  (SQLite)    │
└────────┬────────┘      └──────────────┘
         │
         ↓
┌─────────────────┐
│ Chain Executor  │
│ (Background     │
│  Task)          │
└─────────────────┘
```

## Summary

- **3 new files created** (1165 lines total)
- **2 files modified** (main.py, api_enhanced.py)
- **WebSocket endpoint** at `/ws/chain-execution/{execution_id}`
- **Real-time updates** for execution progress
- **Alpine.js component** for reactive UI
- **Auto-reconnect** and error handling
- **Step-by-step monitoring** with output and error display
