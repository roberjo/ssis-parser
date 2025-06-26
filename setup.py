#!/usr/bin/env python3
"""
Setup script for SSIS Migration Tool
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read the README file
readme_path = Path(__file__).parent / "README.md"
long_description = readme_path.read_text() if readme_path.exists() else ""

# Read requirements
requirements_path = Path(__file__).parent / "requirements.txt"
requirements = []
if requirements_path.exists():
    requirements = [
        line.strip() 
        for line in requirements_path.read_text().splitlines() 
        if line.strip() and not line.startswith("#")
    ]

setup(
    name="ssis-migrator",
    version="2.0.0",
    description="A tool to migrate SSIS packages to Python ETL scripts",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="SSIS Migration Tool Team",
    author_email="team@ssis-migrator.com",
    url="https://github.com/your-org/ssis-parser",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Database",
        "Topic :: Scientific/Engineering :: Information Analysis",
    ],
    python_requires=">=3.10",
    install_requires=requirements,
    extras_require={
        "dev": [
            "black>=23.0.0",
            "flake8>=6.0.0",
            "mypy>=1.5.0",
            "pre-commit>=3.3.0",
            "isort>=5.12.0",
        ],
        "test": [
            "pytest>=7.4.0",
            "pytest-cov>=4.1.0",
            "pytest-mock>=3.11.0",
            "pytest-asyncio>=0.21.0",
        ],
        "docs": [
            "mkdocs>=1.5.0",
            "mkdocs-material>=9.2.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "ssis-migrator=ssis_migrator.cli:main",
        ],
    },
    include_package_data=True,
    zip_safe=False,
    keywords="ssis, etl, migration, python, data, sql-server",
    project_urls={
        "Bug Reports": "https://github.com/your-org/ssis-parser/issues",
        "Source": "https://github.com/your-org/ssis-parser",
        "Documentation": "https://github.com/your-org/ssis-parser/docs",
    },
) 