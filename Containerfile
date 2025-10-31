# Multi-stage production-grade container build with Kali Tools
# Stage 1: Builder
FROM kalilinux/kali-rolling AS builder

WORKDIR /build

# Install Kali metapackages and build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    python3-dev \
    python3-pip \
    # Kali Tools - Top 10 essentials
    nmap \
    sqlmap \
    nikto \
    gobuster \
    metasploit-framework \
    # Additional reconnaissance tools
    whois \
    dnsutils \
    netcat-traditional \
    # Web application tools
    dirb \
    wfuzz \
    # Network tools
    masscan \
    tcpdump \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --user --break-system-packages -r requirements.txt

# Stage 2: Runtime
FROM kalilinux/kali-rolling

# Create non-root user
RUN groupadd -r appuser && useradd -r -g appuser -G sudo appuser

# Install runtime dependencies and Kali tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 \
    python3-pip \
    # Kali Tools
    nmap \
    sqlmap \
    nikto \
    gobuster \
    metasploit-framework \
    whois \
    dnsutils \
    netcat-traditional \
    dirb \
    wfuzz \
    masscan \
    tcpdump \
    # Additional utilities
    curl \
    wget \
    git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy Python dependencies from builder
COPY --from=builder /root/.local /home/appuser/.local

# Copy application code
COPY app/ ./app/
COPY templates/ ./templates/
COPY static/ ./static/
COPY certs/ ./certs/
COPY cli_schema.yaml .
COPY alembic.ini .
COPY alembic/ ./alembic/

# Create directories and set permissions
RUN mkdir -p /app/db /app/logs && \
    chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Add local Python packages to PATH
ENV PATH=/home/appuser/.local/bin:$PATH \
    PYTHONPATH=/app \
    PYTHONUNBUFFERED=1

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=40s --retries=3 \
    CMD python -c "import urllib.request; import ssl; ctx = ssl._create_unverified_context(); urllib.request.urlopen('https://localhost:5172/api/liveness', context=ctx)" || exit 1

# Expose port
EXPOSE 5172

# Run database migrations and start application with SSL
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 5172 --workers 4 --ssl-keyfile=/app/certs/key.pem --ssl-certfile=/app/certs/cert.pem"]
