#!/usr/bin/env python3
"""
Demo script for Execution Monitor Dashboard
Creates sample execution nodes to demonstrate dashboard functionality
"""

import sys
import asyncio
from pathlib import Path
from datetime import datetime, timedelta

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app.fractal_orchestrator import (
    FractalOrchestrator,
    ExecutionNode,
    ExecutionLevel,
    ExecutionStatus
)


def create_sample_execution_tree(orchestrator: FractalOrchestrator):
    """Create a sample execution tree with multiple levels"""

    print("\n=== Creating Sample Execution Tree ===\n")

    # Root: Strategic AI Agent
    agent_node = ExecutionNode(
        id="agent_strategic_001",
        level=ExecutionLevel.META,
        type="agent",
        name="Strategic Attack Planner",
        status=ExecutionStatus.RUNNING
    )
    agent_node.start_time = datetime.utcnow() - timedelta(minutes=5)
    orchestrator.register_node(agent_node)
    print(f"✓ Created: {agent_node.name} (ID: {agent_node.id})")

    # Exercise 1: Web Application Pentest
    exercise1 = ExecutionNode(
        id="exercise_webapp_001",
        level=ExecutionLevel.EXERCISE,
        type="exercise",
        name="Web Application Penetration Test",
        parent_id=agent_node.id,
        status=ExecutionStatus.RUNNING
    )
    exercise1.start_time = datetime.utcnow() - timedelta(minutes=4)
    orchestrator.register_node(exercise1)
    print(f"  ✓ Created: {exercise1.name} (ID: {exercise1.id})")

    # Chain 1.1: Reconnaissance
    chain1_1 = ExecutionNode(
        id="chain_recon_001",
        level=ExecutionLevel.CHAIN,
        type="chain",
        name="Reconnaissance Chain",
        parent_id=exercise1.id,
        status=ExecutionStatus.COMPLETED
    )
    chain1_1.start_time = datetime.utcnow() - timedelta(minutes=4)
    chain1_1.end_time = datetime.utcnow() - timedelta(minutes=2)
    orchestrator.register_node(chain1_1)
    print(f"    ✓ Created: {chain1_1.name} (ID: {chain1_1.id})")

    # Tool 1.1.1: Nmap
    tool1_1_1 = ExecutionNode(
        id="tool_nmap_001",
        level=ExecutionLevel.TOOL,
        type="tool",
        name="Nmap Port Scan",
        parent_id=chain1_1.id,
        status=ExecutionStatus.COMPLETED
    )
    tool1_1_1.start_time = datetime.utcnow() - timedelta(minutes=4)
    tool1_1_1.end_time = datetime.utcnow() - timedelta(minutes=3)
    tool1_1_1.result = {"ports_found": 5, "services": ["http", "https", "ssh", "mysql", "ftp"]}
    orchestrator.register_node(tool1_1_1)
    print(f"      ✓ Created: {tool1_1_1.name} (ID: {tool1_1_1.id})")

    # Tool 1.1.2: Nikto
    tool1_1_2 = ExecutionNode(
        id="tool_nikto_001",
        level=ExecutionLevel.TOOL,
        type="tool",
        name="Nikto Web Scanner",
        parent_id=chain1_1.id,
        status=ExecutionStatus.COMPLETED
    )
    tool1_1_2.start_time = datetime.utcnow() - timedelta(minutes=3)
    tool1_1_2.end_time = datetime.utcnow() - timedelta(minutes=2)
    tool1_1_2.result = {"vulnerabilities": 3, "severity": "medium"}
    orchestrator.register_node(tool1_1_2)
    print(f"      ✓ Created: {tool1_1_2.name} (ID: {tool1_1_2.id})")

    # Chain 1.2: Exploitation (Running)
    chain1_2 = ExecutionNode(
        id="chain_exploit_001",
        level=ExecutionLevel.CHAIN,
        type="chain",
        name="Exploitation Chain",
        parent_id=exercise1.id,
        status=ExecutionStatus.RUNNING,
        dependencies=[chain1_1.id]  # Depends on recon
    )
    chain1_2.start_time = datetime.utcnow() - timedelta(minutes=2)
    orchestrator.register_node(chain1_2)
    print(f"    ✓ Created: {chain1_2.name} (ID: {chain1_2.id})")

    # Tool 1.2.1: SQLMap (Running)
    tool1_2_1 = ExecutionNode(
        id="tool_sqlmap_001",
        level=ExecutionLevel.TOOL,
        type="tool",
        name="SQLMap SQL Injection",
        parent_id=chain1_2.id,
        status=ExecutionStatus.RUNNING
    )
    tool1_2_1.start_time = datetime.utcnow() - timedelta(minutes=2)
    orchestrator.register_node(tool1_2_1)
    print(f"      ✓ Created: {tool1_2_1.name} (ID: {tool1_2_1.id})")

    # Exercise 2: Network Infrastructure (Pending)
    exercise2 = ExecutionNode(
        id="exercise_network_001",
        level=ExecutionLevel.EXERCISE,
        type="exercise",
        name="Network Infrastructure Assessment",
        parent_id=agent_node.id,
        status=ExecutionStatus.PENDING,
        dependencies=[exercise1.id]  # Depends on webapp exercise
    )
    orchestrator.register_node(exercise2)
    print(f"  ✓ Created: {exercise2.name} (ID: {exercise2.id})")

    # Exercise 3: Failed Example
    exercise3 = ExecutionNode(
        id="exercise_failed_001",
        level=ExecutionLevel.EXERCISE,
        type="exercise",
        name="Database Enumeration",
        parent_id=agent_node.id,
        status=ExecutionStatus.FAILED
    )
    exercise3.start_time = datetime.utcnow() - timedelta(minutes=10)
    exercise3.end_time = datetime.utcnow() - timedelta(minutes=8)
    exercise3.error = "Connection timeout: Unable to reach database server"
    orchestrator.register_node(exercise3)
    print(f"  ✓ Created: {exercise3.name} (ID: {exercise3.id}) - FAILED")

    print(f"\n✓ Created {len(orchestrator.nodes)} nodes in execution tree")
    return orchestrator


def print_execution_tree(orchestrator: FractalOrchestrator):
    """Print the execution tree"""
    print("\n=== Execution Tree Visualization ===\n")
    print(orchestrator.get_execution_tree_visual())


def print_statistics(orchestrator: FractalOrchestrator):
    """Print execution statistics"""
    print("\n=== Execution Statistics ===\n")

    stats = orchestrator._get_stats_by_level()

    for level, data in stats.items():
        print(f"{level.upper()}:")
        print(f"  Total: {data['total']}")
        print(f"  Completed: {data['completed']}")
        print(f"  Running: {data['running']}")
        print(f"  Pending: {data['pending']}")
        print(f"  Failed: {data['failed']}")
        print()


def print_api_response(orchestrator: FractalOrchestrator):
    """Show what the API would return"""
    print("\n=== API Response Simulation ===\n")
    print("GET /api/execution/active\n")

    active_nodes = []
    for node_id, node in orchestrator.nodes.items():
        if node.status in [ExecutionStatus.RUNNING, ExecutionStatus.PENDING]:
            duration = 0
            if node.start_time:
                duration = (datetime.utcnow() - node.start_time).total_seconds()

            progress = 0
            if node.status == ExecutionStatus.RUNNING:
                progress = 50
            elif node.status == ExecutionStatus.COMPLETED:
                progress = 100

            active_nodes.append({
                "id": node.id,
                "type": node.type,
                "status": node.status.value,
                "progress": progress,
                "duration": int(duration),
                "level": node.level.value,
                "nodeCount": len(orchestrator.get_children(node_id))
            })

    import json
    response = {
        "executions": active_nodes,
        "completed_today": 15,
        "avg_duration": 145.5
    }

    print(json.dumps(response, indent=2))


def main():
    """Main demo function"""
    print("\n" + "="*60)
    print("EXECUTION MONITOR DASHBOARD - DEMO")
    print("="*60)

    # Create orchestrator
    orchestrator = FractalOrchestrator()

    # Create sample tree
    create_sample_execution_tree(orchestrator)

    # Print visualizations
    print_execution_tree(orchestrator)
    print_statistics(orchestrator)
    print_api_response(orchestrator)

    # Dashboard access info
    print("\n" + "="*60)
    print("DASHBOARD ACCESS")
    print("="*60)
    print("\n1. Start the server:")
    print("   python -m app.main")
    print("\n2. Access dashboard:")
    print("   http://localhost:8000/execution/monitor")
    print("\n3. The dashboard will display:")
    print("   - Active executions list")
    print("   - Performance metrics")
    print("   - Resource utilization")
    print("   - Execution timeline")
    print("   - Real-time logs")
    print("   - Performance charts")
    print("\n" + "="*60)


if __name__ == "__main__":
    main()
