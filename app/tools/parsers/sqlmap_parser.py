"""
SQLMap Output Parser

Parses SQLMap results into structured vulnerability data
"""

import re
from typing import Dict, List, Any


def parse_sqlmap(output: str) -> Dict[str, Any]:
    """
    Parse SQLMap output

    Args:
        output: Raw SQLMap output

    Returns:
        Structured injection results
    """
    vulnerabilities = []
    databases = []
    tables = []
    data_dumped = False

    current_vuln = None

    lines = output.split('\n')

    for line in lines:
        # Detect injection type
        if 'Parameter:' in line:
            param_match = re.search(r'Parameter:\s+(\S+)', line)
            if param_match:
                current_vuln = {
                    'parameter': param_match.group(1),
                    'type': None,
                    'title': None
                }

        # Detect injection type details
        if 'Type:' in line and current_vuln:
            type_match = re.search(r'Type:\s+(.+)', line)
            if type_match:
                current_vuln['type'] = type_match.group(1).strip()

        # Detect title
        if 'Title:' in line and current_vuln:
            title_match = re.search(r'Title:\s+(.+)', line)
            if title_match:
                current_vuln['title'] = title_match.group(1).strip()

                # Add vulnerability
                vulnerabilities.append(current_vuln)
                current_vuln = None

        # Detect databases
        db_match = re.search(r'available databases \[(\d+)\]:', line)
        if db_match:
            # Next lines will have database names
            continue

        if line.startswith('[*] ') and databases is not None and not tables:
            db_name = line[4:].strip()
            if db_name and not db_name.startswith('information_schema'):
                databases.append(db_name)

        # Detect tables
        table_match = re.search(r'Database: (\w+)', line)
        if table_match:
            current_db = table_match.group(1)

        if 'Table:' in line:
            table_match = re.search(r'Table:\s+(\S+)', line)
            if table_match:
                tables.append(table_match.group(1))

        # Detect data dump
        if 'dumped to CSV file' in line or 'entries' in line:
            data_dumped = True

    # Determine vulnerability level
    if vulnerabilities:
        vuln_level = 'critical'
    else:
        vuln_level = 'none'

    return {
        'scan_type': 'sqlmap',
        'vulnerable': len(vulnerabilities) > 0,
        'vulnerability_level': vuln_level,
        'vulnerabilities': vulnerabilities,
        'databases_found': databases,
        'tables_found': tables,
        'data_dumped': data_dumped,
        'summary': f"Found {len(vulnerabilities)} SQL injection point(s), {len(databases)} database(s)"
    }
