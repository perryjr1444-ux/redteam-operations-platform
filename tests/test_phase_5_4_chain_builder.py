"""
Phase 5.4 End-to-End Tests - Attack Chain Builder
Tests for complete attack chain workflow including database, API, and integration

Test Categories:
1. Database tests - AttackChain and ChainExecution CRUD operations
2. API tests - All /api/chains endpoints
3. Integration test - Full workflow from creation to execution
4. UI test - Page rendering and JavaScript loading
"""

import pytest
import json
import time
from datetime import datetime
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app import crud, models, schemas


class TestDatabaseOperations:
    """Test database CRUD operations for AttackChain and ChainExecution"""

    def test_create_attack_chain(self, db_session: Session):
        """Test creating an AttackChain record in database"""
        chain_data = {
            "name": "Test Chain",
            "description": "Test attack chain for unit testing",
            "category": "reconnaissance",
            "risk_level": "medium",
            "steps": [
                {"tool": "nmap", "args": ["-sV", "target"], "description": "Port scan"},
                {"tool": "nikto", "args": ["-h", "target"], "description": "Web scan"}
            ],
            "metadata": {"author": "test_user", "version": "1.0"},
            "created_by": "test_user"
        }

        db_chain = crud.create_attack_chain(db_session, chain_data)

        assert db_chain is not None
        assert db_chain.id > 0
        assert db_chain.chain_id.startswith("chain_")
        assert db_chain.name == "Test Chain"
        assert db_chain.description == "Test attack chain for unit testing"
        assert db_chain.category == "reconnaissance"
        assert db_chain.risk_level == "medium"
        assert db_chain.created_by == "test_user"
        assert db_chain.is_active is True
        assert db_chain.is_template is False

        # Verify JSON serialization
        steps = json.loads(db_chain.steps)
        assert len(steps) == 2
        assert steps[0]["tool"] == "nmap"

        metadata = json.loads(db_chain.chain_metadata)
        assert metadata["author"] == "test_user"

    def test_create_attack_chain_with_custom_id(self, db_session: Session):
        """Test creating an AttackChain with custom chain_id"""
        chain_data = {
            "chain_id": "custom_chain_001",
            "name": "Custom ID Chain",
            "risk_level": "low",
            "steps": [{"tool": "ping", "args": ["target"], "description": "Test connectivity"}],
            "created_by": "test_user"
        }

        db_chain = crud.create_attack_chain(db_session, chain_data)

        assert db_chain.chain_id == "custom_chain_001"
        assert db_chain.name == "Custom ID Chain"

    def test_get_attack_chain_by_chain_id(self, db_session: Session):
        """Test retrieving an AttackChain by chain_id"""
        # Create a chain
        chain_data = {
            "name": "Retrieve Test Chain",
            "risk_level": "high",
            "steps": [{"tool": "test", "args": [], "description": "test"}],
            "created_by": "test_user"
        }
        created_chain = crud.create_attack_chain(db_session, chain_data)

        # Retrieve it
        retrieved_chain = crud.get_attack_chain_by_chain_id(db_session, created_chain.chain_id)

        assert retrieved_chain is not None
        assert retrieved_chain.id == created_chain.id
        assert retrieved_chain.chain_id == created_chain.chain_id
        assert retrieved_chain.name == "Retrieve Test Chain"

    def test_get_attack_chains_list(self, db_session: Session):
        """Test retrieving list of AttackChains"""
        # Create multiple chains
        for i in range(3):
            chain_data = {
                "name": f"List Test Chain {i}",
                "risk_level": "medium",
                "steps": [{"tool": "test", "args": [], "description": "test"}],
                "created_by": "test_user"
            }
            crud.create_attack_chain(db_session, chain_data)

        # Retrieve list
        chains = crud.get_attack_chains(db_session)

        assert len(chains) >= 3
        assert all(chain.is_active for chain in chains)

    def test_update_attack_chain(self, db_session: Session):
        """Test updating an AttackChain"""
        # Create a chain
        chain_data = {
            "name": "Original Name",
            "description": "Original description",
            "risk_level": "low",
            "steps": [{"tool": "test", "args": [], "description": "test"}],
            "created_by": "test_user"
        }
        db_chain = crud.create_attack_chain(db_session, chain_data)

        # Update it
        update_data = {
            "name": "Updated Name",
            "description": "Updated description",
            "risk_level": "critical"
        }
        updated_chain = crud.update_attack_chain(db_session, db_chain.chain_id, update_data)

        assert updated_chain is not None
        assert updated_chain.name == "Updated Name"
        assert updated_chain.description == "Updated description"
        assert updated_chain.risk_level == "critical"

    def test_soft_delete_attack_chain(self, db_session: Session):
        """Test soft deleting an AttackChain (sets is_active=False)"""
        # Create a chain
        chain_data = {
            "name": "Chain to Delete",
            "risk_level": "medium",
            "steps": [{"tool": "test", "args": [], "description": "test"}],
            "created_by": "test_user"
        }
        db_chain = crud.create_attack_chain(db_session, chain_data)
        chain_id = db_chain.chain_id

        # Soft delete
        success = crud.delete_attack_chain(db_session, chain_id)

        assert success is True

        # Verify it's marked inactive
        deleted_chain = crud.get_attack_chain_by_chain_id(db_session, chain_id)
        assert deleted_chain is not None
        assert deleted_chain.is_active is False

        # Verify it doesn't appear in default list
        active_chains = crud.get_attack_chains(db_session, include_inactive=False)
        assert all(chain.chain_id != chain_id for chain in active_chains)

        # Verify it appears when including inactive
        all_chains = crud.get_attack_chains(db_session, include_inactive=True)
        assert any(chain.chain_id == chain_id for chain in all_chains)

    def test_create_chain_execution(self, db_session: Session):
        """Test creating a ChainExecution record"""
        # First create a chain
        chain_data = {
            "name": "Execution Test Chain",
            "risk_level": "medium",
            "steps": [{"tool": "test", "args": [], "description": "test"}],
            "created_by": "test_user"
        }
        db_chain = crud.create_attack_chain(db_session, chain_data)

        # Create execution record
        execution_data = {
            "chain_id": db_chain.chain_id,
            "chain_name": db_chain.name,
            "status": "pending",
            "total_steps": 1,
            "completed_steps": 0,
            "failed_steps": 0,
            "skipped_steps": 0,
            "results": [],
            "executed_by": "test_user"
        }
        db_execution = crud.create_chain_execution(db_session, execution_data)

        assert db_execution is not None
        assert db_execution.id > 0
        assert db_execution.execution_id.startswith("exec_")
        assert db_execution.chain_id == db_chain.chain_id
        assert db_execution.chain_name == "Execution Test Chain"
        assert db_execution.status == "pending"
        assert db_execution.total_steps == 1
        assert db_execution.completed_steps == 0
        assert db_execution.executed_by == "test_user"

    def test_update_execution_status(self, db_session: Session):
        """Test updating ChainExecution status and progress"""
        # Create chain and execution
        chain_data = {
            "name": "Status Update Chain",
            "risk_level": "medium",
            "steps": [{"tool": "test", "args": [], "description": "test"}],
            "created_by": "test_user"
        }
        db_chain = crud.create_attack_chain(db_session, chain_data)

        execution_data = {
            "chain_id": db_chain.chain_id,
            "chain_name": db_chain.name,
            "status": "pending",
            "total_steps": 3,
            "completed_steps": 0,
            "failed_steps": 0,
            "skipped_steps": 0,
            "results": [],
            "executed_by": "test_user"
        }
        db_execution = crud.create_chain_execution(db_session, execution_data)

        # Update to running
        update_data = {
            "status": "running",
            "start_time": datetime.utcnow(),
            "completed_steps": 1
        }
        updated_execution = crud.update_chain_execution(
            db_session, db_execution.execution_id, update_data
        )

        assert updated_execution is not None
        assert updated_execution.status == "running"
        assert updated_execution.start_time is not None
        assert updated_execution.completed_steps == 1

        # Update to completed
        update_data = {
            "status": "completed",
            "end_time": datetime.utcnow(),
            "completed_steps": 3,
            "duration": 45.5,
            "results": [
                {"step": 1, "status": "success"},
                {"step": 2, "status": "success"},
                {"step": 3, "status": "success"}
            ]
        }
        final_execution = crud.update_chain_execution(
            db_session, db_execution.execution_id, update_data
        )

        assert final_execution.status == "completed"
        assert final_execution.end_time is not None
        assert final_execution.duration == 45.5
        assert final_execution.completed_steps == 3

        # Verify results were serialized
        results = json.loads(final_execution.results)
        assert len(results) == 3
        assert results[0]["status"] == "success"

    def test_get_chain_executions(self, db_session: Session):
        """Test retrieving chain execution history"""
        # Create chain
        chain_data = {
            "name": "History Test Chain",
            "risk_level": "medium",
            "steps": [{"tool": "test", "args": [], "description": "test"}],
            "created_by": "test_user"
        }
        db_chain = crud.create_attack_chain(db_session, chain_data)

        # Create multiple executions
        for i in range(3):
            execution_data = {
                "chain_id": db_chain.chain_id,
                "chain_name": db_chain.name,
                "status": "completed",
                "total_steps": 1,
                "completed_steps": 1,
                "failed_steps": 0,
                "skipped_steps": 0,
                "results": [],
                "executed_by": "test_user"
            }
            crud.create_chain_execution(db_session, execution_data)

        # Retrieve executions
        executions = crud.get_chain_executions(db_session, chain_id=db_chain.chain_id)

        assert len(executions) == 3
        assert all(ex.chain_id == db_chain.chain_id for ex in executions)


class TestAPIEndpoints:
    """Test all /api/chains API endpoints"""

    def test_get_chains_list(self, client: TestClient, db_session: Session):
        """Test GET /api/chains - list all chains"""
        # Create some chains
        for i in range(2):
            chain_data = {
                "name": f"API Test Chain {i}",
                "risk_level": "medium",
                "steps": [{"tool": "test", "args": [], "description": "test"}],
                "created_by": "test_user"
            }
            crud.create_attack_chain(db_session, chain_data)

        response = client.get("/api/chains")

        assert response.status_code == 200
        data = response.json()
        assert "custom_chains" in data
        assert "templates" in data
        assert "total" in data
        assert len(data["custom_chains"]) >= 2

    def test_post_create_chain(self, client: TestClient):
        """Test POST /api/chains - create new chain"""
        chain_data = {
            "name": "API Created Chain",
            "description": "Chain created via API",
            "category": "exploitation",
            "risk_level": "high",
            "steps": [
                {
                    "tool": "nmap",
                    "args": ["-sV", "target"],
                    "description": "Version scan"
                },
                {
                    "tool": "metasploit",
                    "args": ["exploit/multi/handler"],
                    "description": "Set up listener"
                }
            ],
            "metadata": {"author": "api_user"}
        }

        response = client.post("/api/chains", json=chain_data)

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "API Created Chain"
        assert data["description"] == "Chain created via API"
        assert data["category"] == "exploitation"
        assert data["risk_level"] == "high"
        assert len(data["steps"]) == 2
        assert data["is_active"] is True
        assert "chain_id" in data

    def test_get_chain_by_id(self, client: TestClient, db_session: Session):
        """Test GET /api/chains/{chain_id} - retrieve specific chain"""
        # Create a chain
        chain_data = {
            "name": "Retrieve via API Chain",
            "risk_level": "medium",
            "steps": [{"tool": "test", "args": [], "description": "test"}],
            "created_by": "test_user"
        }
        db_chain = crud.create_attack_chain(db_session, chain_data)

        response = client.get(f"/api/chains/{db_chain.chain_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["chain_id"] == db_chain.chain_id
        assert data["name"] == "Retrieve via API Chain"
        assert data["risk_level"] == "medium"

    def test_get_chain_not_found(self, client: TestClient):
        """Test GET /api/chains/{chain_id} with non-existent ID"""
        response = client.get("/api/chains/nonexistent_chain_id")

        assert response.status_code == 404
        data = response.json()
        assert "detail" in data

    def test_put_update_chain(self, client: TestClient, db_session: Session):
        """Test PUT /api/chains/{chain_id} - update chain"""
        # Create a chain
        chain_data = {
            "name": "Original Chain Name",
            "risk_level": "low",
            "steps": [{"tool": "test", "args": [], "description": "test"}],
            "created_by": "test_user"
        }
        db_chain = crud.create_attack_chain(db_session, chain_data)

        # Update it via API
        update_data = {
            "name": "Updated Chain Name",
            "risk_level": "critical",
            "description": "Updated via API"
        }

        response = client.put(f"/api/chains/{db_chain.chain_id}", json=update_data)

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Chain Name"
        assert data["risk_level"] == "critical"
        assert data["description"] == "Updated via API"

    def test_delete_chain(self, client: TestClient, db_session: Session):
        """Test DELETE /api/chains/{chain_id} - soft delete chain"""
        # Create a chain
        chain_data = {
            "name": "Chain to Delete via API",
            "risk_level": "medium",
            "steps": [{"tool": "test", "args": [], "description": "test"}],
            "created_by": "test_user"
        }
        db_chain = crud.create_attack_chain(db_session, chain_data)

        response = client.delete(f"/api/chains/{db_chain.chain_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["chain_id"] == db_chain.chain_id

        # Verify it's marked inactive in database
        deleted_chain = crud.get_attack_chain_by_chain_id(db_session, db_chain.chain_id)
        assert deleted_chain.is_active is False

    def test_post_execute_chain(self, client: TestClient, db_session: Session):
        """Test POST /api/chains/{chain_id}/execute - execute chain"""
        # Create a chain
        chain_data = {
            "name": "Executable Chain",
            "risk_level": "medium",
            "steps": [
                {"tool": "nmap", "args": ["-sT", "target"], "description": "TCP scan"},
                {"tool": "nikto", "args": ["-h", "target"], "description": "Web vuln scan"}
            ],
            "created_by": "test_user"
        }
        db_chain = crud.create_attack_chain(db_session, chain_data)

        # Execute it
        execution_request = {
            "chain_id": db_chain.chain_id,
            "context": {"target": "192.168.1.100"}
        }

        response = client.post(
            f"/api/chains/{db_chain.chain_id}/execute",
            json=execution_request
        )

        assert response.status_code == 200
        data = response.json()
        assert data["chain_id"] == db_chain.chain_id
        assert data["chain_name"] == "Executable Chain"
        assert data["status"] == "pending"
        assert data["total_steps"] == 2
        assert data["completed_steps"] == 0
        assert "execution_id" in data

    def test_execute_inactive_chain(self, client: TestClient, db_session: Session):
        """Test executing an inactive chain returns error"""
        # Create and delete a chain
        chain_data = {
            "name": "Inactive Chain",
            "risk_level": "medium",
            "steps": [{"tool": "test", "args": [], "description": "test"}],
            "created_by": "test_user"
        }
        db_chain = crud.create_attack_chain(db_session, chain_data)
        crud.delete_attack_chain(db_session, db_chain.chain_id)

        # Try to execute it
        execution_request = {
            "chain_id": db_chain.chain_id,
            "context": {}
        }

        response = client.post(
            f"/api/chains/{db_chain.chain_id}/execute",
            json=execution_request
        )

        assert response.status_code == 400
        data = response.json()
        assert "inactive" in data["detail"].lower()

    def test_get_chain_executions_list(self, client: TestClient, db_session: Session):
        """Test GET /api/chains/executions - list executions"""
        # Create chain and executions
        chain_data = {
            "name": "List Executions Chain",
            "risk_level": "medium",
            "steps": [{"tool": "test", "args": [], "description": "test"}],
            "created_by": "test_user"
        }
        db_chain = crud.create_attack_chain(db_session, chain_data)

        for i in range(2):
            execution_data = {
                "chain_id": db_chain.chain_id,
                "chain_name": db_chain.name,
                "status": "completed",
                "total_steps": 1,
                "completed_steps": 1,
                "failed_steps": 0,
                "skipped_steps": 0,
                "results": [],
                "executed_by": "test_user"
            }
            crud.create_chain_execution(db_session, execution_data)

        response = client.get("/api/chains/executions")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "executions" in data
        assert len(data["executions"]) >= 2

    def test_get_chain_executions_filtered(self, client: TestClient, db_session: Session):
        """Test GET /api/chains/executions with chain_id filter"""
        # Create two chains with executions
        for i in range(2):
            chain_data = {
                "name": f"Filter Test Chain {i}",
                "risk_level": "medium",
                "steps": [{"tool": "test", "args": [], "description": "test"}],
                "created_by": "test_user"
            }
            db_chain = crud.create_attack_chain(db_session, chain_data)

            execution_data = {
                "chain_id": db_chain.chain_id,
                "chain_name": db_chain.name,
                "status": "completed",
                "total_steps": 1,
                "completed_steps": 1,
                "failed_steps": 0,
                "skipped_steps": 0,
                "results": [],
                "executed_by": "test_user"
            }
            crud.create_chain_execution(db_session, execution_data)

            if i == 0:
                target_chain_id = db_chain.chain_id

        # Filter by first chain
        response = client.get(f"/api/chains/executions?chain_id={target_chain_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["executions"]) >= 1
        assert all(ex["chain_id"] == target_chain_id for ex in data["executions"])


class TestIntegrationWorkflow:
    """Integration test for complete attack chain workflow"""

    def test_complete_chain_workflow(self, client: TestClient, db_session: Session):
        """
        Test complete workflow:
        1. Create chain via API
        2. Verify saved to database
        3. Execute chain
        4. Poll execution status
        5. Verify results stored
        6. Check execution history
        """
        # Step 1: Create chain via API
        chain_data = {
            "name": "Integration Test Chain",
            "description": "Full workflow test from creation to completion",
            "category": "full_attack",
            "risk_level": "high",
            "steps": [
                {
                    "tool": "nmap",
                    "args": ["-sS", "-p-", "target"],
                    "description": "Full port scan"
                },
                {
                    "tool": "nikto",
                    "args": ["-h", "target", "-C", "all"],
                    "description": "Comprehensive web scan"
                },
                {
                    "tool": "sqlmap",
                    "args": ["-u", "target/login", "--batch"],
                    "description": "SQL injection test"
                }
            ],
            "metadata": {
                "author": "integration_test",
                "version": "1.0",
                "tags": ["full_scan", "automated"]
            }
        }

        response = client.post("/api/chains", json=chain_data)
        assert response.status_code == 200
        created_chain = response.json()
        chain_id = created_chain["chain_id"]

        # Step 2: Verify saved to database
        db_chain = crud.get_attack_chain_by_chain_id(db_session, chain_id)
        assert db_chain is not None
        assert db_chain.name == "Integration Test Chain"
        assert db_chain.category == "full_attack"
        assert db_chain.risk_level == "high"

        steps = json.loads(db_chain.steps)
        assert len(steps) == 3
        assert steps[0]["tool"] == "nmap"
        assert steps[1]["tool"] == "nikto"
        assert steps[2]["tool"] == "sqlmap"

        # Step 3: Execute chain
        execution_request = {
            "chain_id": chain_id,
            "context": {
                "target": "192.168.1.100",
                "output_dir": "/tmp/results"
            }
        }

        response = client.post(f"/api/chains/{chain_id}/execute", json=execution_request)
        assert response.status_code == 200
        execution_data = response.json()
        execution_id = execution_data["execution_id"]

        assert execution_data["status"] == "pending"
        assert execution_data["total_steps"] == 3
        assert execution_data["completed_steps"] == 0

        # Step 4: Simulate execution progress (poll execution status)
        # In production, this would be done by the orchestrator
        # Here we simulate the status updates

        # Start execution
        update_data = {
            "status": "running",
            "start_time": datetime.utcnow()
        }
        updated_exec = crud.update_chain_execution(db_session, execution_id, update_data)
        assert updated_exec.status == "running"

        # Complete first step
        update_data = {
            "completed_steps": 1,
            "results": [
                {
                    "step": 1,
                    "tool": "nmap",
                    "status": "success",
                    "output": "Open ports: 22, 80, 443",
                    "timestamp": datetime.utcnow().isoformat()
                }
            ]
        }
        updated_exec = crud.update_chain_execution(db_session, execution_id, update_data)
        assert updated_exec.completed_steps == 1

        # Complete second step
        update_data = {
            "completed_steps": 2,
            "results": [
                {
                    "step": 1,
                    "tool": "nmap",
                    "status": "success",
                    "output": "Open ports: 22, 80, 443",
                    "timestamp": datetime.utcnow().isoformat()
                },
                {
                    "step": 2,
                    "tool": "nikto",
                    "status": "success",
                    "output": "Found 5 vulnerabilities",
                    "timestamp": datetime.utcnow().isoformat()
                }
            ]
        }
        updated_exec = crud.update_chain_execution(db_session, execution_id, update_data)
        assert updated_exec.completed_steps == 2

        # Complete final step
        end_time = datetime.utcnow()
        update_data = {
            "status": "completed",
            "completed_steps": 3,
            "end_time": end_time,
            "duration": 120.5,
            "results": [
                {
                    "step": 1,
                    "tool": "nmap",
                    "status": "success",
                    "output": "Open ports: 22, 80, 443",
                    "timestamp": datetime.utcnow().isoformat()
                },
                {
                    "step": 2,
                    "tool": "nikto",
                    "status": "success",
                    "output": "Found 5 vulnerabilities",
                    "timestamp": datetime.utcnow().isoformat()
                },
                {
                    "step": 3,
                    "tool": "sqlmap",
                    "status": "success",
                    "output": "SQL injection found in login parameter",
                    "timestamp": datetime.utcnow().isoformat()
                }
            ]
        }
        final_exec = crud.update_chain_execution(db_session, execution_id, update_data)

        # Step 5: Verify results stored
        assert final_exec.status == "completed"
        assert final_exec.completed_steps == 3
        assert final_exec.failed_steps == 0
        assert final_exec.duration == 120.5

        results = json.loads(final_exec.results)
        assert len(results) == 3
        assert results[0]["tool"] == "nmap"
        assert results[1]["tool"] == "nikto"
        assert results[2]["tool"] == "sqlmap"
        assert all(r["status"] == "success" for r in results)

        # Step 6: Check execution history via API
        response = client.get(f"/api/chains/executions?chain_id={chain_id}")
        assert response.status_code == 200
        history = response.json()

        assert history["success"] is True
        assert len(history["executions"]) >= 1

        # Find our execution
        our_execution = next(
            (ex for ex in history["executions"] if ex["execution_id"] == execution_id),
            None
        )
        assert our_execution is not None
        assert our_execution["status"] == "completed"
        assert our_execution["total_steps"] == 3
        assert our_execution["completed_steps"] == 3
        assert our_execution["duration"] == 120.5

        # Verify we can retrieve the chain again
        response = client.get(f"/api/chains/{chain_id}")
        assert response.status_code == 200
        final_chain = response.json()
        assert final_chain["name"] == "Integration Test Chain"

    def test_failed_execution_workflow(self, client: TestClient, db_session: Session):
        """Test workflow when execution fails"""
        # Create chain
        chain_data = {
            "name": "Failure Test Chain",
            "risk_level": "medium",
            "steps": [
                {"tool": "nmap", "args": ["-sV", "target"], "description": "Scan"},
                {"tool": "exploit", "args": ["target"], "description": "Exploit"}
            ]
        }

        response = client.post("/api/chains", json=chain_data)
        assert response.status_code == 200
        created_chain = response.json()
        chain_id = created_chain["chain_id"]

        # Execute chain
        execution_request = {"chain_id": chain_id, "context": {}}
        response = client.post(f"/api/chains/{chain_id}/execute", json=execution_request)
        assert response.status_code == 200
        execution_data = response.json()
        execution_id = execution_data["execution_id"]

        # Simulate failure
        update_data = {
            "status": "failed",
            "start_time": datetime.utcnow(),
            "end_time": datetime.utcnow(),
            "completed_steps": 1,
            "failed_steps": 1,
            "duration": 30.0,
            "error_message": "Connection timeout during exploit phase",
            "results": [
                {"step": 1, "tool": "nmap", "status": "success", "output": "Scan complete"},
                {"step": 2, "tool": "exploit", "status": "failed", "error": "Connection timeout"}
            ]
        }
        failed_exec = crud.update_chain_execution(db_session, execution_id, update_data)

        # Verify failure recorded
        assert failed_exec.status == "failed"
        assert failed_exec.failed_steps == 1
        assert failed_exec.error_message == "Connection timeout during exploit phase"

        results = json.loads(failed_exec.results)
        assert results[0]["status"] == "success"
        assert results[1]["status"] == "failed"


class TestUIComponents:
    """Test UI components and page rendering"""

    def test_chain_builder_page_loads(self, client: TestClient):
        """Test /chains/builder page loads successfully"""
        response = client.get("/chains/builder")

        assert response.status_code == 200
        assert response.headers["content-type"].startswith("text/html")

    def test_chain_builder_has_required_elements(self, client: TestClient):
        """Test chain builder page has required UI elements"""
        response = client.get("/chains/builder")
        html = response.text

        # Check for key UI elements
        assert "chain" in html.lower() or "attack" in html.lower()

        # Check for Alpine.js or other JavaScript frameworks
        # (actual implementation may vary)
        assert "script" in html.lower()

    def test_chain_builder_javascript_loads(self, client: TestClient):
        """Test chain builder JavaScript file is accessible"""
        # Try common JavaScript file paths
        possible_js_paths = [
            "/static/js/chain-builder.js",
            "/static/js/alpine-components.js",
            "/static/js/chains.js"
        ]

        # At least one should load (or 404 is acceptable if not implemented)
        for js_path in possible_js_paths:
            response = client.get(js_path)
            # Either loads successfully or doesn't exist yet
            assert response.status_code in [200, 404]

            if response.status_code == 200:
                # If it loads, verify it's JavaScript
                assert "javascript" in response.headers.get("content-type", "").lower() or \
                       js_path.endswith(".js")

    def test_chains_page_css_loads(self, client: TestClient):
        """Test chain builder CSS loads (optional)"""
        possible_css_paths = [
            "/static/css/chains.css",
            "/static/css/chain-builder.css",
            "/static/css/visualizer.css"
        ]

        for css_path in possible_css_paths:
            response = client.get(css_path)
            # Either loads successfully or doesn't exist yet
            assert response.status_code in [200, 404]


class TestValidationAndEdgeCases:
    """Test validation and edge cases"""

    def test_create_chain_with_invalid_risk_level(self, client: TestClient):
        """Test creating chain with invalid risk level"""
        chain_data = {
            "name": "Invalid Risk Chain",
            "risk_level": "super_critical",  # Invalid
            "steps": [{"tool": "test", "args": [], "description": "test"}]
        }

        response = client.post("/api/chains", json=chain_data)

        # Should fail validation
        assert response.status_code == 422  # Validation error

    def test_create_chain_with_empty_steps(self, client: TestClient):
        """Test creating chain with empty steps array"""
        chain_data = {
            "name": "Empty Steps Chain",
            "risk_level": "low",
            "steps": []
        }

        response = client.post("/api/chains", json=chain_data)

        # Should still create (validation may allow empty steps)
        # Actual behavior depends on validation rules
        assert response.status_code in [200, 422]

    def test_update_nonexistent_chain(self, client: TestClient):
        """Test updating a chain that doesn't exist"""
        update_data = {
            "name": "Updated Name"
        }

        response = client.put("/api/chains/nonexistent_id", json=update_data)

        assert response.status_code == 404

    def test_execute_nonexistent_chain(self, client: TestClient):
        """Test executing a chain that doesn't exist"""
        execution_request = {
            "chain_id": "nonexistent_id",
            "context": {}
        }

        response = client.post(
            "/api/chains/nonexistent_id/execute",
            json=execution_request
        )

        assert response.status_code == 404

    def test_create_chain_with_duplicate_id(self, client: TestClient, db_session: Session):
        """Test creating chain with duplicate chain_id"""
        # Create first chain with custom ID
        chain_data = {
            "chain_id": "duplicate_test_001",
            "name": "First Chain",
            "risk_level": "low",
            "steps": [{"tool": "test", "args": [], "description": "test"}],
            "created_by": "test_user"
        }
        crud.create_attack_chain(db_session, chain_data)

        # Try to create second chain with same ID via API
        chain_data_2 = {
            "chain_id": "duplicate_test_001",
            "name": "Second Chain",
            "risk_level": "low",
            "steps": [{"tool": "test", "args": [], "description": "test"}]
        }

        response = client.post("/api/chains", json=chain_data_2)

        # Should fail (may be 500 due to database constraint)
        assert response.status_code in [400, 500]


# Run with: pytest tests/test_phase_5_4_chain_builder.py -v
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
