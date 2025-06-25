#!/usr/bin/env python3
"""
SSIS Migration Tool - Main CLI Entry Point

This module provides the command-line interface for the SSIS Migration Tool.
"""

import sys
from pathlib import Path

# Add the src directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from ssis_migrator.cli import main

if __name__ == "__main__":
    main() 