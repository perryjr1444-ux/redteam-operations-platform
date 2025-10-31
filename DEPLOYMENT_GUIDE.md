# Red Team C2 Platform - Deployment Guide

## Quick Start (Development)

```bash
# 1. Install frontend dependencies
npm install

# 2. Build frontend islands
npm run build
# OR
./scripts/build-frontend.sh

# 3. Install Python dependencies (if not using Docker)
pip install -r requirements.txt

# 4. Start the application
./start-redteam-app.sh
```

## Production Deployment (Docker)

```bash
# Build and start with Docker
./start-redteam-app.sh

# This will:
# - Build the Kali Linux container with all tools
# - Install Python dependencies
# - Copy frontend bundles
# - Start the application on port 5172
```

## Manual Setup

### 1. Frontend Build

```bash
# Install Node.js dependencies
npm install

# Build islands with Vite
npm run build

# Output will be in: static/dist/islands.js
```

### 2. Backend Setup

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Initialize database
alembic upgrade head

# Run application
uvicorn app.main:app --host 0.0.0.0 --port 5172 --workers 4
```

### 3. Kali Tools (Container Only)

The following tools are pre-installed in the Docker container:
- nmap (network scanning)
- sqlmap (SQL injection)
- nikto (web vulnerability scanning)
- gobuster (directory brute-forcing)
- metasploit-framework (exploitation)
- whois, dnsutils, netcat
- dirb, wfuzz
- masscan, tcpdump

## Application Structure

```
redteam_py_app/
├── frontend/               # Islands architecture
│   ├── islands/           # Island components
│   │   ├── terminal.js    # Terminal with xterm.js
│   │   ├── metrics.js     # Live metrics (D3.js)
│   │   ├── attackChain.js # Workflow builder
│   │   ├── outputViewer.js# Dual output view
│   │   └── threatMap.js   # Network topology
│   ├── services/
│   │   └── websocket.js   # WebSocket client
│   ├── lib/
│   │   └── island.js      # Hydration system
│   └── islands.js         # Entry point
│
├── app/
│   ├── tools/             # Kali tools integration
│   │   ├── executor.py    # Async tool execution
│   │   ├── registry.py    # Tool definitions
│   │   ├── chain.py       # Attack orchestrator
│   │   └── parsers/       # Output parsers
│   ├── websocket.py       # WebSocket server
│   ├── api.py             # REST API
│   ├── routes_c2.py       # C2 interface routes
│   └── main.py            # FastAPI application
│
├── templates/             # Military C2 templates
│   ├── c2_base.html      # Base layout
│   ├── c2_dashboard.html # Dashboard
│   ├── c2_chains.html    # Attack chains
│   └── c2_results.html   # Results viewer
│
├── Containerfile          # Kali Linux container
├── docker-compose.yml     # Compose config
├── vite.config.js         # Frontend build
└── tailwind.config.js     # CSS config
```

## Accessing the Platform

After deployment, access the platform at:

**URL**: http://localhost:5172

### Main Pages

- **Dashboard** (`/`) - Tactical overview with terminal, metrics, and threat map
- **Tools** (`/tools`) - Arsenal catalog of available tools
- **Attack Chains** (`/chains`) - Workflow builder for automated attacks
- **Results** (`/results`) - Execution history and analysis
- **Network Map** (`/topology`) - Interactive threat visualization

### API Endpoints

- `GET /api/tools` - List all tools
- `GET /api/metrics` - System metrics
- `GET /api/results` - Execution results
- `GET /api/topology` - Network topology
- `WS /api/ws` - WebSocket for real-time execution

## Features

### Islands Architecture
- Server-side rendering with selective client-side hydration
- Fast initial load, interactive components
- Minimal JavaScript bundle size

### Real-time Execution
- WebSocket streaming of tool output
- Live terminal with xterm.js
- Progress updates for attack chains

### Attack Chains
- Drag-and-drop workflow builder
- Dependency resolution
- Conditional execution
- Data passing between steps

### Tool Integration
- 5 pre-configured tools (nmap, sqlmap, nikto, gobuster, metasploit)
- Async subprocess execution
- Output parsing for structured data
- Registry system for easy expansion

### Security
- Quantum-inspired key generation
- Secure tool execution isolation
- Non-root container user
- Rate limiting and validation

## Troubleshooting

### Frontend build fails
```bash
# Clear cache and reinstall
rm -rf node_modules package-lock.json
npm install
npm run build
```

### WebSocket connection fails
Check that the WebSocket endpoint is accessible:
```bash
curl -i -N -H "Connection: Upgrade" -H "Upgrade: websocket" \
  -H "Sec-WebSocket-Version: 13" -H "Sec-WebSocket-Key: test" \
  http://localhost:5172/api/ws
```

### Container build fails
```bash
# Clean rebuild
podman system prune -a
./start-redteam-app.sh
```

### Tools not found in container
The tools are installed in the Kali container but not on the host.
Make sure you're running commands inside the container:
```bash
podman exec -it redteam-app nmap --version
```

## Development

### Watch mode (frontend)
```bash
npm run dev
# Vite dev server on http://localhost:5173
# Proxies API requests to localhost:5172
```

### Hot reload (backend)
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 5172
```

## Production Checklist

- [ ] Set `SECRET_KEY` environment variable (or use quantum generation)
- [ ] Configure production database (PostgreSQL recommended)
- [ ] Set `ENVIRONMENT=production`
- [ ] Build frontend: `npm run build`
- [ ] Enable HTTPS/TLS
- [ ] Configure rate limiting
- [ ] Set up log aggregation
- [ ] Configure monitoring
- [ ] Run security scan

## Advanced Configuration

### Add New Tools

Edit `app/tools/registry.py`:

```python
register_tool(ToolDefinition(
    name="custom_tool",
    command="tool-command",
    category=ToolCategory.EXPLOITATION,
    description="Tool description",
    arguments=[...],
    parser=custom_parser,
    timeout=3600
))
```

### Create Custom Attack Chains

Edit `app/tools/chain.py`:

```python
CUSTOM_CHAIN = ChainDefinition(
    id="custom_chain",
    name="Custom Attack Chain",
    description="Description",
    steps=[
        ChainStep(id="step1", tool="nmap", args={...}),
        ChainStep(id="step2", tool="sqlmap", args={...}, depends_on=["step1"]),
    ]
)

# Register
orchestrator.register_chain(CUSTOM_CHAIN)
```

---

**Built with Islands Architecture, Kali Linux, and Military-Grade Design**

For issues or questions, check the BUILD_STATUS.md file.
