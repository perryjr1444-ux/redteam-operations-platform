
from sqlalchemy.orm import Session
from . import models
from datetime import datetime
import json
import uuid

# --- Template CRUD ---
def get_template_by_template_id(db: Session, template_id: str):
    return db.query(models.Template).filter(models.Template.template_id == template_id).first()

def get_templates(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Template).offset(skip).limit(limit).all()

def create_template(db: Session, template: dict):
    db_template = models.Template(**template)
    db.add(db_template)
    db.commit()
    db.refresh(db_template)
    return db_template

# --- Exercise CRUD ---
def get_exercises(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Exercise).offset(skip).limit(limit).all()

def get_exercise_by_exercise_id(db: Session, exercise_id: str):
    return db.query(models.Exercise).filter(models.Exercise.exercise_id == exercise_id).first()

def create_exercise(db: Session, exercise: dict):
    db_exercise = models.Exercise(**exercise)
    db.add(db_exercise)
    db.commit()
    db.refresh(db_exercise)
    return db_exercise

# --- Attack Container CRUD ---
def get_attack_containers(db: Session, exercise_id: str = None, skip: int = 0, limit: int = 100):
    query = db.query(models.AttackContainer)
    if exercise_id:
        query = query.filter(models.AttackContainer.exercise_id == exercise_id)
    return query.order_by(models.AttackContainer.created_at.desc()).offset(skip).limit(limit).all()

def get_attack_container_by_id(db: Session, container_id: str):
    return db.query(models.AttackContainer).filter(
        models.AttackContainer.container_id == container_id
    ).first()

def create_attack_container(db: Session, container_data: dict):
    db_container = models.AttackContainer(**container_data)
    db.add(db_container)
    db.commit()
    db.refresh(db_container)
    return db_container

def update_attack_container_status(db: Session, container_id: str, status: str):
    container = get_attack_container_by_id(db, container_id)
    if container:
        container.status = status
        if status in ["stopped", "exited"]:
            container.stopped_at = datetime.utcnow()
        db.commit()
        db.refresh(container)
    return container

def delete_attack_container(db: Session, container_id: str):
    container = get_attack_container_by_id(db, container_id)
    if container:
        db.delete(container)
        db.commit()
        return True
    return False


# --- Attack Chain CRUD ---
def get_attack_chains(db: Session, skip: int = 0, limit: int = 100, include_inactive: bool = False):
    """Get all attack chains"""
    query = db.query(models.AttackChain)
    if not include_inactive:
        query = query.filter(models.AttackChain.is_active == True)
    return query.order_by(models.AttackChain.created_at.desc()).offset(skip).limit(limit).all()


def get_attack_chain_by_chain_id(db: Session, chain_id: str):
    """Get attack chain by chain_id"""
    return db.query(models.AttackChain).filter(models.AttackChain.chain_id == chain_id).first()


def create_attack_chain(db: Session, chain_data: dict):
    """Create new attack chain"""
    # Generate chain_id if not provided
    if "chain_id" not in chain_data or not chain_data["chain_id"]:
        chain_data["chain_id"] = f"chain_{uuid.uuid4().hex[:12]}"

    # Serialize steps to JSON
    if "steps" in chain_data:
        chain_data["steps"] = json.dumps(chain_data["steps"])

    # Serialize metadata to JSON if present
    if "metadata" in chain_data and chain_data["metadata"]:
        chain_data["chain_metadata"] = json.dumps(chain_data["metadata"])
        del chain_data["metadata"]

    db_chain = models.AttackChain(**chain_data)
    db.add(db_chain)
    db.commit()
    db.refresh(db_chain)
    return db_chain


def update_attack_chain(db: Session, chain_id: str, chain_data: dict):
    """Update attack chain"""
    chain = get_attack_chain_by_chain_id(db, chain_id)
    if not chain:
        return None

    # Serialize steps to JSON if provided
    if "steps" in chain_data:
        chain_data["steps"] = json.dumps(chain_data["steps"])

    # Serialize metadata to JSON if provided
    if "metadata" in chain_data and chain_data["metadata"]:
        chain_data["chain_metadata"] = json.dumps(chain_data["metadata"])
        del chain_data["metadata"]

    for key, value in chain_data.items():
        if hasattr(chain, key) and value is not None:
            setattr(chain, key, value)

    db.commit()
    db.refresh(chain)
    return chain


def delete_attack_chain(db: Session, chain_id: str):
    """Delete attack chain (soft delete by setting is_active=False)"""
    chain = get_attack_chain_by_chain_id(db, chain_id)
    if chain:
        chain.is_active = False
        db.commit()
        return True
    return False


# --- Chain Execution CRUD ---
def get_chain_executions(db: Session, chain_id: str = None, skip: int = 0, limit: int = 100):
    """Get chain executions"""
    query = db.query(models.ChainExecution)
    if chain_id:
        query = query.filter(models.ChainExecution.chain_id == chain_id)
    return query.order_by(models.ChainExecution.created_at.desc()).offset(skip).limit(limit).all()


def get_chain_execution_by_id(db: Session, execution_id: str):
    """Get chain execution by execution_id"""
    return db.query(models.ChainExecution).filter(
        models.ChainExecution.execution_id == execution_id
    ).first()


def create_chain_execution(db: Session, execution_data: dict):
    """Create new chain execution record"""
    # Generate execution_id if not provided
    if "execution_id" not in execution_data or not execution_data["execution_id"]:
        execution_data["execution_id"] = f"exec_{uuid.uuid4().hex[:12]}"

    # Serialize results to JSON if it's a list or dict
    if "results" in execution_data and execution_data["results"] is not None:
        if isinstance(execution_data["results"], (list, dict)):
            execution_data["results"] = json.dumps(execution_data["results"])

    db_execution = models.ChainExecution(**execution_data)
    db.add(db_execution)
    db.commit()
    db.refresh(db_execution)
    return db_execution


def update_chain_execution(db: Session, execution_id: str, execution_data: dict):
    """Update chain execution"""
    execution = get_chain_execution_by_id(db, execution_id)
    if not execution:
        return None

    # Serialize results to JSON if it's a list or dict
    if "results" in execution_data and execution_data["results"] is not None:
        if isinstance(execution_data["results"], (list, dict)):
            execution_data["results"] = json.dumps(execution_data["results"])

    for key, value in execution_data.items():
        if hasattr(execution, key) and value is not None:
            setattr(execution, key, value)

    db.commit()
    db.refresh(execution)
    return execution
