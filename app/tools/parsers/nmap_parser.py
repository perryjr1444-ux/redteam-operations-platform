"""
Nmap Output Parser

Parses nmap scan results into structured data
"""

import re
from typing import Dict, List, Any
import xml.etree.ElementTree as ET


def parse_nmap(output: str) -> Dict[str, Any]:
    """
    Parse nmap output (text or XML)

    Args:
        output: Raw nmap output

    Returns:
        Structured scan results
    """
    # Try XML parsing first (if -oX was used)
    if output.strip().startswith('<?xml'):
        return parse_nmap_xml(output)

    # Fall back to text parsing
    return parse_nmap_text(output)


def parse_nmap_xml(xml_output: str) -> Dict[str, Any]:
    """Parse nmap XML output"""
    try:
        root = ET.fromstring(xml_output)

        hosts = []
        for host in root.findall('.//host'):
            # Get address
            address_elem = host.find('.//address[@addrtype="ipv4"]')
            if address_elem is None:
                address_elem = host.find('.//address[@addrtype="ipv6"]')

            address = address_elem.get('addr') if address_elem is not None else 'unknown'

            # Get status
            status_elem = host.find('status')
            status = status_elem.get('state') if status_elem is not None else 'unknown'

            # Get hostname
            hostname_elem = host.find('.//hostname')
            hostname = hostname_elem.get('name') if hostname_elem is not None else None

            # Get ports
            ports = []
            for port in host.findall('.//port'):
                port_id = port.get('portid')
                protocol = port.get('protocol')

                state_elem = port.find('state')
                state = state_elem.get('state') if state_elem is not None else 'unknown'

                service_elem = port.find('service')
                service = {}
                if service_elem is not None:
                    service = {
                        'name': service_elem.get('name'),
                        'product': service_elem.get('product'),
                        'version': service_elem.get('version'),
                        'extrainfo': service_elem.get('extrainfo'),
                    }

                ports.append({
                    'port': int(port_id),
                    'protocol': protocol,
                    'state': state,
                    'service': service
                })

            # Get OS detection
            os_matches = []
            for osmatch in host.findall('.//osmatch'):
                os_matches.append({
                    'name': osmatch.get('name'),
                    'accuracy': int(osmatch.get('accuracy', 0))
                })

            hosts.append({
                'address': address,
                'hostname': hostname,
                'status': status,
                'ports': ports,
                'os_matches': os_matches
            })

        return {
            'scan_type': 'nmap',
            'hosts_found': len(hosts),
            'hosts': hosts,
            'summary': f"Found {len(hosts)} host(s)"
        }

    except ET.ParseError as e:
        return {'error': f'XML parse error: {str(e)}'}


def parse_nmap_text(text_output: str) -> Dict[str, Any]:
    """Parse nmap text output"""
    hosts = []
    current_host = None

    lines = text_output.split('\n')

    for line in lines:
        # Detect host line
        host_match = re.search(r'Nmap scan report for ([\w\.\-]+) \(([\d\.]+)\)', line)
        if not host_match:
            host_match = re.search(r'Nmap scan report for ([\d\.]+)', line)

        if host_match:
            if current_host:
                hosts.append(current_host)

            hostname = host_match.group(1) if len(host_match.groups()) > 1 else None
            address = host_match.group(2) if len(host_match.groups()) > 1 else host_match.group(1)

            current_host = {
                'address': address,
                'hostname': hostname,
                'status': 'up',
                'ports': []
            }
            continue

        # Detect port line
        port_match = re.search(r'(\d+)/(tcp|udp)\s+(open|closed|filtered)\s+(\S+)', line)
        if port_match and current_host:
            port_num, protocol, state, service = port_match.groups()

            current_host['ports'].append({
                'port': int(port_num),
                'protocol': protocol,
                'state': state,
                'service': {'name': service}
            })

    # Add last host
    if current_host:
        hosts.append(current_host)

    # Calculate statistics
    open_ports = sum(len([p for p in h['ports'] if p['state'] == 'open']) for h in hosts)

    return {
        'scan_type': 'nmap',
        'hosts_found': len(hosts),
        'open_ports': open_ports,
        'hosts': hosts,
        'summary': f"Found {len(hosts)} host(s) with {open_ports} open port(s)"
    }
