"""
Nikto Output Parser

Parses Nikto web server scan results
"""

import re
from typing import Dict, List, Any


def parse_nikto(output: str) -> Dict[str, Any]:
    """
    Parse Nikto output

    Args:
        output: Raw Nikto output

    Returns:
        Structured vulnerability findings
    """
    findings = []
    target = None
    server = None

    lines = output.split('\n')

    for line in lines:
        # Detect target
        target_match = re.search(r'Target IP:\s+([\d\.]+)', line)
        if target_match:
            target = target_match.group(1)

        target_match = re.search(r'Target Hostname:\s+(\S+)', line)
        if target_match and not target:
            target = target_match.group(1)

        # Detect server
        server_match = re.search(r'Server:\s+(.+)', line)
        if server_match:
            server = server_match.group(1).strip()

        # Detect findings (+ lines)
        if line.startswith('+ '):
            finding = line[2:].strip()

            # Categorize finding
            category = 'info'
            severity = 'low'

            if any(keyword in finding.lower() for keyword in ['vulnerable', 'exploit', 'injection', 'xss']):
                category = 'vulnerability'
                severity = 'high'
            elif any(keyword in finding.lower() for keyword in ['outdated', 'version', 'disclosure']):
                category = 'misconfiguration'
                severity = 'medium'

            findings.append({
                'description': finding,
                'category': category,
                'severity': severity
            })

    # Calculate statistics
    high_sev = len([f for f in findings if f['severity'] == 'high'])
    medium_sev = len([f for f in findings if f['severity'] == 'medium'])
    low_sev = len([f for f in findings if f['severity'] == 'low'])

    return {
        'scan_type': 'nikto',
        'target': target,
        'server': server,
        'findings_total': len(findings),
        'findings': findings,
        'severity_counts': {
            'high': high_sev,
            'medium': medium_sev,
            'low': low_sev
        },
        'summary': f"Found {len(findings)} issue(s) - {high_sev} high, {medium_sev} medium, {low_sev} low"
    }
