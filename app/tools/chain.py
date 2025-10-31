"""
Attack Chain Orchestrator - Automated Tool Workflow Execution

Manages sequential and parallel execution of multiple tools with data passing
between stages.
"""

import asyncio
from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import json


class StepStatus(str, Enum):
    """Execution status of a chain step"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class ChainStep:
    """A single step in an attack chain"""
    id: str
    tool: str
    args: Dict[str, Any]
    depends_on: List[str] = field(default_factory=list)  # Step IDs this depends on
    data_mapping: Dict[str, str] = field(default_factory=dict)  # Map data from previous steps
    condition: Optional[str] = None  # Conditional execution (e.g., "prev.success")
    parallel: bool = False  # Can run in parallel with other steps
    on_error: str = "stop"  # 'stop', 'continue', 'skip_remaining'


@dataclass
class ChainDefinition:
    """Complete attack chain definition"""
    id: str
    name: str
    description: str
    steps: List[ChainStep]
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class StepResult:
    """Result of a chain step execution"""
    step_id: str
    status: StepStatus
    tool: str
    output: List[Dict[str, Any]] = field(default_factory=list)  # Raw output lines
    parsed_data: Optional[Dict[str, Any]] = None  # Parsed/structured data
    return_code: Optional[int] = None
    duration: Optional[float] = None
    error: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None


class AttackChainOrchestrator:
    """
    Orchestrates execution of multi-step attack chains
    """

    def __init__(self, tool_executor, tool_registry):
        self.executor = tool_executor
        self.registry = tool_registry
        self.chains: Dict[str, ChainDefinition] = {}
        self.execution_results: Dict[str, List[StepResult]] = {}

    def register_chain(self, chain: ChainDefinition):
        """Register an attack chain"""
        self.chains[chain.id] = chain

    def get_chain(self, chain_id: str) -> Optional[ChainDefinition]:
        """Get chain definition"""
        return self.chains.get(chain_id)

    async def execute_chain(
        self,
        chain_id: str,
        initial_context: Optional[Dict[str, Any]] = None,
        progress_callback: Optional[Callable] = None
    ) -> List[StepResult]:
        """
        Execute an attack chain

        Args:
            chain_id: Chain identifier
            initial_context: Initial context/variables for the chain
            progress_callback: Async callback for progress updates

        Returns:
            List of step results
        """
        chain = self.get_chain(chain_id)
        if not chain:
            raise ValueError(f"Chain '{chain_id}' not found")

        context = initial_context or {}
        results: List[StepResult] = []
        step_outputs: Dict[str, StepResult] = {}  # Map step_id -> result

        # Execute steps in order, respecting dependencies
        for step in chain.steps:
            # Check if dependencies are met
            if not await self._check_dependencies(step, step_outputs):
                result = StepResult(
                    step_id=step.id,
                    status=StepStatus.SKIPPED,
                    tool=step.tool,
                    error="Dependencies not met"
                )
                results.append(result)
                step_outputs[step.id] = result
                continue

            # Check condition if specified
            if step.condition and not self._evaluate_condition(step.condition, step_outputs):
                result = StepResult(
                    step_id=step.id,
                    status=StepStatus.SKIPPED,
                    tool=step.tool,
                    error=f"Condition not met: {step.condition}"
                )
                results.append(result)
                step_outputs[step.id] = result
                continue

            # Resolve arguments with data from previous steps
            resolved_args = self._resolve_arguments(step, step_outputs, context)

            # Build command
            try:
                command = self.registry.build_command(step.tool, resolved_args)
            except Exception as e:
                result = StepResult(
                    step_id=step.id,
                    status=StepStatus.FAILED,
                    tool=step.tool,
                    error=f"Command build failed: {str(e)}"
                )
                results.append(result)
                step_outputs[step.id] = result

                if step.on_error == "stop":
                    break
                continue

            # Execute step
            result = await self._execute_step(step, command, progress_callback)
            results.append(result)
            step_outputs[step.id] = result

            # Handle errors
            if result.status == StepStatus.FAILED:
                if step.on_error == "stop":
                    break
                elif step.on_error == "skip_remaining":
                    # Mark remaining steps as skipped
                    remaining_steps = chain.steps[chain.steps.index(step) + 1:]
                    for remaining in remaining_steps:
                        results.append(StepResult(
                            step_id=remaining.id,
                            status=StepStatus.SKIPPED,
                            tool=remaining.tool,
                            error="Previous step failed"
                        ))
                    break

        # Store results
        execution_id = f"{chain_id}_{datetime.utcnow().isoformat()}"
        self.execution_results[execution_id] = results

        return results

    async def _execute_step(
        self,
        step: ChainStep,
        command: str,
        progress_callback: Optional[Callable]
    ) -> StepResult:
        """Execute a single step"""
        result = StepResult(
            step_id=step.id,
            status=StepStatus.RUNNING,
            tool=step.tool,
            start_time=datetime.utcnow()
        )

        # Notify progress
        if progress_callback:
            await progress_callback({
                'step_id': step.id,
                'status': 'running',
                'tool': step.tool
            })

        try:
            # Stream execution
            async for output in self.executor.execute(command):
                # Store output
                result.output.append(output)

                # Stream to callback
                if progress_callback:
                    await progress_callback({
                        'step_id': step.id,
                        'type': 'output',
                        'data': output
                    })

                # Check for completion
                if output.get('type') == 'complete':
                    result.status = StepStatus.COMPLETED
                    result.return_code = output.get('return_code')
                    result.duration = output.get('duration')
                elif output.get('type') == 'error':
                    result.status = StepStatus.FAILED
                    result.error = output.get('data')

            # Parse output if parser is available
            tool_def = self.registry.get(step.tool)
            if tool_def and tool_def.parser:
                try:
                    raw_output = '\n'.join([
                        line['data'] for line in result.output
                        if line.get('type') in ('stdout', 'stderr')
                    ])
                    result.parsed_data = tool_def.parser(raw_output)
                except Exception as e:
                    # Parsing error doesn't fail the step
                    result.parsed_data = {'parse_error': str(e)}

        except Exception as e:
            result.status = StepStatus.FAILED
            result.error = str(e)

        result.end_time = datetime.utcnow()

        # Final progress notification
        if progress_callback:
            await progress_callback({
                'step_id': step.id,
                'status': result.status,
                'duration': result.duration
            })

        return result

    async def _check_dependencies(
        self,
        step: ChainStep,
        completed_steps: Dict[str, StepResult]
    ) -> bool:
        """Check if step dependencies are satisfied"""
        for dep_id in step.depends_on:
            if dep_id not in completed_steps:
                return False
            if completed_steps[dep_id].status != StepStatus.COMPLETED:
                return False
        return True

    def _evaluate_condition(
        self,
        condition: str,
        step_outputs: Dict[str, StepResult]
    ) -> bool:
        """Evaluate a conditional expression"""
        # Simple condition evaluation
        # Format: "step_id.success" or "step_id.failed"
        if '.' in condition:
            step_id, check = condition.split('.', 1)
            if step_id not in step_outputs:
                return False

            result = step_outputs[step_id]
            if check == 'success':
                return result.status == StepStatus.COMPLETED
            elif check == 'failed':
                return result.status == StepStatus.FAILED

        return True

    def _resolve_arguments(
        self,
        step: ChainStep,
        step_outputs: Dict[str, StepResult],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Resolve step arguments by mapping data from previous steps

        Data mapping format: {"arg_name": "step_id.field_path"}
        Example: {"target": "nmap_scan.parsed_data.hosts[0]"}
        """
        resolved = dict(step.args)

        for arg_name, data_path in step.data_mapping.items():
            if '.' not in data_path:
                # Simple context variable
                if data_path in context:
                    resolved[arg_name] = context[data_path]
                continue

            # Parse data path: step_id.field.subfield
            parts = data_path.split('.')
            step_id = parts[0]

            if step_id not in step_outputs:
                continue

            # Navigate the data structure
            data = step_outputs[step_id].parsed_data
            if not data:
                continue

            try:
                for part in parts[1:]:
                    # Handle array indexing
                    if '[' in part:
                        field, index = part.split('[')
                        index = int(index.rstrip(']'))
                        data = data[field][index]
                    else:
                        data = data[part]

                resolved[arg_name] = data
            except (KeyError, IndexError, TypeError):
                # Data path not found, keep original value
                pass

        return resolved


# Example chain definitions

WEB_RECON_CHAIN = ChainDefinition(
    id="web_recon",
    name="Web Application Reconnaissance",
    description="Comprehensive web app reconnaissance and vulnerability scanning",
    steps=[
        ChainStep(
            id="nmap_scan",
            tool="nmap",
            args={"-p": "80,443,8080,8443", "-sV": True, "-sC": True},
            data_mapping={"target": "target_url"}
        ),
        ChainStep(
            id="nikto_scan",
            tool="nikto",
            args={},
            depends_on=["nmap_scan"],
            data_mapping={"-h": "target_url"},
            condition="nmap_scan.success"
        ),
        ChainStep(
            id="dir_bruteforce",
            tool="gobuster",
            args={"-w": "/usr/share/wordlists/dirb/common.txt"},
            depends_on=["nmap_scan"],
            data_mapping={"-u": "target_url"},
            parallel=True
        ),
        ChainStep(
            id="sql_injection",
            tool="sqlmap",
            args={"--dbs": True, "--batch": True},
            depends_on=["nikto_scan", "dir_bruteforce"],
            data_mapping={"-u": "target_url"},
            on_error="continue"
        )
    ]
)
