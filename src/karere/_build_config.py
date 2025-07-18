"""
Build configuration detection for Karere application.

This module detects the build environment and provides configuration
for production hardening features.
"""

import os
import sys
from pathlib import Path


def is_production_build():
    """
    Determine if this is a production build.
    
    Returns:
        bool: True if this is a production build, False otherwise
    """
    # Method 1: Check environment variable
    if os.environ.get('KARERE_PRODUCTION') == '1':
        return True
    
    # Method 2: Check if running from Flatpak (production-like environment)
    if os.environ.get('FLATPAK_ID'):
        return True
    
    # Method 3: Check if installed in system directories
    try:
        # If we can import from system-installed location
        install_path = Path(__file__).resolve()
        system_paths = [
            Path('/usr/lib/python'),
            Path('/usr/local/lib/python'),
            Path('/app/lib/python'),  # Flatpak
        ]
        
        for sys_path in system_paths:
            if sys_path.exists() and sys_path in install_path.parents:
                return True
    except Exception:
        pass
    
    # Method 4: Check if we're in a development directory structure
    try:
        # Development builds typically have src/karere structure
        current_dir = Path(__file__).parent
        if (current_dir.parent.name == 'src' and 
            (current_dir.parent.parent / 'meson.build').exists()):
            return False
    except Exception:
        pass
    
    # Method 5: Check Python optimization level
    if sys.flags.optimize > 0:
        return True
    
    # Default to development if uncertain
    return False


def is_development_build():
    """
    Determine if this is a development build.
    
    Returns:
        bool: True if this is a development build, False otherwise
    """
    return not is_production_build()


def get_build_info():
    """
    Get detailed build information.
    
    Returns:
        dict: Build information including environment and features
    """
    production = is_production_build()
    
    # Determine build environment
    environment = "development"
    if os.environ.get('KARERE_PRODUCTION') == '1':
        environment = "production (explicit)"
    elif os.environ.get('FLATPAK_ID'):
        environment = "production (flatpak)"
    elif sys.flags.optimize > 0:
        environment = "production (optimized)"
    
    # Check for development indicators
    dev_indicators = []
    if Path(__file__).parent.parent.parent.name == 'src':
        dev_indicators.append("src directory structure")
    if (Path(__file__).parent.parent.parent / 'meson.build').exists():
        dev_indicators.append("meson.build present")
    if os.environ.get('KARERE_DEV_MODE') == '1':
        dev_indicators.append("dev mode environment")
    
    return {
        'is_production': production,
        'is_development': not production,
        'environment': environment,
        'dev_indicators': dev_indicators,
        'flatpak_id': os.environ.get('FLATPAK_ID'),
        'python_optimize': sys.flags.optimize,
        'developer_tools_allowed': not production,
        'debug_logging_allowed': not production or os.environ.get('KARERE_DEBUG') == '1',
    }


def should_enable_developer_tools():
    """
    Determine if developer tools should be enabled.
    
    Returns:
        bool: True if developer tools should be available, False otherwise
    """
    # Always disable in production builds
    if is_production_build():
        return False
    
    # Allow in development builds
    return True


def should_show_developer_settings():
    """
    Determine if developer settings should be shown in the UI.
    
    Returns:
        bool: True if developer settings should be visible, False otherwise
    """
    # Hide developer settings in production
    if is_production_build():
        return False
    
    # Show in development builds
    return True


def get_default_log_level():
    """
    Get the default log level for the current build.
    
    Returns:
        str: Default log level (INFO for production, DEBUG for development)
    """
    if is_production_build():
        return "INFO"
    else:
        return "DEBUG"


def should_enable_debug_features():
    """
    Determine if debug features should be enabled.
    
    Returns:
        bool: True if debug features should be available, False otherwise
    """
    # Enable debug features in development
    if is_development_build():
        return True
    
    # Allow debug features in production if explicitly enabled
    if os.environ.get('KARERE_DEBUG') == '1':
        return True
    
    return False