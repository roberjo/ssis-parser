#!/usr/bin/env python3
"""
Version information for SSIS Migration Tool
"""

__version__ = "2.0.0"
__author__ = "SSIS Migration Tool Team"
__email__ = "team@ssis-migrator.com"


def get_version() -> str:
    """Get the current version string"""
    return __version__


def get_version_info() -> dict:
    """Get detailed version information"""
    return {
        "version": __version__,
        "author": __author__,
        "email": __email__,
    }


def is_development_version() -> bool:
    """Check if this is a development version"""
    return "dev" in __version__ or "alpha" in __version__ or "beta" in __version__


def get_version_string() -> str:
    """Get a formatted version string"""
    version_str = f"SSIS Migration Tool v{__version__}"
    if is_development_version():
        version_str += " (Development)"
    return version_str 