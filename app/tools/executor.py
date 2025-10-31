"""
Async Tool Executor with Real-time Streaming
"""

import asyncio
import subprocess
from typing import AsyncIterator, Optional, Dict, Any
from datetime import datetime
import shlex


class ToolExecutor:
    """
    Execute Kali Linux tools asynchronously with streaming output
    """

    def __init__(self):
        self.running_processes = {}

    async def execute(
        self,
        command: str,
        cwd: Optional[str] = None,
        env: Optional[Dict[str, str]] = None,
        timeout: Optional[int] = 3600
    ) -> AsyncIterator[Dict[str, Any]]:
        """
        Execute a command and yield output line by line

        Args:
            command: Command string to execute
            cwd: Working directory
            env: Environment variables
            timeout: Execution timeout in seconds

        Yields:
            Dict with type ('stdout'|'stderr'|'complete'|'error') and data
        """
        start_time = datetime.utcnow()

        try:
            # Parse command safely
            cmd_args = shlex.split(command)

            # Create subprocess
            process = await asyncio.create_subprocess_exec(
                *cmd_args,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=cwd,
                env=env
            )

            # Store process reference
            execution_id = f"proc_{id(process)}"
            self.running_processes[execution_id] = process

            # Read stdout and stderr concurrently
            async def read_stream(stream, stream_type):
                while True:
                    line = await stream.readline()
                    if not line:
                        break

                    try:
                        decoded = line.decode('utf-8', errors='replace').rstrip()
                        yield {
                            'type': stream_type,
                            'data': decoded,
                            'timestamp': datetime.utcnow().isoformat()
                        }
                    except Exception as e:
                        yield {
                            'type': 'error',
                            'data': f'Decode error: {str(e)}',
                            'timestamp': datetime.utcnow().isoformat()
                        }

            # Stream both stdout and stderr
            async for item in self._merge_async_iters(
                read_stream(process.stdout, 'stdout'),
                read_stream(process.stderr, 'stderr')
            ):
                yield item

            # Wait for process to complete
            try:
                return_code = await asyncio.wait_for(process.wait(), timeout=timeout)
            except asyncio.TimeoutError:
                process.kill()
                await process.wait()
                yield {
                    'type': 'error',
                    'data': f'Process timeout after {timeout}s',
                    'timestamp': datetime.utcnow().isoformat()
                }
                return

            # Send completion message
            duration = (datetime.utcnow() - start_time).total_seconds()
            yield {
                'type': 'complete',
                'return_code': return_code,
                'duration': duration,
                'timestamp': datetime.utcnow().isoformat()
            }

        except Exception as e:
            yield {
                'type': 'error',
                'data': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }

        finally:
            # Cleanup
            if execution_id in self.running_processes:
                del self.running_processes[execution_id]

    async def _merge_async_iters(self, *async_iters):
        """
        Merge multiple async iterators

        Yields items from all iterators as they become available
        """
        queue = asyncio.Queue()
        async def consume(aiter):
            async for item in aiter:
                await queue.put((False, item))
            await queue.put((True, None))

        # Start all consumers
        tasks = [asyncio.create_task(consume(aiter)) for aiter in async_iters]
        finished_count = 0

        # Yield items as they arrive
        while finished_count < len(tasks):
            is_done, item = await queue.get()
            if is_done:
                finished_count += 1
            else:
                yield item

        # Wait for all tasks to complete
        await asyncio.gather(*tasks)

    async def kill(self, execution_id: str):
        """Kill a running process"""
        if execution_id in self.running_processes:
            process = self.running_processes[execution_id]
            process.kill()
            await process.wait()
            del self.running_processes[execution_id]
