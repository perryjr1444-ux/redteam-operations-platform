"""Setup configuration for redteam_py_app package."""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="redteam-app",
    version="1.0.0",
    author="c0nfig",
    description="Red Team Exercise Management Application",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Information Technology",
        "Topic :: Security",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.10",
    install_requires=[
        "fastapi>=0.119.0",
        "uvicorn[standard]>=0.38.0",
        "jinja2>=3.1.4",
        "python-multipart>=0.0.19",
        "pydantic-settings>=2.7.1",
        "python-dotenv>=1.0.1",
        "PyYAML>=6.0.2",
        "SQLAlchemy>=2.0.38",
        "alembic>=1.14.0",
        "slowapi>=0.1.9",
    ],
    extras_require={
        "dev": [
            "pytest>=8.3.4",
            "pytest-cov>=6.0.0",
            "pytest-asyncio>=0.24.0",
            "httpx>=0.28.1",
            "black>=24.10.0",
            "flake8>=7.1.1",
            "mypy>=1.14.0",
            "isort>=5.13.2",
        ],
    },
)
