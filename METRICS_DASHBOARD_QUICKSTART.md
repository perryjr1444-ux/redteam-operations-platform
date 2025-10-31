[8m# Metrics Dashboard - Quick Start Guide

## Access the Dashboard

**URL:** http://localhost:8000/metrics/dashboard

**Navigation:** Click "Metrics" in the main sidebar

## What You'll See

### 1. Overview Cards (Top Row)
- **Active Exercises:** Current running exercises
- **System Health:** Overall health percentage (color-coded)
- **Running Containers:** Active container count + CPU usage
- **Success Rate:** Attack operation success percentage

### 2. Time Range Selector
Choose your data range: **1h** | **24h** | **7d** | **30d**

### 3. Charts (5 Visualizations)

#### Performance Trends (Line Chart)
- Toggle between CPU, Memory, and Containers
- Shows historical trends

#### Success Rate (Doughnut Chart)
- Success vs Failed vs Pending operations
- Visual percentage breakdown

#### Tool Usage (Bar Chart)
- Most-used tools (nmap, sqlmap, metasploit, etc.)
- Usage count per tool

#### Activity Timeline (Line Chart)
- Operations over time
- Activity patterns

#### Resource Consumption (Multi-line Area Chart)
- Combined CPU, Memory, Container metrics
- Real-time resource tracking

### 4. Container Table
Detailed view of all containers:
- Container ID
- Type
- Status (color-coded)
- CPU & Memory usage
- Uptime
- Operation count

### 5. Activity Log
Real-time feed of recent operations and events

### 6. Export Tools
- **Export CSV:** Download metrics for spreadsheet analysis
- **Export JSON:** Download complete dashboard data
- **Refresh:** Manually update all data

## Quick Actions

### Change Time Range
1. Click one of the time range buttons (1h, 24h, 7d, 30d)
2. All charts update automatically

### View Different Metrics
1. In Performance chart, click CPU/Memory/Containers buttons
2. Chart switches data source instantly

### Export Data
1. Click "Export CSV" or "Export JSON"
2. File downloads automatically
3. Activity is logged

### Clear Activity Log
1. Scroll to Activity Log section
2. Click "Clear Log" button
3. Log resets (new activities continue to appear)

## Auto-Refresh

Dashboard updates automatically:
- **Every 5 seconds:** Live metrics (overview cards)
- **Every 10 seconds:** Activity data (charts, tool usage)
- **Every 30 seconds:** Historical chart data

## Color Coding

### System Health
- **Green (80-100%):** Healthy
- **Yellow (50-79%):** Warning
- **Red (0-49%):** Critical

### Container Status
- **Green badge:** Running
- **Red badge:** Stopped
- **Yellow badge:** Other states

### Activity Types
- **Blue icon:** System events
- **Purple icon:** Operations
- **Green icon:** Success events
- **Cyan icon:** Container events
- **Red icon:** Errors

## API Endpoints (For Developers)

```
GET /api/metrics/live
GET /api/metrics/activity
GET /api/attacks/containers
```

## Files

```
Template:    templates/metrics_dashboard.html
JavaScript:  static/js/metrics-dashboard.js
API:         app/routes/api_enhanced.py
Route:       app/main.py
```

## Troubleshooting

**Charts not showing?**
- Check browser console for errors
- Verify server is running on port 8000
- Ensure Chart.js is loaded

**No data displayed?**
- API endpoints should return valid JSON
- Check network tab in DevTools
- Verify services are running

**Export not working?**
- Check browser download settings
- Disable popup blockers
- View console for errors

## Features Checklist

- [x] Real-time metrics updates
- [x] Multiple chart types
- [x] Time range selection
- [x] Container monitoring
- [x] Activity tracking
- [x] CSV export
- [x] JSON export
- [x] Auto-refresh
- [x] Professional dark theme
- [x] Responsive design

## Need More Info?

See full documentation: `/docs/METRICS_DASHBOARD.md`

## Support

For issues:
1. Check application logs
2. Review browser console
3. Test API endpoints directly
4. Verify network connectivity

---

**Built for:** Red Team Operations
**Version:** 1.0.0
**Framework:** Alpine.js + Chart.js + Bootstrap 5
**Status:** Production Ready
[0m