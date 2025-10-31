
from sqlalchemy import Column, Integer, String, Float, Text, DateTime, Boolean
from datetime import datetime
from .database import Base

class Template(Base):
    __tablename__ = "templates"

    id = Column(Integer, primary_key=True, index=True)
    template_id = Column(String, unique=True, index=True)
    name = Column(String)
    category = Column(String)
    risk_level = Column(String)
    duration = Column(String)

class Exercise(Base):
    __tablename__ = "exercises"

    id = Column(Integer, primary_key=True, index=True)
    exercise_id = Column(String, unique=True, index=True)
    template = Column(String)
    state = Column(String)
    progress = Column(Float)
    start_date = Column(String)
    owner = Column(String)

class AttackContainer(Base):
    """Track Kali Linux attack containers"""
    __tablename__ = "attack_containers"

    id = Column(Integer, primary_key=True, index=True)
    container_id = Column(String, unique=True, index=True)
    container_name = Column(String)
    exercise_id = Column(String)  # Link to exercise
    image = Column(String, default="kalilinux/kali-rolling:latest")
    status = Column(String)  # running, stopped, exited
    target = Column(String)  # Target IP/hostname
    attack_type = Column(String)  # nmap, metasploit, sqlmap, etc.
    command = Column(Text)  # Command being executed
    created_at = Column(DateTime, default=datetime.utcnow)
    stopped_at = Column(DateTime, nullable=True)


class User(Base):
    """User authentication and authorization"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(100), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    is_superuser = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    last_login = Column(DateTime, nullable=True)


class AttackChain(Base):
    """Custom attack chain definition"""
    __tablename__ = "attack_chains"

    id = Column(Integer, primary_key=True, index=True)
    chain_id = Column(String, unique=True, index=True, nullable=False)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    category = Column(String(100), nullable=True)
    risk_level = Column(String(20), default="medium")  # low, medium, high, critical
    steps = Column(Text, nullable=False)  # JSON-encoded list of steps
    chain_metadata = Column(Text, nullable=True)  # JSON-encoded metadata
    created_by = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_template = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)


class ChainExecution(Base):
    """Attack chain execution history"""
    __tablename__ = "chain_executions"

    id = Column(Integer, primary_key=True, index=True)
    execution_id = Column(String, unique=True, index=True, nullable=False)
    chain_id = Column(String, index=True, nullable=False)
    chain_name = Column(String(200), nullable=True)
    status = Column(String(20), default="pending")  # pending, running, completed, failed, cancelled
    total_steps = Column(Integer, default=0)
    completed_steps = Column(Integer, default=0)
    failed_steps = Column(Integer, default=0)
    skipped_steps = Column(Integer, default=0)
    results = Column(Text, nullable=True)  # JSON-encoded step results
    start_time = Column(DateTime, nullable=True)
    end_time = Column(DateTime, nullable=True)
    duration = Column(Float, nullable=True)  # seconds
    executed_by = Column(String(50), nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
