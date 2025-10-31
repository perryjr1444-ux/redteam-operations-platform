"""
Tool Registry - Centralized registry for Kali Linux tools

Maintains metadata, argument schemas, and output parsers for each tool
"""

from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass, field
from enum import Enum

# Import parsers
from .parsers import parse_nmap, parse_sqlmap, parse_nikto, parse_gobuster, parse_generic


class ToolCategory(str, Enum):
    """Tool categories matching Kali metapackages"""
    INFORMATION_GATHERING = "information_gathering"
    VULNERABILITY_ANALYSIS = "vulnerability_analysis"
    WEB_APPLICATION = "web_application"
    EXPLOITATION = "exploitation"
    POST_EXPLOITATION = "post_exploitation"
    PASSWORD_ATTACKS = "password_attacks"
    WIRELESS_ATTACKS = "wireless_attacks"
    FORENSICS = "forensics"


@dataclass
class ToolArgument:
    """Tool argument specification"""
    name: str
    type: str  # 'string', 'int', 'bool', 'file', 'list'
    required: bool = False
    default: Any = None
    description: str = ""
    choices: Optional[List[str]] = None


@dataclass
class ToolDefinition:
    """Complete tool definition"""
    name: str
    command: str
    category: ToolCategory
    description: str
    arguments: List[ToolArgument] = field(default_factory=list)
    parser: Optional[Callable] = None
    requires_root: bool = False
    timeout: int = 3600  # Default 1 hour
    example: Optional[str] = None


class ToolRegistry:
    """
    Central registry for all Kali Linux tools
    """

    def __init__(self):
        self._tools: Dict[str, ToolDefinition] = {}

    def register(self, tool: ToolDefinition):
        """Register a tool"""
        self._tools[tool.name] = tool

    def get(self, name: str) -> Optional[ToolDefinition]:
        """Get tool definition"""
        return self._tools.get(name)

    def list_by_category(self, category: ToolCategory) -> List[ToolDefinition]:
        """List all tools in a category"""
        return [tool for tool in self._tools.values() if tool.category == category]

    def list_all(self) -> List[ToolDefinition]:
        """List all registered tools"""
        return list(self._tools.values())

    def search(self, query: str) -> List[ToolDefinition]:
        """Search tools by name or description"""
        query_lower = query.lower()
        return [
            tool for tool in self._tools.values()
            if query_lower in tool.name.lower() or query_lower in tool.description.lower()
        ]

    def build_command(self, name: str, args: Dict[str, Any]) -> str:
        """
        Build command string from tool name and arguments

        Args:
            name: Tool name
            args: Dictionary of arguments

        Returns:
            Command string ready for execution
        """
        tool = self.get(name)
        if not tool:
            raise ValueError(f"Tool '{name}' not found in registry")

        # Start with base command
        cmd_parts = [tool.command]

        # Add arguments
        for arg_def in tool.arguments:
            arg_value = args.get(arg_def.name, arg_def.default)

            # Skip if not provided and not required
            if arg_value is None:
                if arg_def.required:
                    raise ValueError(f"Required argument '{arg_def.name}' not provided")
                continue

            # Build argument string based on type
            if arg_def.type == 'bool':
                if arg_value:
                    cmd_parts.append(arg_def.name)
            elif arg_def.type == 'list':
                for item in arg_value:
                    cmd_parts.append(f"{arg_def.name} {item}")
            else:
                cmd_parts.append(f"{arg_def.name} {arg_value}")

        return ' '.join(cmd_parts)


# Global registry instance
_registry = ToolRegistry()


def register_tool(tool: ToolDefinition):
    """Decorator/function to register a tool"""
    _registry.register(tool)
    return tool


def get_registry() -> ToolRegistry:
    """Get the global tool registry"""
    return _registry


# Register common Kali tools

register_tool(ToolDefinition(
    name="nmap",
    command="nmap",
    category=ToolCategory.INFORMATION_GATHERING,
    description="Network port scanner and service detection tool",
    arguments=[
        ToolArgument(name="-p", type="string", description="Port specification (e.g., 80,443,1-1000)"),
        ToolArgument(name="-sV", type="bool", description="Service version detection"),
        ToolArgument(name="-sC", type="bool", description="Run default NSE scripts"),
        ToolArgument(name="-O", type="bool", description="OS detection"),
        ToolArgument(name="-A", type="bool", description="Aggressive scan (OS, version, scripts, traceroute)"),
        ToolArgument(name="-T", type="int", description="Timing template (0-5)", default=3),
        ToolArgument(name="-oX", type="string", description="Output to XML file"),
        ToolArgument(name="target", type="string", required=True, description="Target IP or hostname"),
    ],
    parser=parse_nmap,
    timeout=7200,  # 2 hours
    example="nmap -sV -sC -p 80,443 example.com"
))

register_tool(ToolDefinition(
    name="sqlmap",
    command="sqlmap",
    category=ToolCategory.WEB_APPLICATION,
    description="Automated SQL injection detection and exploitation",
    arguments=[
        ToolArgument(name="-u", type="string", required=True, description="Target URL"),
        ToolArgument(name="--dbs", type="bool", description="Enumerate databases"),
        ToolArgument(name="--tables", type="bool", description="Enumerate tables"),
        ToolArgument(name="--dump", type="bool", description="Dump table data"),
        ToolArgument(name="-D", type="string", description="Database name"),
        ToolArgument(name="-T", type="string", description="Table name"),
        ToolArgument(name="--batch", type="bool", default=True, description="Never ask for user input"),
        ToolArgument(name="--risk", type="int", description="Risk level (1-3)", default=1),
        ToolArgument(name="--level", type="int", description="Test level (1-5)", default=1),
    ],
    parser=parse_sqlmap,
    timeout=3600,
    example="sqlmap -u 'http://example.com/page?id=1' --dbs --batch"
))

register_tool(ToolDefinition(
    name="nikto",
    command="nikto",
    category=ToolCategory.WEB_APPLICATION,
    description="Web server vulnerability scanner",
    arguments=[
        ToolArgument(name="-h", type="string", required=True, description="Target host"),
        ToolArgument(name="-p", type="string", description="Port(s) to scan", default="80,443"),
        ToolArgument(name="-ssl", type="bool", description="Force SSL"),
        ToolArgument(name="-Tuning", type="string", description="Tuning options (1-9)"),
    ],
    parser=parse_nikto,
    timeout=1800,
    example="nikto -h example.com -p 80,443"
))

register_tool(ToolDefinition(
    name="gobuster",
    command="gobuster dir",
    category=ToolCategory.WEB_APPLICATION,
    description="Directory and file brute-forcing tool",
    arguments=[
        ToolArgument(name="-u", type="string", required=True, description="Target URL"),
        ToolArgument(name="-w", type="string", required=True, description="Wordlist path"),
        ToolArgument(name="-x", type="string", description="File extensions (e.g., php,html,txt)"),
        ToolArgument(name="-t", type="int", description="Number of threads", default=10),
        ToolArgument(name="-k", type="bool", description="Skip SSL verification"),
        ToolArgument(name="-o", type="string", description="Output file"),
    ],
    parser=parse_gobuster,
    timeout=3600,
    example="gobuster dir -u http://example.com -w /usr/share/wordlists/dirb/common.txt"
))

register_tool(ToolDefinition(
    name="metasploit",
    command="msfconsole",
    category=ToolCategory.EXPLOITATION,
    description="Metasploit Framework console",
    arguments=[
        ToolArgument(name="-r", type="string", description="Resource file to execute"),
        ToolArgument(name="-x", type="string", description="Execute command(s)"),
        ToolArgument(name="-q", type="bool", default=True, description="Quiet mode"),
    ],
    requires_root=True,
    timeout=7200,
    example="msfconsole -q -x 'use exploit/multi/handler; set PAYLOAD windows/meterpreter/reverse_tcp; run'"
))
