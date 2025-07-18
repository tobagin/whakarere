"""
Version management for Karere application.

This module provides a single source of truth for version information,
reading from the package metadata when available, or falling back to
a hardcoded version for development environments.
"""

import os
import sys
from pathlib import Path


def get_version():
    """
    Get the application version from the most reliable source available.
    
    Returns:
        str: The version string (e.g., "0.1.9")
    """
    # Method 1: Try to read from package metadata (when installed)
    try:
        if sys.version_info >= (3, 8):
            from importlib.metadata import version
        else:
            from importlib_metadata import version
        return version('karere')
    except Exception:
        pass
    
    # Method 2: Try to read from meson build configuration
    try:
        # Look for build configuration in various possible locations
        search_paths = [
            Path(__file__).parent.parent.parent / 'meson.build',
            Path(__file__).parent.parent.parent.parent / 'meson.build',
            Path.cwd() / 'meson.build',
        ]
        
        for meson_file in search_paths:
            if meson_file.exists():
                with open(meson_file, 'r') as f:
                    content = f.read()
                    # Parse version from meson.build
                    for line in content.split('\n'):
                        if 'version:' in line and 'project(' in content:
                            # Extract version from line like "  version: '0.1.9',"
                            version_part = line.split('version:')[1].strip()
                            version_str = version_part.split(',')[0].strip().strip("'\"")
                            if version_str:
                                return version_str
                break
    except Exception:
        pass
    
    # Method 3: Read from __init__.py as fallback
    try:
        init_file = Path(__file__).parent / '__init__.py'
        if init_file.exists():
            with open(init_file, 'r') as f:
                content = f.read()
                for line in content.split('\n'):
                    if line.startswith('__version__'):
                        # Extract version from line like '__version__ = "0.1.9"'
                        version_str = line.split('=')[1].strip().strip("'\"")
                        if version_str:
                            return version_str
    except Exception:
        pass
    
    # Method 4: Environment variable (for development/testing)
    env_version = os.environ.get('KARERE_VERSION')
    if env_version:
        return env_version
    
    # Method 5: Final fallback
    return "0.1.9"


def get_version_info():
    """
    Get detailed version information.
    
    Returns:
        dict: Version information including version string and source
    """
    version = get_version()
    
    # Determine the source of the version
    source = "fallback"
    try:
        if sys.version_info >= (3, 8):
            from importlib.metadata import version as get_pkg_version
        else:
            from importlib_metadata import version as get_pkg_version
        get_pkg_version('karere')
        source = "package_metadata"
    except Exception:
        # Check if we got version from meson.build
        search_paths = [
            Path(__file__).parent.parent.parent / 'meson.build',
            Path(__file__).parent.parent.parent.parent / 'meson.build',
            Path.cwd() / 'meson.build',
        ]
        
        for meson_file in search_paths:
            if meson_file.exists():
                source = "meson_build"
                break
        else:
            # Check if from __init__.py
            init_file = Path(__file__).parent / '__init__.py'
            if init_file.exists():
                try:
                    with open(init_file, 'r') as f:
                        content = f.read()
                        if '__version__' in content:
                            source = "init_py"
                except Exception:
                    pass
    
    # Check if from environment
    if os.environ.get('KARERE_VERSION'):
        source = "environment"
    
    return {
        'version': version,
        'source': source,
        'major': int(version.split('.')[0]) if '.' in version else 0,
        'minor': int(version.split('.')[1]) if version.count('.') >= 1 else 0,
        'patch': int(version.split('.')[2]) if version.count('.') >= 2 else 0,
    }


# Export the version for easy access
__version__ = get_version()