"""
Generic Output Parser

Extracts common patterns from tool outputs
"""

import re
from typing import Dict, List, Any


def parse_generic(output: str, tool_name: str = 'unknown') -> Dict[str, Any]:
    """
    Generic parser for tools without specific parsers

    Extracts:
    - IP addresses
    - URLs
    - Email addresses
    - File paths
    - Common vulnerability indicators

    Args:
        output: Raw tool output
        tool_name: Name of the tool

    Returns:
        Extracted patterns and statistics
    """
    # Extract patterns
    ip_addresses = re.findall(r'\b(?:\d{1,3}\.){3}\d{1,3}\b', output)
    urls = re.findall(r'https?://[^\s<>"{}|\\^`\[\]]+', output)
    emails = re.findall(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', output)
    file_paths = re.findall(r'(?:/[\w\-./]+)|(?:[A-Z]:\\[\w\-\\./]+)', output)

    # Look for vulnerability indicators
    vuln_keywords = ['vulnerable', 'exploit', 'injection', 'xss', 'csrf', 'rce', 'lfi', 'rfi', 'sqli']
    vulnerabilities = []

    for line in output.split('\n'):
        line_lower = line.lower()
        for keyword in vuln_keywords:
            if keyword in line_lower:
                vulnerabilities.append({
                    'keyword': keyword,
                    'line': line.strip()
                })

    # Look for credentials
    credential_patterns = [
        r'password[:\s]+(\S+)',
        r'user[:\s]+(\S+)',
        r'api[_\s]?key[:\s]+(\S+)',
        r'token[:\s]+(\S+)'
    ]

    credentials = []
    for pattern in credential_patterns:
        matches = re.findall(pattern, output, re.IGNORECASE)
        credentials.extend(matches)

    # Count errors and warnings
    errors = len(re.findall(r'\berror\b', output, re.IGNORECASE))
    warnings = len(re.findall(r'\bwarning\b', output, re.IGNORECASE))

    # Line count
    lines = len(output.split('\n'))

    return {
        'scan_type': tool_name,
        'line_count': lines,
        'patterns': {
            'ip_addresses': list(set(ip_addresses)),
            'urls': list(set(urls)),
            'emails': list(set(emails)),
            'file_paths': list(set(file_paths))[:20],  # Limit to 20
            'credentials': list(set(credentials))
        },
        'indicators': {
            'vulnerabilities': vulnerabilities[:10],  # Limit to 10
            'errors': errors,
            'warnings': warnings
        },
        'summary': f"{tool_name} output: {lines} lines, {len(vulnerabilities)} potential vulnerabilities"
    }
