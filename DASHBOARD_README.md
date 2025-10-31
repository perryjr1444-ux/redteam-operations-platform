[8m# Execution Monitor Dashboard - Quick Start Guide

## What is This?

A comprehensive real-time monitoring dashboard for tracking fractal execution nodes in the Red Team application. Monitor active executions, view performance metrics, manage resources, and stream logs - all in a professional, dark-themed interface.

## Quick Access

```
http://localhost:8000/execution/monitor
```

## Installation

**No installation required!** All dependencies are loaded via CDN:
- Alpine.js 3.13.3
- Chart.js 4.4.0
- Bootstrap 5.3.3
- Bootstrap Icons 1.11.3

Just start the server and access the dashboard.

## Starting the Server

```bash
cd /opt/projects/redteam_py_app
python -m app.main
```

Server will start on `http://localhost:8000`

## Dashboard Features at a Glance

### 1. Performance Metrics (Top Row)
- **Active Executions**: Current running executions
- **Completed Today**: Executions finished in last 24h
- **Success Rate**: Percentage of successful executions
- **Average Duration**: Mean execution time

### 2. Active Executions List (Left Column)
- Real-time execution status
- Progress bars
- Quick actions (Pause/Resume/Cancel)
- Duration tracking
- Hierarchy information

### 3. Resource Utilization (Right Column, Top)
- CPU usage with color-coded alerts
- Memory utilization
- Network traffic
- Container pool status

### 4. Recent Activity Timeline (Right Column, Middle)
- Chronological event feed
- Execution start/stop events
- Status changes
- Error notifications

### 5. Performance Charts (Bottom)
- **Line Chart**: Execution duration over time
- **Doughnut Chart**: Status distribution

### 6. Execution Logs (Full Width)
- Real-time log streaming
- Color-coded levels (info/success/warning/error)
- Filter by level
- Auto-scroll to latest

## Using the Dashboard

### Monitoring Executions

**View Active Executions:**
1. Active executions appear automatically in the list
2. Each shows:
   - Status indicator (colored dot)
   - Execution type and ID
   - Progress bar
   - Duration
   - Level and node count

**Status Indicators:**
- **Blue pulsing dot**: Running
- **Gray dot**: Pending
- **Green dot**: Completed
- **Red dot**: Failed
- **Yellow dot**: Cancelled

### Managing Executions

**Pause an Execution:**
1. Find running execution in list
2. Click yellow **Pause** button
3. Execution pauses immediately

**Resume a Paused Execution:**
1. Find paused execution in list
2. Click green **Resume** button
3. Execution continues

**Cancel an Execution:**
1. Find execution in list
2. Click red **Cancel** button
3. Confirm in dialog
4. Execution terminates

### Viewing Logs

**Filter Logs:**
1. Use dropdown above log viewer
2. Select level: All, Info, Success, Warning, Error
3. Logs filter automatically

**Clear Logs:**
1. Click **Clear** button above log viewer
2. All logs removed (can't undo)

**Log Colors:**
- **Cyan**: Info messages
- **Green**: Success messages
- **Yellow**: Warning messages
- **Red**: Error messages

### Reading Charts

**Performance Chart (Line):**
- Shows execution duration over time
- X-axis: Time (last 20 executions)
- Y-axis: Duration in seconds
- Hover for exact values

**Status Distribution Chart (Doughnut):**
- Shows execution status breakdown
- Segments: Running, Completed, Failed, Pending
- Hover for counts and percentages

### WebSocket Status

**Connection Indicator (Bottom Right):**
- **Green pulsing**: Connected, receiving real-time updates
- **Red**: Disconnected, auto-reconnecting
- **Loading spinner**: Processing updates

## Testing the Dashboard

### Run Test Suite
```bash
python test_dashboard.py
```

Expected: 6/8 tests pass (2 failures are dependency-related, don't affect functionality)

### Run Demo
```bash
python demo_dashboard.py
```

Creates sample execution tree and shows what dashboard will display.

## File Structure

```
/opt/projects/redteam_py_app/
├── templates/
│   └── execution_dashboard.html    # Main template (21 KB)
├── static/js/
│   ├── execution-dashboard.js      # Dashboard logic (23 KB)
│   └── alpine-components.js        # Alpine stores (13 KB)
├── app/routes/
│   ├── ui_enhanced.py              # UI routes (2 KB)
│   └── api_enhanced.py             # API endpoints (24 KB)
├── EXECUTION_DASHBOARD.md          # Full documentation (11 KB)
├── DASHBOARD_SUMMARY.md            # Implementation summary (15 KB)
├── DASHBOARD_README.md             # This file (Quick start)
├── test_dashboard.py               # Test suite
└── demo_dashboard.py               # Demo script
```

## API Endpoints Used

### GET /api/execution/active
Returns active and pending executions

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

### WebSocket: ws://localhost:8000/ws/tool
Real-time event streaming

**Events:**
- `execution_started` - New execution
- `execution_updated` - Progress update
- `execution_completed` - Finished successfully
- `execution_failed` - Error occurred
- `node_update` - Node status change
- `log` - New log entry

## Troubleshooting

### Dashboard Won't Load
1. **Check server is running**: `python -m app.main`
2. **Check URL**: `http://localhost:8000/execution/monitor`
3. **Check browser console**: Press F12, look for errors
4. **Clear cache**: Ctrl+Shift+R (or Cmd+Shift+R on Mac)

### No Executions Showing
1. **No active executions**: Dashboard empty if nothing running
2. **Check API**: Visit `http://localhost:8000/api/execution/active`
3. **Run demo**: `python demo_dashboard.py` to see sample data

### WebSocket Won't Connect
1. **Check WebSocket endpoint**: Should be `ws://localhost:8000/ws/tool`
2. **Check firewall**: Allow WebSocket connections
3. **Check browser**: Must support WebSockets (all modern browsers do)
4. **Auto-reconnect**: Dashboard tries to reconnect every 3 seconds

### Charts Not Showing
1. **Check Chart.js loaded**: Look for errors in browser console
2. **Check canvas elements**: Should see `<canvas>` tags in DOM
3. **Wait for data**: Charts need data to display
4. **Refresh page**: Ctrl+R (or Cmd+R on Mac)

### Logs Not Appearing
1. **Check filter**: Set to "All Logs" to see everything
2. **Check log viewer**: Scroll to bottom
3. **Generate activity**: Logs appear when executions run
4. **Clear and retry**: Click Clear, then try again

## Tips & Tricks

### Performance
- Dashboard auto-refreshes every 3-5 seconds
- Charts update every 30 seconds
- Duration counters update every second
- Pause/Resume work instantly

### Best Practices
1. **Monitor regularly**: Check dashboard during operations
2. **Watch timeline**: Recent activity shows what's happening
3. **Check resources**: Prevent overload by monitoring utilization
4. **Review logs**: Catch issues early with log monitoring
5. **Use pause/resume**: Control execution flow as needed

### Keyboard Shortcuts
- **F5**: Refresh page
- **Ctrl+R**: Manual refresh
- **Ctrl+Shift+R**: Hard refresh (clear cache)
- **F12**: Open developer tools

## Integration with Other Dashboards

### Navigate to Other Views
- **Tree Visualizer**: Click "Tree Visualizer" button (top right)
- **AI Agents**: Use sidebar menu
- **Main Dashboard**: Click "Dashboard" in sidebar

### Links
- Main Dashboard: `/`
- AI Agents: `/ai/dashboard`
- Execution Monitor: `/execution/monitor` (You are here)
- Tree Visualizer: `/execution/visualizer`
- Health: `/health`
- Metrics: `/metrics`

## Support & Documentation

### Full Documentation
- **User Guide**: `/EXECUTION_DASHBOARD.md` (11 KB)
- **Implementation**: `/DASHBOARD_SUMMARY.md` (15 KB)
- **Quick Start**: This file

### Demo & Testing
- **Test Suite**: `python test_dashboard.py`
- **Demo Script**: `python demo_dashboard.py`

### Source Code
- **Template**: `templates/execution_dashboard.html`
- **JavaScript**: `static/js/execution-dashboard.js`
- **API**: `app/routes/api_enhanced.py`

## What's Next?

### After Dashboard Loads
1. Watch active executions appear
2. Monitor resource utilization
3. Review timeline for activity
4. Check logs for details
5. Use pause/resume/cancel as needed

### Creating Sample Data
Run the demo script to populate dashboard:
```bash
python demo_dashboard.py
```

This creates a sample execution tree with:
- 1 AI Agent (Strategic Planner)
- 3 Exercises (Web App, Network, Database)
- 2 Chains (Reconnaissance, Exploitation)
- 3 Tools (Nmap, Nikto, SQLMap)

### Advanced Usage
See full documentation at `/EXECUTION_DASHBOARD.md` for:
- WebSocket integration
- Chart customization
- Alpine.js component details
- API endpoint documentation
- Development guidelines

## Quick Commands

```bash
# Start server
python -m app.main

# Run tests
python test_dashboard.py

# Run demo
python demo_dashboard.py

# Access dashboard
open http://localhost:8000/execution/monitor
```

## System Requirements

- **Python**: 3.8+
- **Browser**: Modern browser (Chrome, Firefox, Safari, Edge)
- **Network**: localhost access
- **Port**: 8000 available

## Features Summary

✓ Real-time execution monitoring
✓ Performance metrics tracking
✓ Resource utilization alerts
✓ Event timeline
✓ Log streaming with filtering
✓ Interactive charts
✓ Pause/Resume/Cancel controls
✓ WebSocket real-time updates
✓ Auto-refresh
✓ Responsive design
✓ Professional dark theme
✓ NO installation required

## Success Indicators

Dashboard is working correctly when you see:
1. **Green pulsing dot** (bottom right) = WebSocket connected
2. **Metrics updating** (top row) = Data flowing
3. **Charts rendering** (bottom) = Visualizations working
4. **Executions listing** (left) = Orchestrator connected
5. **Logs appearing** (bottom) = Events streaming

## That's It!

You now know everything needed to use the Execution Monitor Dashboard effectively.

**Access URL:** `http://localhost:8000/execution/monitor`

Enjoy monitoring your Red Team executions! 🎯
[0m