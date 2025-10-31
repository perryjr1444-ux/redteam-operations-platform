"""Input validation and sanitization utilities."""

import re
import ipaddress
from typing import Optional
from urllib.parse import urlparse
from pydantic import BaseModel, Field, field_validator


class TargetValidator:
    """Validator for attack targets (IPs, domains, URLs)."""

    @staticmethod
    def is_valid_ip(target: str) -> bool:
        """Check if target is a valid IP address (IPv4 or IPv6)."""
        try:
            ipaddress.ip_address(target)
            return True
        except ValueError:
            return False

    @staticmethod
    def is_valid_cidr(target: str) -> bool:
        """Check if target is a valid CIDR notation."""
        try:
            ipaddress.ip_network(target, strict=False)
            return True
        except ValueError:
            return False

    @staticmethod
    def is_valid_hostname(target: str) -> bool:
        """Check if target is a valid hostname/domain."""
        # RFC 1123 hostname regex
        hostname_pattern = r'^(?=.{1,253}$)(?!-)[A-Za-z0-9-]{1,63}(?<!-)(\.[A-Za-z0-9-]{1,63})*$'
        return bool(re.match(hostname_pattern, target))

    @staticmethod
    def is_valid_url(target: str) -> bool:
        """Check if target is a valid URL."""
        try:
            result = urlparse(target)
            return all([result.scheme, result.netloc])
        except Exception:
            return False

    @staticmethod
    def sanitize_target(target: str) -> str:
        """
        Sanitize and validate a target string.

        Raises ValueError if target contains shell metacharacters or is invalid.
        """
        if not target or len(target) > 500:
            raise ValueError("Target must be between 1 and 500 characters")

        # Remove leading/trailing whitespace
        target = target.strip()

        # Check for shell metacharacters that could be used for injection
        dangerous_chars = [';', '&', '|', '`', '$', '(', ')', '<', '>', '\n', '\r']
        for char in dangerous_chars:
            if char in target:
                raise ValueError(f"Invalid character in target: {char}")

        # Validate target format
        if not (
            TargetValidator.is_valid_ip(target) or
            TargetValidator.is_valid_cidr(target) or
            TargetValidator.is_valid_hostname(target) or
            TargetValidator.is_valid_url(target)
        ):
            raise ValueError(
                "Target must be a valid IP address, CIDR range, hostname, or URL"
            )

        return target


class CommandValidator:
    """Validator for custom attack commands."""

    # Whitelist of allowed commands for security tools
    ALLOWED_COMMANDS = {
        'nmap', 'masscan', 'nikto', 'gobuster', 'dirb', 'ffuf',
        'sqlmap', 'wpscan', 'hydra', 'john', 'hashcat',
        'metasploit-framework', 'msfconsole', 'msfvenom',
        'burpsuite', 'zaproxy', 'nuclei', 'subfinder',
        'amass', 'dnsenum', 'fierce', 'dnsrecon',
        'whois', 'dig', 'host', 'nslookup', 'ping', 'traceroute',
        'curl', 'wget', 'nc', 'netcat', 'socat',
        'ssh', 'scp', 'ftp', 'telnet', 'smtp-user-enum',
        'enum4linux', 'smbclient', 'rpcclient', 'crackmapexec',
        'responder', 'impacket', 'bloodhound', 'mimikatz',
        'powershell', 'python', 'python3', 'ruby', 'perl', 'bash', 'sh',
        'apt-get', 'apt', 'dpkg', 'pip', 'pip3', 'gem', 'npm'
    }

    # Dangerous command patterns that should be blocked
    BLOCKED_PATTERNS = [
        r'rm\s+-rf',  # Dangerous file deletion
        r'mkfs\.',  # Filesystem formatting
        r'dd\s+if=',  # Disk operations
        r'>\s*/dev/sd',  # Writing to disk devices
        r'fork\s*\(',  # Fork bombs
        r':\(\)\{',  # Fork bomb pattern
        r'curl.*\|\s*bash',  # Piping to shell
        r'wget.*\|\s*sh',  # Piping to shell
    ]

    @staticmethod
    def sanitize_command(command: str, allow_complex: bool = False) -> str:
        """
        Sanitize and validate a custom command.

        Args:
            command: The command string to validate
            allow_complex: If True, allows command chaining with && and pipes

        Raises:
            ValueError: If command is invalid or contains dangerous patterns
        """
        if not command or len(command) > 5000:
            raise ValueError("Command must be between 1 and 5000 characters")

        command = command.strip()

        # Check for blocked patterns
        for pattern in CommandValidator.BLOCKED_PATTERNS:
            if re.search(pattern, command, re.IGNORECASE):
                raise ValueError(f"Command contains blocked pattern: {pattern}")

        # If not allowing complex commands, check for shell metacharacters
        if not allow_complex:
            dangerous_chars = [';', '&', '|', '`', '$()']
            for char in dangerous_chars:
                if char in command:
                    raise ValueError(
                        f"Command contains shell metacharacter: {char}. "
                        "Use simple commands only or enable complex mode."
                    )

        # Extract base command (first word)
        base_command = command.split()[0] if command.split() else ""

        # Validate that base command is in allowlist (skip if starts with apt-get/apt for installation)
        if base_command and not command.startswith(('apt-get', 'apt ', 'pip')):
            if base_command not in CommandValidator.ALLOWED_COMMANDS:
                raise ValueError(
                    f"Command '{base_command}' is not in the allowed list. "
                    f"Allowed commands: {', '.join(sorted(CommandValidator.ALLOWED_COMMANDS))}"
                )

        return command


# Pydantic schemas for attack endpoints
class NmapScanRequest(BaseModel):
    """Schema for nmap scan requests."""

    target: str = Field(..., min_length=1, max_length=500)
    scan_type: str = Field(default="quick", pattern="^(quick|full|stealth|service)$")
    exercise_id: Optional[str] = Field(None, max_length=100)

    @field_validator('target')
    @classmethod
    def validate_target(cls, v):
        """Validate and sanitize target."""
        return TargetValidator.sanitize_target(v)


class MetasploitRequest(BaseModel):
    """Schema for metasploit requests."""

    target: str = Field(..., min_length=1, max_length=500)
    exercise_id: Optional[str] = Field(None, max_length=100)

    @field_validator('target')
    @classmethod
    def validate_target(cls, v):
        """Validate and sanitize target."""
        return TargetValidator.sanitize_target(v)


class SQLMapRequest(BaseModel):
    """Schema for sqlmap requests."""

    target: str = Field(..., min_length=1, max_length=1000)
    exercise_id: Optional[str] = Field(None, max_length=100)

    @field_validator('target')
    @classmethod
    def validate_target(cls, v):
        """Validate URL target for SQLMap."""
        v = v.strip()
        if not TargetValidator.is_valid_url(v):
            raise ValueError("SQLMap target must be a valid URL")
        return v


class CustomAttackRequest(BaseModel):
    """Schema for custom attack requests."""

    target: str = Field(..., min_length=1, max_length=500)
    command: str = Field(..., min_length=1, max_length=5000)
    attack_type: str = Field(default="custom", max_length=50)
    exercise_id: Optional[str] = Field(None, max_length=100)
    allow_complex: bool = Field(default=False)

    @field_validator('target')
    @classmethod
    def validate_target(cls, v):
        """Validate and sanitize target."""
        return TargetValidator.sanitize_target(v)

    @field_validator('command')
    @classmethod
    def validate_command(cls, v, info):
        """Validate and sanitize command."""
        allow_complex = info.data.get('allow_complex', False)
        return CommandValidator.sanitize_command(v, allow_complex=allow_complex)

    @field_validator('attack_type')
    @classmethod
    def validate_attack_type(cls, v):
        """Validate attack type."""
        # Only allow alphanumeric, hyphens, and underscores
        if not re.match(r'^[a-zA-Z0-9_-]+$', v):
            raise ValueError("Attack type must contain only alphanumeric characters, hyphens, and underscores")
        return v
