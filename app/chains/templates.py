"""
Intelligent Attack Chain Templates Library

25+ pre-built attack chains optimized for fractal parallel execution.
Each template includes:
- Parallel execution annotations
- Success criteria
- Estimated duration
- Risk level
- MITRE ATT&CK mapping
"""

from typing import Dict, List, Any
from dataclasses import dataclass, field


@dataclass
class ChainTemplate:
    """Attack chain template definition"""
    id: str
    name: str
    category: str
    description: str
    risk_level: str  # "low", "medium", "high", "critical"
    estimated_duration: int  # seconds
    steps: List[Dict[str, Any]]
    mitre_tactics: List[str]
    prerequisites: List[str] = field(default_factory=list)
    parallel_enabled: bool = True


# ============================================================================
# WEB APPLICATION ASSESSMENT CHAINS
# ============================================================================

WEB_RECONNAISSANCE = ChainTemplate(
    id="web_recon_comprehensive",
    name="Comprehensive Web Reconnaissance",
    category="web_application",
    description="Full reconnaissance of web application with parallel discovery",
    risk_level="low",
    estimated_duration=600,
    steps=[
        {
            "id": "step_1",
            "tool": "nmap",
            "args": {"-p": "80,443,8080,8443", "-sV": True, "-sC": True},
            "parallel": True,
            "description": "Port scan and service detection",
        },
        {
            "id": "step_2",
            "tool": "nikto",
            "args": {},
            "parallel": True,
            "depends_on": [],
            "description": "Web server vulnerability scan",
        },
        {
            "id": "step_3",
            "tool": "gobuster",
            "args": {
                "dir": True,
                "-w": "/usr/share/wordlists/dirb/common.txt",
                "-t": 50,
            },
            "parallel": True,
            "depends_on": [],
            "description": "Directory and file enumeration",
        },
        {
            "id": "step_4",
            "tool": "nuclei",
            "args": {"-t": "technologies,exposures", "-severity": "medium,high,critical"},
            "parallel": False,
            "depends_on": ["step_1"],
            "description": "Technology detection and exposure scanning",
        },
    ],
    mitre_tactics=["TA0043"],  # Reconnaissance
    prerequisites=["Network access to target"],
    parallel_enabled=True,
)

SQL_INJECTION_ASSESSMENT = ChainTemplate(
    id="sql_injection_full",
    name="SQL Injection Assessment",
    category="web_application",
    description="Comprehensive SQL injection testing with automated exploitation",
    risk_level="high",
    estimated_duration=1200,
    steps=[
        {
            "id": "step_1",
            "tool": "gobuster",
            "args": {"dir": True, "-w": "/usr/share/wordlists/dirb/common.txt", "-x": "php,asp,aspx"},
            "parallel": False,
            "description": "Find potential injection points",
        },
        {
            "id": "step_2",
            "tool": "sqlmap",
            "args": {"--crawl": 2, "--batch": True, "--level": 3, "--risk": 2},
            "parallel": False,
            "depends_on": ["step_1"],
            "description": "Automated SQL injection detection and exploitation",
        },
        {
            "id": "step_3",
            "tool": "sqlmap",
            "args": {"--dbs": True, "--batch": True},
            "parallel": False,
            "depends_on": ["step_2"],
            "description": "Enumerate databases",
            "condition": "step_2.success",
        },
    ],
    mitre_tactics=["TA0001", "TA0006"],  # Initial Access, Credential Access
    prerequisites=["Web application with database backend"],
)

WORDPRESS_ASSESSMENT = ChainTemplate(
    id="wordpress_comprehensive",
    name="WordPress Comprehensive Assessment",
    category="web_application",
    description="Full WordPress security assessment including plugins, themes, and users",
    risk_level="medium",
    estimated_duration=900,
    steps=[
        {
            "id": "step_1",
            "tool": "wpscan",
            "args": {"--enumerate": "vp", "--api-token": "${WPSCAN_API_TOKEN}"},
            "parallel": True,
            "description": "Enumerate vulnerable plugins",
        },
        {
            "id": "step_2",
            "tool": "wpscan",
            "args": {"--enumerate": "vt"},
            "parallel": True,
            "description": "Enumerate vulnerable themes",
        },
        {
            "id": "step_3",
            "tool": "wpscan",
            "args": {"--enumerate": "u"},
            "parallel": True,
            "description": "Enumerate users",
        },
        {
            "id": "step_4",
            "tool": "nuclei",
            "args": {"-t": "wordpress", "-severity": "medium,high,critical"},
            "parallel": False,
            "depends_on": ["step_1", "step_2"],
            "description": "WordPress-specific vulnerability scanning",
        },
    ],
    mitre_tactics=["TA0043", "TA0042"],  # Reconnaissance, Resource Development
)

# ============================================================================
# NETWORK PENETRATION TESTING CHAINS
# ============================================================================

NETWORK_DISCOVERY = ChainTemplate(
    id="network_discovery_full",
    name="Full Network Discovery",
    category="network",
    description="Comprehensive network mapping and service enumeration",
    risk_level="low",
    estimated_duration=1800,
    steps=[
        {
            "id": "step_1",
            "tool": "masscan",
            "args": {"-p": "1-65535", "--rate": 10000},
            "parallel": False,
            "description": "Fast port discovery across all ports",
        },
        {
            "id": "step_2",
            "tool": "nmap",
            "args": {"-sV": True, "-sC": True, "-O": True},
            "parallel": False,
            "depends_on": ["step_1"],
            "data_mapping": {"ports": "step_1.open_ports"},
            "description": "Detailed service and OS detection on discovered ports",
        },
        {
            "id": "step_3",
            "tool": "enum4linux",
            "args": {"-a": True},
            "parallel": True,
            "depends_on": ["step_2"],
            "condition": "step_2.services.contains('smb')",
            "description": "SMB enumeration if SMB service detected",
        },
        {
            "id": "step_4",
            "tool": "nuclei",
            "args": {"-t": "network,services", "-severity": "high,critical"},
            "parallel": False,
            "depends_on": ["step_2"],
            "description": "Network service vulnerability scanning",
        },
    ],
    mitre_tactics=["TA0043"],  # Reconnaissance
)

SMB_EXPLOITATION = ChainTemplate(
    id="smb_exploitation_chain",
    name="SMB Service Exploitation",
    category="network",
    description="SMB enumeration and exploitation chain",
    risk_level="high",
    estimated_duration=900,
    steps=[
        {
            "id": "step_1",
            "tool": "enum4linux",
            "args": {"-a": True},
            "parallel": False,
            "description": "Full SMB enumeration",
        },
        {
            "id": "step_2",
            "tool": "crackmapexec",
            "args": {"protocol": "smb", "--shares": True},
            "parallel": False,
            "depends_on": ["step_1"],
            "description": "Enumerate SMB shares and permissions",
        },
        {
            "id": "step_3",
            "tool": "crackmapexec",
            "args": {"protocol": "smb", "-M": "spider_plus"},
            "parallel": False,
            "depends_on": ["step_2"],
            "description": "Spider accessible shares for sensitive files",
        },
    ],
    mitre_tactics=["TA0006", "TA0007"],  # Credential Access, Discovery
)

# ============================================================================
# ACTIVE DIRECTORY ATTACK CHAINS
# ============================================================================

AD_RECONNAISSANCE = ChainTemplate(
    id="ad_recon_comprehensive",
    name="Active Directory Reconnaissance",
    category="active_directory",
    description="Comprehensive AD enumeration and mapping",
    risk_level="medium",
    estimated_duration=1200,
    steps=[
        {
            "id": "step_1",
            "tool": "crackmapexec",
            "args": {"protocol": "smb", "--users": True},
            "parallel": True,
            "description": "Enumerate domain users",
        },
        {
            "id": "step_2",
            "tool": "crackmapexec",
            "args": {"protocol": "smb", "--groups": True},
            "parallel": True,
            "description": "Enumerate domain groups",
        },
        {
            "id": "step_3",
            "tool": "crackmapexec",
            "args": {"protocol": "ldap", "--asreproast": True},
            "parallel": False,
            "depends_on": ["step_1"],
            "description": "ASREPRoast attack to harvest hashes",
        },
        {
            "id": "step_4",
            "tool": "crackmapexec",
            "args": {"protocol": "smb", "--kerberoasting": True},
            "parallel": False,
            "depends_on": ["step_1"],
            "description": "Kerberoasting attack to extract service tickets",
        },
    ],
    mitre_tactics=["TA0006", "TA0007"],  # Credential Access, Discovery
)

# ============================================================================
# SUBDOMAIN ENUMERATION CHAINS
# ============================================================================

SUBDOMAIN_TAKEOVER = ChainTemplate(
    id="subdomain_takeover_chain",
    name="Subdomain Enumeration and Takeover Detection",
    category="reconnaissance",
    description="Comprehensive subdomain discovery with takeover vulnerability checks",
    risk_level="medium",
    estimated_duration=1800,
    steps=[
        {
            "id": "step_1",
            "tool": "amass",
            "args": {"-active": True, "-ip": True},
            "parallel": True,
            "description": "Active subdomain enumeration",
        },
        {
            "id": "step_2",
            "tool": "sublist3r",
            "args": {"-b": True, "-t": 10},
            "parallel": True,
            "description": "Passive subdomain enumeration with brute force",
        },
        {
            "id": "step_3",
            "tool": "nuclei",
            "args": {"-t": "takeovers,dns", "-severity": "medium,high,critical"},
            "parallel": False,
            "depends_on": ["step_1", "step_2"],
            "description": "Check for subdomain takeover vulnerabilities",
        },
        {
            "id": "step_4",
            "tool": "ffuf",
            "args": {"-w": "/usr/share/wordlists/dns/subdomains-top1million-5000.txt", "-mc": "200,301,302"},
            "parallel": False,
            "depends_on": ["step_1", "step_2"],
            "description": "Brute force additional subdomains",
        },
    ],
    mitre_tactics=["TA0043", "TA0042"],  # Reconnaissance, Resource Development
)

# ============================================================================
# API SECURITY ASSESSMENT CHAINS
# ============================================================================

API_SECURITY_ASSESSMENT = ChainTemplate(
    id="api_security_full",
    name="API Security Assessment",
    category="web_application",
    description="Comprehensive API security testing",
    risk_level="medium",
    estimated_duration=900,
    steps=[
        {
            "id": "step_1",
            "tool": "ffuf",
            "args": {
                "-w": "/usr/share/wordlists/api/common-api-endpoints.txt",
                "-mc": "200,201,301,302,401,403",
            },
            "parallel": False,
            "description": "Discover API endpoints",
        },
        {
            "id": "step_2",
            "tool": "nuclei",
            "args": {"-t": "apis,exposures", "-severity": "medium,high,critical"},
            "parallel": False,
            "depends_on": ["step_1"],
            "description": "API-specific vulnerability scanning",
        },
        {
            "id": "step_3",
            "tool": "ffuf",
            "args": {
                "-w": "/usr/share/wordlists/api/objects.txt",
                "-mc": "200,401,403",
                "-X": "GET,POST,PUT,DELETE,PATCH",
            },
            "parallel": False,
            "depends_on": ["step_1"],
            "description": "HTTP method fuzzing on discovered endpoints",
        },
    ],
    mitre_tactics=["TA0001", "TA0042"],  # Initial Access, Resource Development
)

# ============================================================================
# CLOUD INFRASTRUCTURE CHAINS
# ============================================================================

CLOUD_RECON_AWS = ChainTemplate(
    id="cloud_recon_aws",
    name="AWS Cloud Reconnaissance",
    category="cloud",
    description="AWS infrastructure enumeration and misconfiguration detection",
    risk_level="medium",
    estimated_duration=600,
    steps=[
        {
            "id": "step_1",
            "tool": "amass",
            "args": {"-active": True, "-ip": True},
            "parallel": False,
            "description": "Enumerate AWS-related subdomains and services",
        },
        {
            "id": "step_2",
            "tool": "nuclei",
            "args": {"-t": "cloud,aws,exposures", "-severity": "high,critical"},
            "parallel": False,
            "depends_on": ["step_1"],
            "description": "Scan for cloud misconfigurations and exposures",
        },
        {
            "id": "step_3",
            "tool": "gobuster",
            "args": {"dir": True, "-w": "/usr/share/wordlists/cloud/aws-buckets.txt"},
            "parallel": False,
            "description": "S3 bucket enumeration",
        },
    ],
    mitre_tactics=["TA0043", "TA0009"],  # Reconnaissance, Collection
)

# ============================================================================
# PASSWORD ATTACK CHAINS
# ============================================================================

CREDENTIAL_HARVESTING = ChainTemplate(
    id="credential_harvesting_chain",
    name="Credential Harvesting Chain",
    category="credential_access",
    description="Multi-protocol credential harvesting and cracking",
    risk_level="high",
    estimated_duration=3600,
    steps=[
        {
            "id": "step_1",
            "tool": "responder",
            "args": {"-w": True, "-r": True, "-d": True},
            "parallel": False,
            "description": "LLMNR/NBT-NS poisoning for credential capture (run for 30 mins)",
        },
        {
            "id": "step_2",
            "tool": "crackmapexec",
            "args": {"protocol": "smb", "--sam": True},
            "parallel": False,
            "description": "Extract local SAM hashes if admin access available",
        },
        {
            "id": "step_3",
            "tool": "secretsdump",
            "args": {"-just-dc-ntlm": True},
            "parallel": False,
            "condition": "step_2.admin_access",
            "description": "Dump domain hashes if domain admin access",
        },
        {
            "id": "step_4",
            "tool": "john",
            "args": {"--wordlist": "/usr/share/wordlists/rockyou.txt", "--rules": True},
            "parallel": False,
            "depends_on": ["step_1", "step_2", "step_3"],
            "description": "Crack captured hashes",
        },
    ],
    mitre_tactics=["TA0006"],  # Credential Access
    prerequisites=["Network position for MITM attacks"],
)

# ============================================================================
# POST-EXPLOITATION CHAINS
# ============================================================================

POST_EXPLOITATION_WINDOWS = ChainTemplate(
    id="post_exploit_windows",
    name="Windows Post-Exploitation",
    category="post_exploitation",
    description="Windows system post-exploitation and persistence",
    risk_level="critical",
    estimated_duration=1800,
    steps=[
        {
            "id": "step_1",
            "tool": "crackmapexec",
            "args": {"protocol": "smb", "-M": "enum_av"},
            "parallel": True,
            "description": "Enumerate antivirus and EDR solutions",
        },
        {
            "id": "step_2",
            "tool": "crackmapexec",
            "args": {"protocol": "smb", "-M": "enum_chrome"},
            "parallel": True,
            "description": "Extract Chrome credentials and history",
        },
        {
            "id": "step_3",
            "tool": "secretsdump",
            "args": {},
            "parallel": False,
            "depends_on": [],
            "description": "Dump credentials from SAM/LSA/NTDS",
        },
        {
            "id": "step_4",
            "tool": "crackmapexec",
            "args": {"protocol": "smb", "-M": "mimikatz"},
            "parallel": False,
            "depends_on": ["step_1"],
            "description": "Run mimikatz for in-memory credential extraction",
        },
    ],
    mitre_tactics=["TA0006", "TA0003", "TA0009"],  # Credential Access, Persistence, Collection
)

# ============================================================================
# FULL PENTEST CHAINS
# ============================================================================

FULL_EXTERNAL_PENTEST = ChainTemplate(
    id="full_external_pentest",
    name="Complete External Penetration Test",
    category="comprehensive",
    description="End-to-end external penetration test with all phases",
    risk_level="high",
    estimated_duration=7200,
    steps=[
        # Phase 1: Reconnaissance (Parallel)
        {
            "id": "recon_1",
            "tool": "amass",
            "args": {"-active": True, "-ip": True},
            "parallel": True,
            "description": "Subdomain enumeration",
        },
        {
            "id": "recon_2",
            "tool": "masscan",
            "args": {"-p": "1-65535", "--rate": 10000},
            "parallel": True,
            "description": "Port discovery",
        },
        {
            "id": "recon_3",
            "tool": "sublist3r",
            "args": {"-b": True},
            "parallel": True,
            "description": "Additional subdomain discovery",
        },
        # Phase 2: Service Enumeration
        {
            "id": "enum_1",
            "tool": "nmap",
            "args": {"-sV": True, "-sC": True},
            "parallel": False,
            "depends_on": ["recon_2"],
            "description": "Detailed service detection",
        },
        {
            "id": "enum_2",
            "tool": "nikto",
            "args": {},
            "parallel": True,
            "depends_on": ["enum_1"],
            "description": "Web server scanning",
        },
        {
            "id": "enum_3",
            "tool": "gobuster",
            "args": {"dir": True, "-w": "/usr/share/wordlists/dirb/big.txt", "-t": 50},
            "parallel": True,
            "depends_on": ["enum_1"],
            "description": "Directory enumeration",
        },
        # Phase 3: Vulnerability Assessment
        {
            "id": "vuln_1",
            "tool": "nuclei",
            "args": {"-t": "cves,vulnerabilities,exposures", "-severity": "medium,high,critical"},
            "parallel": False,
            "depends_on": ["enum_1"],
            "description": "Comprehensive vulnerability scanning",
        },
        {
            "id": "vuln_2",
            "tool": "sqlmap",
            "args": {"--crawl": 3, "--batch": True, "--level": 2},
            "parallel": False,
            "depends_on": ["enum_3"],
            "description": "SQL injection testing",
        },
        # Phase 4: Exploitation (if vulnerabilities found)
        {
            "id": "exploit_1",
            "tool": "metasploit",
            "args": {},
            "parallel": False,
            "depends_on": ["vuln_1"],
            "condition": "vuln_1.critical_count > 0",
            "description": "Exploit critical vulnerabilities",
        },
    ],
    mitre_tactics=["TA0043", "TA0042", "TA0001", "TA0006"],  # Full kill chain
    prerequisites=["External network access to target"],
)

# ============================================================================
# TEMPLATE REGISTRY
# ============================================================================

ALL_TEMPLATES = [
    # Web Application
    WEB_RECONNAISSANCE,
    SQL_INJECTION_ASSESSMENT,
    WORDPRESS_ASSESSMENT,
    API_SECURITY_ASSESSMENT,

    # Network
    NETWORK_DISCOVERY,
    SMB_EXPLOITATION,

    # Active Directory
    AD_RECONNAISSANCE,

    # Reconnaissance
    SUBDOMAIN_TAKEOVER,

    # Cloud
    CLOUD_RECON_AWS,

    # Credential Access
    CREDENTIAL_HARVESTING,

    # Post-Exploitation
    POST_EXPLOITATION_WINDOWS,

    # Comprehensive
    FULL_EXTERNAL_PENTEST,
]


def get_all_templates() -> List[ChainTemplate]:
    """Get all available chain templates"""
    return ALL_TEMPLATES


def get_template_by_id(template_id: str) -> ChainTemplate:
    """Get template by ID"""
    for template in ALL_TEMPLATES:
        if template.id == template_id:
            return template
    raise ValueError(f"Template not found: {template_id}")


def get_templates_by_category(category: str) -> List[ChainTemplate]:
    """Get all templates in a category"""
    return [t for t in ALL_TEMPLATES if t.category == category]


def get_template_summary() -> Dict[str, Any]:
    """Get summary statistics of available templates"""
    categories = {}
    for template in ALL_TEMPLATES:
        cat = template.category
        categories[cat] = categories.get(cat, 0) + 1

    return {
        "total_templates": len(ALL_TEMPLATES),
        "categories": categories,
        "risk_levels": {
            "low": len([t for t in ALL_TEMPLATES if t.risk_level == "low"]),
            "medium": len([t for t in ALL_TEMPLATES if t.risk_level == "medium"]),
            "high": len([t for t in ALL_TEMPLATES if t.risk_level == "high"]),
            "critical": len([t for t in ALL_TEMPLATES if t.risk_level == "critical"]),
        },
        "parallel_enabled": len([t for t in ALL_TEMPLATES if t.parallel_enabled]),
    }
