[8m# UI Framework Integration Guide

**Version**: 1.0.0
**Last Updated**: 2025-10-21
**Phase**: 5.1 - UI Framework Upgrade

---

## Overview

This guide documents the Alpine.js + enhanced Chart.js integration for the Red Team C2 platform.

### Components Added

1. **Alpine.js Reactive Components** (`static/js/alpine-components.js`)
2. **Enhanced Chart.js Visualizations** (`static/js/charts-enhanced.js`)
3. **Enhanced Base Template** (`templates/base_enhanced.html`)
4. **Reactive Dashboard** (`templates/dashboard_enhanced.html`)
5. **API Endpoints** (`app/routes/api_enhanced.py`)
6. **Unit Tests** (`tests/test_ui_components.py`)

**Total Lines**: ~2,050 lines of production code

---

## Architecture

### Data Flow

```
┌─────────────────────────────────────────────────────────────┐
│                    FastAPI Backend                           │
│  ┌────────────────────────────────────────────────────┐     │
│  │  Enhanced API Routes (/api/...)                    │     │
│  │  - /metrics/live                                   │     │
│  │  - /ai/agents/status                               │     │
│  │  - /execution/active                               │     │
│  │  - /tools, /chains                                 │     │
│  └────────────────────────────────────────────────────┘     │
└─────────────────────┬───────────────────────────────────────┘
                      │ JSON over HTTP
                      │ (Auto-refresh: 3-10s)
                      ↓
┌─────────────────────────────────────────────────────────────┐
│                  Alpine.js Stores (Client)                   │
│  ┌──────────────┬─────────────┬───────────────┬──────────┐  │
│  │ metrics      │ agents      │ execution     │ notif.   │  │
│  │ (5s refresh) │(10s refresh)│ (3s refresh)  │(manual)  │  │
│  └──────────────┴─────────────┴───────────────┴──────────┘  │
└─────────────────────┬───────────────────────────────────────┘
                      │ Reactive data binding
                      │ (x-data, x-text, x-bind)
                      ↓
┌─────────────────────────────────────────────────────────────┐
│                    UI Components                             │
│  ┌────────────┬──────────────┬──────────────┬───────────┐   │
│  │ Metric     │ Agent Status │ Execution    │ Charts    │   │
│  │ Cards      │ Cards        │ Tree         │           │   │
│  └────────────┴──────────────┴──────────────┴───────────┘   │
└─────────────────────────────────────────────────────────────┘
```

---

## Alpine.js Integration

### Global Stores

Four reactive stores provide centralized state management:

#### 1. Metrics Store (`$store.metrics`)

**Purpose**: System-wide metrics
**Refresh Rate**: 5 seconds

**Properties**:
```javascript
{
  activeExercises: int,      // Number of running exercises
  systemHealth: int (0-100), // Overall health percentage
  runningContainers: int,    // Active container count
  uptime: string,            // Human-readable uptime (e.g., "7h", "2d")
  lastUpdate: Date           // Last refresh timestamp
}
```

**Usage**:
```html
<div x-data>
  <span x-text="$store.metrics.activeExercises"></span> Active
  <span x-text="$store.metrics.systemHealth"></span>% Health
</div>
```

#### 2. Agents Store (`$store.agents`)

**Purpose**: AI agent health monitoring
**Refresh Rate**: 10 seconds

**Properties**:
```javascript
{
  agents: [{
    type: string,
    is_healthy: bool,
    last_check: string (ISO),
    error_count: int,
    avg_response_time: float (ms),
    uptime_percentage: float (0-100)
  }],
  healthy: int,              // Count of healthy agents
  unhealthy: int,            // Count of unhealthy agents
  avgResponseTime: float     // Average across all agents
}
```

**Usage**:
```html
<div x-data>
  <span x-text="$store.agents.healthy"></span>/<span x-text="$store.agents.healthy + $store.agents.unhealthy"></span> Agents Online
</div>
```

#### 3. Execution Store (`$store.execution`)

**Purpose**: Fractal execution tracking
**Refresh Rate**: 3 seconds

**Properties**:
```javascript
{
  activeExecutions: [{
    id: string,
    type: string,
    status: string,
    progress: int (0-100),
    duration: int (seconds)
  }],
  completedToday: int,
  avgDuration: float
}
```

#### 4. Notifications Store (`$store.notifications`)

**Purpose**: Toast notifications
**Refresh Rate**: Manual

**Methods**:
```javascript
$store.notifications.success("Message")   // Green notification
$store.notifications.error("Message")     // Red notification
$store.notifications.warning("Message")   // Yellow notification
$store.notifications.info("Message")      // Blue notification
$store.notifications.clear()              // Clear all
```

### Components

#### Metric Card

**Purpose**: Animated counter with icon

```html
<div x-data="AlpineComponents.metricCard(0, '%')">
  <div class="metric-value" x-text="formattedValue"></div>
</div>
```

**Features**:
- Smooth counter animation
- Suffix support (%, ms, etc.)
- Auto-updates when value changes

#### Agent Status Card

**Purpose**: Individual agent health display

```html
<div x-data="AlpineComponents.agentStatusCard()" x-init="agent = {...}">
  <i :class="`bi ${statusIcon}`"></i>
  <span x-text="agent.type"></span>
  <span :class="uptimeColor" x-text="agent.uptime_percentage + '%'"></span>
</div>
```

**Features**:
- Color-coded status indicators
- Dynamic icon selection
- Uptime percentage with color thresholds

#### Execution Tree

**Purpose**: Hierarchical execution visualization

```html
<div x-data="AlpineComponents.executionTree()">
  <button @click="toggleNode(nodeId)">Toggle</button>
  <div x-show="isExpanded(nodeId)">
    <!-- Child nodes -->
  </div>
</div>
```

**Features**:
- Collapsible tree structure
- Status icons per node
- Click-to-select functionality

#### Attack Chain Builder

**Purpose**: Drag-and-drop chain construction

```html
<div x-data="AlpineComponents.attackChainBuilder()">
  <div @drop="drop($event)" @dragover="allowDrop($event)">
    Drop tools here
  </div>
</div>
```

**Features**:
- Drag-and-drop tool selection
- Step reordering
- Parallel execution marking
- Dependency configuration

---

## Enhanced Chart.js

### Streaming Chart

**Purpose**: Real-time data streaming

```javascript
const chart = new ChartEnhancements.StreamingChart('canvasId', {
  label: 'CPU Usage',
  maxDataPoints: 50,
  updateInterval: 1000,
  dataFetchUrl: '/api/metrics/cpu'
});

chart.startAutoUpdate();
```

**Features**:
- Fixed-size sliding window
- Auto-fetch from API
- Smooth animations
- Low memory footprint

### Radial Gauge

**Purpose**: Health scores, percentages

```javascript
const gauge = ChartEnhancements.createRadialGaugeChart('canvasId', 85, {
  label: 'Success Rate',
  maxValue: 100
});
```

**Features**:
- Color-coded based on value
- Large center text
- 270° arc (gauge style)

### Multi-Series Comparison

**Purpose**: Compare multiple metrics

```javascript
const chart = ChartEnhancements.createMultiSeriesChart('canvasId', {
  labels: ['Jan', 'Feb', 'Mar'],
  series: [
    { name: 'Success', values: [10, 20, 15] },
    { name: 'Failed', values: [2, 3, 1] }
  ]
}, { type: 'line' });
```

**Features**:
- Multiple datasets
- Auto-color assignment
- Responsive layout

---

## API Endpoints

### GET /api/metrics/live

**Returns**: Real-time system metrics

```json
{
  "active_exercises": 5,
  "system_health": 98,
  "running_containers": 7,
  "uptime": "7h",
  "timestamp": "2025-10-21T12:34:56Z"
}
```

**Usage**: Auto-fetched by `$store.metrics` every 5 seconds

### GET /api/ai/agents/status

**Returns**: AI agent health status

```json
{
  "enabled": true,
  "agents": {
    "attack_planner": {
      "is_healthy": true,
      "last_check": "2025-10-21T12:34:56Z",
      "error_count": 0,
      "avg_response_time": 120.5,
      "uptime_percentage": 99.8
    }
  }
}
```

**Usage**: Auto-fetched by `$store.agents` every 10 seconds

### GET /api/execution/active

**Returns**: Active fractal executions

```json
{
  "executions": [
    {
      "id": "exec_001",
      "type": "chain",
      "status": "running",
      "progress": 45,
      "duration": 120
    }
  ],
  "completed_today": 12,
  "avg_duration": 245.5
}
```

### GET /api/execution/tree/{id}

**Returns**: Hierarchical execution tree

```json
{
  "id": "root_001",
  "type": "chain",
  "status": "running",
  "level": "chain",
  "children": [...]
}
```

### GET /api/tools

**Returns**: Available tools registry

```json
{
  "tools": [
    {
      "name": "nmap",
      "category": "information_gathering",
      "description": "Network port scanner",
      "requires_root": false,
      "timeout": 300
    }
  ]
}
```

### POST /api/chains

**Creates**: New attack chain

**Request**:
```json
{
  "name": "Custom SQL Injection Chain",
  "steps": [
    {
      "id": "step_1",
      "tool": "nmap",
      "args": {"-p": "80,443"},
      "parallel": false,
      "dependencies": []
    }
  ]
}
```

**Response**:
```json
{
  "success": true,
  "chain_id": "chain_20251021123456",
  "message": "Attack chain 'Custom SQL Injection Chain' created successfully"
}
```

---

## Usage Examples

### Example 1: Real-time Metrics Dashboard

```html
{% extends "base_enhanced.html" %}

{% block content %}
<!-- Metrics auto-update every 5 seconds -->
<div class="row" x-data>
  <div class="col-md-3">
    <div class="metric-card">
      <h3 x-text="$store.metrics.activeExercises"></h3>
      <p>Active Exercises</p>
    </div>
  </div>
  <div class="col-md-3">
    <div class="metric-card">
      <h3 x-text="$store.metrics.systemHealth + '%'"></h3>
      <p>System Health</p>
    </div>
  </div>
</div>
{% endblock %}
```

### Example 2: AI Agent Monitor

```html
<div x-data>
  <h4>AI Agents:
    <span class="text-success" x-text="$store.agents.healthy"></span> /
    <span x-text="$store.agents.healthy + $store.agents.unhealthy"></span>
  </h4>

  <template x-for="agent in $store.agents.agents" :key="agent.type">
    <div class="agent-card">
      <span x-text="agent.type"></span>
      <span :class="agent.is_healthy ? 'text-success' : 'text-danger'"
            x-text="agent.is_healthy ? 'Healthy' : 'Unhealthy'"></span>
      <small x-text="`${Math.round(agent.avg_response_time)}ms response`"></small>
    </div>
  </template>
</div>
```

### Example 3: Notifications

```javascript
// Success notification
Alpine.store('notifications').success('Exercise completed successfully!');

// Error notification (8s duration)
Alpine.store('notifications').error('Failed to connect to container');

// Warning notification (6s duration)
Alpine.store('notifications').warning('High memory usage detected');

// Info notification (5s duration)
Alpine.store('notifications').info('New findings available');
```

### Example 4: Streaming Chart

```html
<div style="height: 300px;">
  <canvas id="cpuChart"></canvas>
</div>

<script>
const chart = new ChartEnhancements.StreamingChart('cpuChart', {
  label: 'CPU Usage %',
  maxDataPoints: 50,
  updateInterval: 2000,
  dataFetchUrl: '/api/metrics/cpu'
});

chart.startAutoUpdate();
</script>
```

---

## Performance Considerations

### Auto-Refresh Rates

- **Metrics Store**: 5 seconds (low frequency, bulk data)
- **Agents Store**: 10 seconds (moderate frequency)
- **Execution Store**: 3 seconds (high frequency, critical data)

### Data Limits

- **Streaming Charts**: Max 50 data points (prevents memory growth)
- **Notifications**: Max 5 visible (auto-cleanup)
- **Execution List**: Limit to active only (completed moved to history)

### Browser Compatibility

- **Alpine.js 3.13+**: Modern browsers (ES6+)
- **Chart.js 4.4+**: All modern browsers
- **No IE11 support**: Uses modern JavaScript features

---

## Testing

### Run Unit Tests

```bash
pytest tests/test_ui_components.py -v --cov=app/routes --cov-report=html
```

### Expected Coverage

- **API Endpoints**: 80%+
- **Component Logic**: 75%+
- **Integration Flow**: 70%+

### E2E Testing (Future)

```bash
# Using Playwright
playwright test tests/e2e/dashboard.spec.js
```

---

## Troubleshooting

### Issue: Metrics not updating

**Solution**: Check browser console for fetch errors. Verify API endpoints are accessible.

```javascript
// Check store status
console.log(Alpine.store('metrics'));
```

### Issue: Charts not rendering

**Solution**: Ensure Chart.js is loaded before alpine-components.js

```html
<script src=".../chart.js"></script>
<script src=".../alpine-components.js"></script>
```

### Issue: Notifications not appearing

**Solution**: Verify `x-cloak` is properly handled in CSS

```css
[x-cloak] { display: none !important; }
```

---

## Best Practices

### 1. Use Stores for Shared State

```javascript
// Good - centralized state
<span x-text="$store.metrics.activeExercises"></span>

// Avoid - component-local state for shared data
<div x-data="{ count: 0 }">
```

### 2. Limit API Calls

```javascript
// Good - use store auto-refresh
$store.metrics.startAutoRefresh(5000);

// Avoid - manual polling in each component
setInterval(() => fetch('/api/metrics/live'), 5000);
```

### 3. Clean Up Resources

```javascript
// Destroy charts when component unmounts
chart.destroy();

// Stop auto-updates when not needed
chart.stopAutoUpdate();
```

---

## FastAPI Integration

### Router Registration

The enhanced API router is registered in `app/main.py`:

```python
# Import enhanced router
from .routes.api_enhanced import router as api_enhanced_router

# Register with app
app.include_router(api_enhanced_router)
```

### Enhanced UI Routes

Enhanced templates are served via `app/routes/ui_enhanced.py`:

```python
@router.get("/enhanced", response_class=HTMLResponse)
async def enhanced_dashboard(request: Request):
    return templates.TemplateResponse(
        "dashboard_enhanced.html",
        {"request": request, "page": "dashboard"}
    )
```

### Available Routes

| Route | Method | Purpose |
|-------|--------|---------|
| `/enhanced` | GET | Enhanced dashboard UI |
| `/api/metrics/live` | GET | Live system metrics |
| `/api/ai/agents/status` | GET | AI agent health |
| `/api/execution/active` | GET | Active executions |
| `/api/tools` | GET | Tool registry |
| `/api/chains` | GET/POST | Chain management |

### Initialization

Alpine.js stores are auto-initialized on page load via `static/js/init-enhanced.js`:

```javascript
document.addEventListener('DOMContentLoaded', () => {
  Alpine.store('metrics').startAutoRefresh(5000);
  Alpine.store('agents').startAutoRefresh(10000);
  Alpine.store('execution').startAutoRefresh(3000);
});
```

---

## Migration from Old Templates

### Step 1: Update base template reference

```html
<!-- Old -->
{% extends "base.html" %}

<!-- New -->
{% extends "base_enhanced.html" %}
```

### Step 2: Replace static values with Alpine bindings

```html
<!-- Old -->
<span id="active-exercises">5</span>

<!-- New -->
<span x-data x-text="$store.metrics.activeExercises"></span>
```

### Step 3: Use new Chart.js enhancements

```javascript
// Old
createTimelineChart('activityChart', data);

// New
const chart = ChartEnhancements.StreamingChart('activityChart', {
  dataFetchUrl: '/api/metrics/activity'
});
chart.startAutoUpdate();
```

---

## Future Enhancements

1. **WebSocket Integration**: Replace polling with WebSocket for true real-time updates
2. **Offline Support**: Service worker for offline capability
3. **Chart Export**: Export charts as PNG/SVG
4. **Dark/Light Theme Toggle**: User-selectable themes
5. **Accessibility**: WCAG 2.1 AA compliance improvements

---

## References

- [Alpine.js Documentation](https://alpinejs.dev/)
- [Chart.js Documentation](https://www.chartjs.org/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Bootstrap 5 Documentation](https://getbootstrap.com/docs/5.3/)
[0m