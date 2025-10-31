[8m# Execution Monitor Dashboard

## Overview

A comprehensive real-time monitoring dashboard for the Red Team application's fractal execution orchestrator. The dashboard provides visibility into active executions, performance metrics, resource utilization, and execution logs.

## Location

- **URL**: `http://localhost:8000/execution/monitor`
- **Template**: `/templates/execution_dashboard.html`
- **JavaScript**: `/static/js/execution-dashboard.js`
- **API Endpoints**: `/app/routes/api_enhanced.py`

## Features

### 1. Active Executions List
- Real-time list of all running executions
- Status indicators (Running, Completed, Failed, Pending, Cancelled)
- Progress tracking with visual progress bars
- Duration tracking for each execution
- Execution hierarchy information (level, node count)
- Quick action buttons (Pause/Resume/Cancel)

### 2. Performance Metrics
Four key metrics displayed at the top:
- **Active Executions**: Current number of running executions
- **Completed Today**: Number of executions completed in the last 24 hours
- **Success Rate**: Percentage of successful executions
- **Average Duration**: Mean execution time

### 3. Resource Utilization
Real-time monitoring of:
- CPU usage (%)
- Memory usage (%)
- Network utilization (%)
- Container pool utilization

Visual progress bars with color-coded alerts:
- Green: Low utilization (< 50%)
- Yellow: Medium utilization (50-80%)
- Red: High utilization (> 80%)

### 4. Execution Timeline
Chronological activity feed showing:
- Execution start/stop events
- Status changes
- System notifications
- Error events
- User actions

Each event includes:
- Timestamp
- Event type
- Status indicator
- Descriptive message

### 5. Performance Charts

#### Execution Performance Chart
- Line chart showing execution duration over time
- Last 20 execution data points
- Real-time updates as executions complete
- Smooth animations and transitions

#### Status Distribution Chart
- Doughnut chart showing distribution of execution statuses
- Running, Completed, Failed, and Pending counts
- Percentage calculations
- Interactive tooltips

### 6. Execution Logs Viewer
- Real-time log streaming
- Color-coded log levels:
  - **Info**: Cyan (#0dcaf0)
  - **Success**: Green (#00ff88)
  - **Warning**: Yellow (#ffc107)
  - **Error**: Red (#dc3545)
- Log filtering by level
- Timestamps for all entries
- Auto-scroll to latest logs
- Clear logs functionality

### 7. Quick Actions

Each execution supports:
- **Pause**: Temporarily halt execution (displayed when running)
- **Resume**: Continue paused execution (displayed when paused)
- **Cancel**: Terminate execution with confirmation
- **Details**: View detailed execution information

### 8. Real-Time Updates

#### WebSocket Connection
- Automatic connection to WebSocket endpoint
- Reconnection on disconnect (3-second delay)
- Connection status indicator
- Real-time event streaming

#### Event Types
- `execution_started`: New execution began
- `execution_updated`: Progress or status change
- `execution_completed`: Execution finished successfully
- `execution_failed`: Execution encountered error
- `node_update`: Individual node status change
- `log`: New log entry

### 9. Auto-Refresh
- Active executions: Every 5 seconds
- Resource metrics: Every 5 seconds
- Execution durations: Every 1 second
- Performance charts: Every 30 seconds

## Architecture

### Frontend Stack
- **Alpine.js**: Reactive state management
- **Chart.js**: Performance visualizations
- **Bootstrap 5**: UI components and layout
- **WebSocket**: Real-time communication
- **Custom CSS**: Dark theme with cyberpunk aesthetics

### Backend Stack
- **FastAPI**: REST API endpoints
- **WebSocket**: Real-time event streaming
- **FractalOrchestrator**: Execution tracking
- **AgentManager**: AI agent coordination
- **ContainerPool**: Resource management

### Data Flow
```
FractalOrchestrator
        ↓
  API Endpoints (/api/execution/*)
        ↓
  Alpine Store ($store.execution)
        ↓
  Dashboard Component (executionDashboard())
        ↓
  UI Updates (Reactive)
```

### WebSocket Flow
```
Execution Event
        ↓
  WebSocket Manager
        ↓
  Client WebSocket
        ↓
  handleWebSocketMessage()
        ↓
  State Updates
        ↓
  UI Re-render
```

## API Endpoints

### GET /api/execution/active
Returns active executions

**Response:**
```json
{
  "executions": [
    {
      "id": "execution_123",
      "type": "exercise",
      "status": "running",
      "progress": 50,
      "duration": 120,
      "level": "exercise",
      "nodeCount": 5
    }
  ],
  "completed_today": 15,
  "avg_duration": 145.5
}
```

### GET /api/execution/tree/{root_id}
Returns execution tree structure

**Response:**
```json
{
  "id": "root_node",
  "type": "agent",
  "status": "running",
  "level": "meta",
  "children": [...]
}
```

### GET /api/metrics/live
Returns live system metrics

**Response:**
```json
{
  "active_exercises": 3,
  "system_health": 95,
  "running_containers": 12,
  "uptime": "5d",
  "timestamp": "2025-10-22T10:30:00Z"
}
```

## Alpine.js Component

### Main Component: executionDashboard()

**State Properties:**
- `activeExecutions`: Array of active execution objects
- `selectedExecution`: Currently selected execution for details
- `timeline`: Array of timeline events
- `logs`: Array of log entries
- `logFilter`: Current log filter ('all', 'info', 'success', 'warning', 'error')
- `isLoading`: Loading state indicator
- `wsConnected`: WebSocket connection status
- `metrics`: Object containing performance metrics
- `resources`: Object containing resource utilization data

**Methods:**
- `init()`: Initialize component, fetch data, connect WebSocket
- `fetchActiveExecutions()`: Retrieve active executions from API
- `fetchMetrics()`: Retrieve performance metrics
- `fetchResources()`: Retrieve resource utilization
- `connectWebSocket()`: Establish WebSocket connection
- `handleWebSocketMessage(message)`: Process incoming WebSocket events
- `pauseExecution(id)`: Pause an execution
- `resumeExecution(id)`: Resume a paused execution
- `cancelExecution(id)`: Cancel an execution
- `addLog(level, message)`: Add entry to logs
- `formatDuration(seconds)`: Format duration for display
- `formatTime(timestamp)`: Format timestamp for display

## Styling

### Theme
- **Dark Mode**: Primary background (#0a0e1a)
- **Accent Colors**:
  - Success: #00ff88 (green)
  - Info: #0dcaf0 (cyan)
  - Warning: #ffc107 (yellow)
  - Danger: #dc3545 (red)
- **Font**: JetBrains Mono for code/metrics

### Animations
- Pulse animation for running status
- Smooth transitions on hover
- Slide-in animations for cards
- Loading spinners
- Chart animations

### Responsive Design
- Grid-based layout (12 columns)
- Breakpoints at 768px
- Mobile-optimized views
- Scrollable containers

## Usage

### Basic Usage
1. Navigate to `http://localhost:8000/execution/monitor`
2. Dashboard loads automatically with current data
3. Active executions appear in the list
4. Metrics and charts update in real-time

### Monitoring Executions
1. View execution list for current status
2. Check progress bars for completion percentage
3. Review timeline for recent events
4. Monitor resource utilization

### Managing Executions
1. Click **Pause** to temporarily halt an execution
2. Click **Resume** to continue a paused execution
3. Click **Cancel** to terminate an execution (requires confirmation)
4. Click **Details** icon to view execution information

### Viewing Logs
1. Logs appear automatically at bottom of dashboard
2. Use filter dropdown to show specific log levels
3. Click **Clear** to remove all logs
4. Logs auto-scroll to show latest entries

### Performance Analysis
1. Review performance chart for execution duration trends
2. Check status distribution chart for success/failure ratios
3. Monitor resource utilization for bottlenecks
4. Use timeline to identify patterns

### Navigation
- Click **Refresh** to manually update all data
- Click **Tree Visualizer** to view detailed execution tree
- Use sidebar navigation to access other dashboards

## Integration

### With Fractal Orchestrator
```python
from app.fractal_orchestrator import FractalOrchestrator, ExecutionNode

# Create orchestrator
orchestrator = FractalOrchestrator()

# Register node
node = ExecutionNode(
    id="exec_001",
    level=ExecutionLevel.EXERCISE,
    type="exercise",
    name="Web App Penetration Test"
)
orchestrator.register_node(node)

# Execute with callbacks
async def on_node_complete(node):
    # Notify WebSocket clients
    await notify_execution_update(node)

await orchestrator.execute_node("exec_001", executor_func, on_node_complete)
```

### With WebSocket Manager
```python
from app.websocket import manager

# Send execution update
await manager.broadcast({
    "type": "execution_started",
    "data": {
        "id": "exec_001",
        "type": "exercise",
        "status": "running"
    }
})
```

## Development

### Adding New Features
1. Update `execution-dashboard.js` component
2. Add corresponding API endpoint in `api_enhanced.py`
3. Update template HTML in `execution_dashboard.html`
4. Test WebSocket event handling

### Debugging
1. Open browser console for JavaScript errors
2. Check WebSocket connection status indicator
3. Review FastAPI logs for backend errors
4. Use Alpine DevTools for state inspection

### Performance Optimization
- Limit active execution list to 50 items
- Throttle chart updates to 30 seconds
- Batch WebSocket messages
- Use virtual scrolling for large log lists

## Security Considerations

### Access Control
- Dashboard requires authentication (configured in routes)
- WebSocket connections validated
- API endpoints protected by auth middleware

### Data Validation
- Input sanitization for execution IDs
- CSRF protection on actions
- Rate limiting on API endpoints

### Monitoring
- Log all execution actions
- Audit trail for pause/resume/cancel
- Alert on suspicious activity

## Troubleshooting

### Dashboard Not Loading
1. Verify server is running on port 8000
2. Check browser console for errors
3. Ensure Alpine.js and Chart.js CDNs are accessible
4. Verify template path is correct

### No Executions Showing
1. Check if orchestrator has active nodes
2. Verify API endpoint returns data
3. Check WebSocket connection status
4. Review browser network tab for failed requests

### WebSocket Not Connecting
1. Verify WebSocket endpoint is accessible
2. Check firewall/proxy settings
3. Review server logs for WebSocket errors
4. Ensure browser supports WebSockets

### Charts Not Updating
1. Verify Chart.js is loaded
2. Check canvas elements exist in DOM
3. Review console for Chart.js errors
4. Ensure data format matches chart expectations

## Future Enhancements

### Planned Features
- [ ] Export execution data to CSV/JSON
- [ ] Execution replay functionality
- [ ] Custom metric dashboards
- [ ] Advanced filtering and search
- [ ] Execution comparison tool
- [ ] Historical trend analysis
- [ ] Alert configuration
- [ ] Mobile app integration
- [ ] Multi-user collaboration
- [ ] Execution scheduling

### Performance Improvements
- [ ] Virtual scrolling for logs
- [ ] Progressive data loading
- [ ] Service Worker for offline capability
- [ ] IndexedDB for local caching
- [ ] WebWorkers for heavy computations

## Support

For issues or questions:
1. Check this documentation
2. Review example executions
3. Check server logs
4. Open GitHub issue

## License

Part of the Red Team C2 application.
[0m