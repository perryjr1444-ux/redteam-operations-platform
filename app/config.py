"""Application configuration management."""

import os
import sys
from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import field_validator, ValidationError

# Import quantum key generation
try:
    from app.quantum_keygen import generate_quantum_secret_key
    QUANTUM_KEYGEN_AVAILABLE = True
except ImportError:
    QUANTUM_KEYGEN_AVAILABLE = False


class Settings(BaseSettings):
    """Application settings with environment variable overrides."""

    # Application
    APP_NAME: str = "RedTeam Exercise Manager"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    ENVIRONMENT: str = "production"

    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 5172
    WORKERS: int = 4

    # Database
    DATABASE_URL: str = "sqlite:///./db/redteam.db"

    # Security
    SECRET_KEY: str = os.getenv("SECRET_KEY", "")
    ALLOWED_HOSTS: list[str] = ["*"]
    CORS_ORIGINS: list[str] = []
    RATE_LIMIT_PER_MINUTE: int = 60

    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"  # json or text

    # UI Theme
    UI_THEME: str = "shadcn"  # Options: shadcn, cyberpunk, military
    THEME_SWITCHER_ENABLED: bool = True

    # Paths
    BASE_DIR: Path = Path(__file__).parent.parent
    STATIC_DIR: Path = BASE_DIR / "static"
    TEMPLATES_DIR: Path = BASE_DIR / "templates"
    DATA_DIR: Path = BASE_DIR / "data"
    DB_DIR: Path = BASE_DIR / "db"

    # Data initialization
    SCHEMA_FILE: str = "cli_schema.yaml"
    AUTO_POPULATE: bool = True

    @field_validator('SECRET_KEY')
    @classmethod
    def validate_secret_key(cls, v, info):
        """Validate SECRET_KEY is set properly - warnings only, no exit."""
        environment = info.data.get('ENVIRONMENT', 'production')

        # In development/test, provide a default but warn
        if not v:
            if environment in ["development", "dev", "test"]:
                print(f"\nWARNING: Using default SECRET_KEY in {environment} mode.", file=sys.stderr)
                print("This is INSECURE and should only be used for local development!\n", file=sys.stderr)
                return "dev-insecure-key-change-for-production-use-only-DO-NOT-USE-IN-PROD"
            else:
                # Production mode - will be validated at startup
                print(f"\nWARNING: SECRET_KEY not set in {environment} mode!", file=sys.stderr)
                print("This will be checked at application startup.\n", file=sys.stderr)
                return ""

        return v

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


def validate_production_config():
    """
    Validate production configuration.

    Call this at application startup (not import time) to enforce
    production security requirements.

    Automatically generates quantum-inspired secret key if not provided.

    Raises:
        SystemExit: If configuration is invalid in production mode
    """
    if settings.ENVIRONMENT == "production":
        if not settings.SECRET_KEY or settings.SECRET_KEY in [
            "",
            "CHANGE_ME_IN_PRODUCTION",
            "changeme",
            "secret",
            "password",
            "change-me-in-production"
        ]:
            # Auto-generate quantum secret key
            if QUANTUM_KEYGEN_AVAILABLE:
                print("\n" + "=" * 80, file=sys.stderr)
                print("Quantum-Inspired Key Generation System", file=sys.stderr)
                print("=" * 80, file=sys.stderr)
                print("\nNo SECRET_KEY provided. Generating quantum-inspired key...", file=sys.stderr)

                try:
                    quantum_key = generate_quantum_secret_key()
                    settings.SECRET_KEY = quantum_key

                    print("✓ Crystal Lattice KDF: Initialized", file=sys.stderr)
                    print("✓ Master Seed: Loaded/Generated", file=sys.stderr)
                    print("✓ Lattice Transformations: Applied", file=sys.stderr)
                    print("✓ Key Derivation: Complete", file=sys.stderr)
                    print(f"✓ Key Length: {len(quantum_key)} characters", file=sys.stderr)
                    print("\nQuantum-inspired SECRET_KEY generated successfully!", file=sys.stderr)
                    print("Note: Key is derived deterministically from master seed.", file=sys.stderr)
                    print("Master seed location: db/.quantum_seed", file=sys.stderr)
                    print("\n" + "=" * 80 + "\n", file=sys.stderr)
                except Exception as e:
                    print(f"\n✗ Quantum key generation failed: {e}", file=sys.stderr)
                    print("Falling back to manual configuration required.", file=sys.stderr)
                    print("\n" + "=" * 80, file=sys.stderr)
                    print("CRITICAL SECURITY ERROR: SECRET_KEY not set!", file=sys.stderr)
                    print("=" * 80, file=sys.stderr)
                    print("\nGenerate a secure key with:", file=sys.stderr)
                    print("  python3 -c 'import secrets; print(secrets.token_urlsafe(32))'", file=sys.stderr)
                    print("\n" + "=" * 80 + "\n", file=sys.stderr)
                    sys.exit(1)
            else:
                print("\n" + "=" * 80, file=sys.stderr)
                print("CRITICAL SECURITY ERROR: SECRET_KEY not set!", file=sys.stderr)
                print("=" * 80, file=sys.stderr)
                print("\nYou must set a strong SECRET_KEY environment variable in production.", file=sys.stderr)
                print("Generate a secure key with:", file=sys.stderr)
                print("  python3 -c 'import secrets; print(secrets.token_urlsafe(32))'", file=sys.stderr)
                print("\nThen set it in your environment:", file=sys.stderr)
                print("  export SECRET_KEY='<your-generated-key>'", file=sys.stderr)
                print("  # or add to .env file", file=sys.stderr)
                print("\n" + "=" * 80 + "\n", file=sys.stderr)
                sys.exit(1)

        # Ensure minimum length
        if len(settings.SECRET_KEY) < 32:
            print("\n" + "=" * 80, file=sys.stderr)
            print("CRITICAL SECURITY ERROR: SECRET_KEY too short!", file=sys.stderr)
            print("=" * 80, file=sys.stderr)
            print(f"\nSECRET_KEY must be at least 32 characters long (current: {len(settings.SECRET_KEY)})", file=sys.stderr)
            print("Generate a secure key with:", file=sys.stderr)
            print("  python3 -c 'import secrets; print(secrets.token_urlsafe(32))'", file=sys.stderr)
            print("\n" + "=" * 80 + "\n", file=sys.stderr)
            sys.exit(1)

    print(f"✓ Configuration validated for {settings.ENVIRONMENT} environment", file=sys.stderr)


# Initialize settings (validation happens at startup, not here)
settings = Settings()
