"""WebSocket terminal streaming for real-time container output."""

import asyncio
import subprocess
from typing import Optional
from fastapi import WebSocket, WebSocketDisconnect
from .logger import logger


class TerminalStreamer:
    """Stream container output via WebSocket."""

    def __init__(self):
        self.active_connections: dict[str, list[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, container_id: str):
        """Connect WebSocket client for a container."""
        await websocket.accept()

        if container_id not in self.active_connections:
            self.active_connections[container_id] = []

        self.active_connections[container_id].append(websocket)
        logger.info(f"WebSocket connected for container: {container_id}")

    def disconnect(self, websocket: WebSocket, container_id: str):
        """Disconnect WebSocket client."""
        if container_id in self.active_connections:
            if websocket in self.active_connections[container_id]:
                self.active_connections[container_id].remove(websocket)

            if not self.active_connections[container_id]:
                del self.active_connections[container_id]

        logger.info(f"WebSocket disconnected for container: {container_id}")

    async def stream_container_logs(
        self, websocket: WebSocket, container_id: str, follow: bool = True
    ):
        """Stream container logs to WebSocket client."""
        try:
            # Build podman logs command
            cmd = ["podman", "logs"]
            if follow:
                cmd.append("-f")  # Follow log output
            cmd.append(container_id)

            # Start subprocess
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
            )

            # Stream output line by line
            for line in iter(process.stdout.readline, ""):
                if not line:
                    break

                try:
                    await websocket.send_text(line)
                except WebSocketDisconnect:
                    logger.info(f"Client disconnected from {container_id}")
                    process.terminate()
                    break
                except Exception as e:
                    logger.error(f"Error sending to WebSocket: {e}")
                    process.terminate()
                    break

            process.wait(timeout=1)

        except subprocess.TimeoutExpired:
            process.kill()
        except Exception as e:
            logger.error(f"Error streaming container logs: {e}")
            await websocket.send_text(f"Error: {str(e)}\r\n")

    async def execute_command(
        self, websocket: WebSocket, container_id: str, command: str
    ):
        """Execute command in container and stream output."""
        try:
            # Build podman exec command
            cmd = ["podman", "exec", "-it", container_id, "sh", "-c", command]

            # Start subprocess
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
            )

            # Send initial prompt
            await websocket.send_text(f"$ {command}\r\n")

            # Stream output
            for line in iter(process.stdout.readline, ""):
                if not line:
                    break

                try:
                    await websocket.send_text(line)
                except WebSocketDisconnect:
                    process.terminate()
                    break

            # Wait for process to complete
            return_code = process.wait(timeout=300)

            # Send completion message
            await websocket.send_text(f"\r\nCommand completed (exit code: {return_code})\r\n")

        except subprocess.TimeoutExpired:
            process.kill()
            await websocket.send_text("\r\nCommand timed out after 5 minutes\r\n")
        except Exception as e:
            logger.error(f"Error executing command: {e}")
            await websocket.send_text(f"Error: {str(e)}\r\n")


# Global instance
terminal_streamer = TerminalStreamer()
