"""Podman service for managing attack containers."""

import subprocess
import json
import shlex
import re
from typing import List, Dict, Optional
from datetime import datetime

from .logger import logger
from .config import settings
from .validators import TargetValidator, CommandValidator


class PodmanService:
    """Service for managing Kali Linux attack containers via Podman."""

    def __init__(self):
        self.kali_image = "docker.io/kalilinux/kali-rolling:latest"
        self.pod_name = "redteam-pod"

    def run_podman_command(self, cmd: List[str], capture_output=True) -> Dict:
        """Execute podman command and return result."""
        try:
            result = subprocess.run(
                ["podman"] + cmd,
                capture_output=capture_output,
                text=True,
                timeout=30
            )
            return {
                "success": result.returncode == 0,
                "stdout": result.stdout.strip() if result.stdout else "",
                "stderr": result.stderr.strip() if result.stderr else "",
                "returncode": result.returncode
            }
        except subprocess.TimeoutExpired:
            logger.error(f"Podman command timed out: {' '.join(cmd)}")
            return {"success": False, "error": "Command timed out"}
        except Exception as e:
            logger.error(f"Podman command failed: {e}", exc_info=True)
            return {"success": False, "error": str(e)}

    def ensure_kali_image(self) -> bool:
        """Ensure Kali Linux image is pulled."""
        logger.info(f"Checking for Kali image: {self.kali_image}")

        # Check if image exists
        result = self.run_podman_command(["image", "exists", self.kali_image])

        if not result["success"]:
            logger.info(f"Pulling Kali image: {self.kali_image}")
            pull_result = self.run_podman_command(
                ["pull", self.kali_image],
                capture_output=False
            )
            return pull_result["success"]

        return True

    def launch_attack_container(
        self,
        container_name: str,
        attack_type: str,
        target: str,
        command: str,
        exercise_id: Optional[str] = None,
        detach: bool = True
    ) -> Dict:
        """Launch a Kali Linux container for red team operations."""

        # Ensure image is available
        if not self.ensure_kali_image():
            return {"success": False, "error": "Failed to pull Kali image"}

        # Build podman run command
        podman_cmd = [
            "run",
            "--name", container_name,
            "--pod", self.pod_name,
            "-l", f"exercise_id={exercise_id or 'standalone'}",
            "-l", f"attack_type={attack_type}",
            "-l", f"target={target}",
        ]

        if detach:
            podman_cmd.append("-d")

        # Add Kali image and command
        podman_cmd.append(self.kali_image)
        podman_cmd.extend(["sh", "-c", command])

        logger.info(f"Launching attack container: {container_name}")
        result = self.run_podman_command(podman_cmd)

        if result["success"]:
            container_id = result["stdout"].strip()
            logger.info(f"Container launched: {container_id}")
            return {
                "success": True,
                "container_id": container_id,
                "container_name": container_name
            }
        else:
            logger.error(f"Failed to launch container: {result['stderr']}")
            return {
                "success": False,
                "error": result.get("stderr", "Unknown error")
            }

    def stop_container(self, container_id: str) -> Dict:
        """Stop a running attack container."""
        logger.info(f"Stopping container: {container_id}")
        result = self.run_podman_command(["stop", container_id])

        if result["success"]:
            return {"success": True, "message": f"Container {container_id} stopped"}
        else:
            return {"success": False, "error": result.get("stderr")}

    def remove_container(self, container_id: str, force: bool = False) -> Dict:
        """Remove an attack container."""
        logger.info(f"Removing container: {container_id}")
        cmd = ["rm"]
        if force:
            cmd.append("-f")
        cmd.append(container_id)

        result = self.run_podman_command(cmd)

        if result["success"]:
            return {"success": True, "message": f"Container {container_id} removed"}
        else:
            return {"success": False, "error": result.get("stderr")}

    def get_container_logs(self, container_id: str, tail: int = 100) -> Dict:
        """Get logs from an attack container."""
        result = self.run_podman_command([
            "logs",
            "--tail", str(tail),
            container_id
        ])

        if result["success"]:
            return {
                "success": True,
                "logs": result["stdout"]
            }
        else:
            return {
                "success": False,
                "error": result.get("stderr")
            }

    def list_attack_containers(self, exercise_id: Optional[str] = None) -> List[Dict]:
        """List all attack containers, optionally filtered by exercise."""

        cmd = [
            "ps", "-a",
            "--filter", f"pod={self.pod_name}",
            "--filter", "label=attack_type",
            "--format", "json"
        ]

        if exercise_id:
            cmd.extend(["--filter", f"label=exercise_id={exercise_id}"])

        result = self.run_podman_command(cmd)

        if result["success"] and result["stdout"]:
            try:
                containers = json.loads(result["stdout"])
                return containers if isinstance(containers, list) else [containers]
            except json.JSONDecodeError:
                logger.error("Failed to parse container list JSON")
                return []

        return []

    def execute_in_container(
        self,
        container_id: str,
        command: List[str]
    ) -> Dict:
        """Execute a command in a running container."""

        result = self.run_podman_command(
            ["exec", container_id] + command
        )

        if result["success"]:
            return {
                "success": True,
                "output": result["stdout"]
            }
        else:
            return {
                "success": False,
                "error": result.get("stderr")
            }

    # Pre-defined attack patterns
    def nmap_scan(
        self,
        target: str,
        exercise_id: Optional[str] = None,
        scan_type: str = "quick"
    ) -> Dict:
        """Launch an nmap scan container."""

        # Validate target first
        try:
            target = TargetValidator.sanitize_target(target)
        except ValueError as e:
            logger.error(f"Invalid nmap target: {e}")
            return {"success": False, "error": str(e)}

        # Define scan commands with properly escaped target
        escaped_target = shlex.quote(target)
        scan_commands = {
            "quick": f"nmap -F {escaped_target}",
            "full": f"nmap -p- {escaped_target}",
            "stealth": f"nmap -sS -T2 {escaped_target}",
            "service": f"nmap -sV -sC {escaped_target}"
        }

        command = scan_commands.get(scan_type, scan_commands["quick"])

        # Sanitize target for container name (remove special chars)
        safe_target = re.sub(r'[^a-zA-Z0-9.-]', '-', target)[:50]
        container_name = f"nmap-{safe_target}-{datetime.now().strftime('%Y%m%d%H%M%S')}"

        return self.launch_attack_container(
            container_name=container_name,
            attack_type="nmap",
            target=target,
            command=f"apt-get update -qq && apt-get install -y nmap && {command}",
            exercise_id=exercise_id
        )

    def metasploit_console(
        self,
        target: str,
        exercise_id: Optional[str] = None
    ) -> Dict:
        """Launch an interactive Metasploit container."""

        # Validate target first
        try:
            target = TargetValidator.sanitize_target(target)
        except ValueError as e:
            logger.error(f"Invalid metasploit target: {e}")
            return {"success": False, "error": str(e)}

        # Sanitize target for container name (remove special chars)
        safe_target = re.sub(r'[^a-zA-Z0-9.-]', '-', target)[:50]
        container_name = f"msf-{safe_target}-{datetime.now().strftime('%Y%m%d%H%M%S')}"

        # Start msfconsole in daemon mode
        command = "apt-get update -qq && apt-get install -y metasploit-framework && msfconsole -q"

        return self.launch_attack_container(
            container_name=container_name,
            attack_type="metasploit",
            target=target,
            command=command,
            exercise_id=exercise_id,
            detach=True
        )

    def sql_injection_test(
        self,
        target: str,
        exercise_id: Optional[str] = None
    ) -> Dict:
        """Launch SQLMap for SQL injection testing."""

        # Validate target (must be a URL for SQLMap)
        try:
            target = target.strip()
            if not TargetValidator.is_valid_url(target):
                raise ValueError("SQLMap target must be a valid URL")
        except ValueError as e:
            logger.error(f"Invalid SQLMap target: {e}")
            return {"success": False, "error": str(e)}

        # Sanitize target for container name (remove special chars)
        safe_target = re.sub(r'[^a-zA-Z0-9.-]', '-', target)[:50]
        container_name = f"sqlmap-{safe_target}-{datetime.now().strftime('%Y%m%d%H%M%S')}"

        # Escape target for command
        escaped_target = shlex.quote(target)
        command = f"apt-get update -qq && apt-get install -y sqlmap && sqlmap -u {escaped_target} --batch --crawl=2"

        return self.launch_attack_container(
            container_name=container_name,
            attack_type="sqlmap",
            target=target,
            command=command,
            exercise_id=exercise_id
        )

    def custom_attack(
        self,
        target: str,
        command: str,
        attack_type: str = "custom",
        exercise_id: Optional[str] = None,
        allow_complex: bool = False
    ) -> Dict:
        """Launch a custom attack container with user-defined command."""

        # Validate target
        try:
            target = TargetValidator.sanitize_target(target)
        except ValueError as e:
            logger.error(f"Invalid custom attack target: {e}")
            return {"success": False, "error": str(e)}

        # Validate command
        try:
            command = CommandValidator.sanitize_command(command, allow_complex=allow_complex)
        except ValueError as e:
            logger.error(f"Invalid custom attack command: {e}")
            return {"success": False, "error": str(e)}

        # Sanitize attack_type for container name
        safe_attack_type = re.sub(r'[^a-zA-Z0-9_-]', '-', attack_type)[:50]
        container_name = f"custom-{safe_attack_type}-{datetime.now().strftime('%Y%m%d%H%M%S')}"

        return self.launch_attack_container(
            container_name=container_name,
            attack_type=attack_type,
            target=target,
            command=command,
            exercise_id=exercise_id
        )


# Global instance
podman_service = PodmanService()
