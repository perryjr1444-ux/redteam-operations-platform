"""
Gobuster Output Parser

Parses directory/file brute-forcing results
"""

import re
from typing import Dict, List, Any


def parse_gobuster(output: str) -> Dict[str, Any]:
    """
    Parse Gobuster output

    Args:
        output: Raw Gobuster output

    Returns:
        Structured directory findings
    """
    discovered = []
    target = None

    lines = output.split('\n')

    for line in lines:
        # Detect target
        if line.startswith('[+] Url:'):
            target_match = re.search(r'\[+\] Url:\s+(\S+)', line)
            if target_match:
                target = target_match.group(1)

        # Detect discovered paths
        # Format: /path (Status: 200) [Size: 1234]
        discovery_match = re.search(r'^(/\S+)\s+\(Status:\s+(\d+)\)(?:\s+\[Size:\s+(\d+)\])?', line)
        if discovery_match:
            path, status, size = discovery_match.groups()

            discovered.append({
                'path': path,
                'status_code': int(status),
                'size': int(size) if size else None,
                'full_url': f"{target}{path}" if target else path
            })

    # Categorize by status code
    success_codes = [d for d in discovered if 200 <= d['status_code'] < 300]
    redirect_codes = [d for d in discovered if 300 <= d['status_code'] < 400]
    forbidden_codes = [d for d in discovered if d['status_code'] == 403]

    return {
        'scan_type': 'gobuster',
        'target': target,
        'discovered_total': len(discovered),
        'discovered': discovered,
        'status_breakdown': {
            'success': len(success_codes),
            'redirects': len(redirect_codes),
            'forbidden': len(forbidden_codes)
        },
        'summary': f"Discovered {len(discovered)} path(s) - {len(success_codes)} accessible"
    }
