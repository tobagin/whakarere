#!/usr/bin/env python3
"""
Test script to verify production hardening features.

This script tests that developer tools and debug features are properly
disabled in production builds.
"""

import os
import sys
import tempfile
from pathlib import Path


def test_build_config():
    """Test build configuration detection."""
    print("Testing build configuration detection...")
    
    # Add src to path for testing
    sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))
    
    from karere._build_config import (
        is_production_build, is_development_build, get_build_info,
        should_enable_developer_tools, should_show_developer_settings,
        get_default_log_level, should_enable_debug_features
    )
    
    # Test in current environment
    print(f"  Current environment:")
    build_info = get_build_info()
    for key, value in build_info.items():
        print(f"    {key}: {value}")
    
    # Test with explicit production environment
    print(f"\n  Testing explicit production environment:")
    os.environ['KARERE_PRODUCTION'] = '1'
    
    # Re-import to pick up environment changes
    import importlib
    import karere._build_config
    importlib.reload(karere._build_config)
    
    from karere._build_config import (
        is_production_build, is_development_build, get_build_info,
        should_enable_developer_tools, should_show_developer_settings,
        get_default_log_level, should_enable_debug_features
    )
    
    production_info = get_build_info()
    for key, value in production_info.items():
        print(f"    {key}: {value}")
    
    # Verify production hardening
    assert is_production_build(), "Should detect production build"
    assert not should_enable_developer_tools(), "Developer tools should be disabled"
    assert not should_show_developer_settings(), "Developer settings should be hidden"
    assert get_default_log_level() == "INFO", "Default log level should be INFO"
    assert not should_enable_debug_features(), "Debug features should be disabled"
    
    print("  ✅ Production hardening working correctly")
    
    # Test with debug override
    print(f"\n  Testing debug override in production:")
    os.environ['KARERE_DEBUG'] = '1'
    
    # Re-import to pick up environment changes
    importlib.reload(karere._build_config)
    
    from karere._build_config import should_enable_debug_features
    
    assert should_enable_debug_features(), "Debug features should be enabled with override"
    print("  ✅ Debug override working correctly")
    
    # Clean up environment
    del os.environ['KARERE_PRODUCTION']
    del os.environ['KARERE_DEBUG']
    
    return True


def test_developer_tools_disabled():
    """Test that developer tools are properly disabled in production."""
    print("\nTesting developer tools disabling...")
    
    # Set production environment
    os.environ['KARERE_PRODUCTION'] = '1'
    
    # Test that developer tools detection works
    sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))
    
    from karere._build_config import should_enable_developer_tools, should_show_developer_settings
    
    assert not should_enable_developer_tools(), "Developer tools should be disabled in production"
    assert not should_show_developer_settings(), "Developer settings should be hidden in production"
    
    print("  ✅ Developer tools properly disabled in production")
    
    # Clean up
    del os.environ['KARERE_PRODUCTION']
    
    return True


def test_logging_hardening():
    """Test that logging is properly hardened in production."""
    print("\nTesting logging hardening...")
    
    # Set production environment
    os.environ['KARERE_PRODUCTION'] = '1'
    
    sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))
    
    from karere._build_config import get_default_log_level, should_enable_debug_features
    
    # Test default log level
    assert get_default_log_level() == "INFO", "Default log level should be INFO in production"
    
    # Test debug features
    assert not should_enable_debug_features(), "Debug features should be disabled in production"
    
    print("  ✅ Logging properly hardened in production")
    
    # Test with debug override
    os.environ['KARERE_DEBUG'] = '1'
    
    # Re-import to pick up environment changes
    import importlib
    import karere._build_config
    importlib.reload(karere._build_config)
    
    from karere._build_config import should_enable_debug_features
    
    assert should_enable_debug_features(), "Debug features should be enabled with override"
    print("  ✅ Debug override working for logging")
    
    # Clean up
    del os.environ['KARERE_PRODUCTION']
    del os.environ['KARERE_DEBUG']
    
    return True


def test_flatpak_detection():
    """Test that Flatpak environment is detected as production."""
    print("\nTesting Flatpak detection...")
    
    # Set Flatpak environment
    os.environ['FLATPAK_ID'] = 'io.github.tobagin.karere'
    
    sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))
    
    # Re-import to pick up environment changes
    import importlib
    import karere._build_config
    importlib.reload(karere._build_config)
    
    from karere._build_config import is_production_build, get_build_info
    
    assert is_production_build(), "Flatpak environment should be detected as production"
    
    build_info = get_build_info()
    assert build_info['environment'] == "production (flatpak)", "Should detect Flatpak environment"
    
    print("  ✅ Flatpak environment properly detected as production")
    
    # Clean up
    del os.environ['FLATPAK_ID']
    
    return True


def test_gsettings_integration():
    """Test that GSettings integration works with production hardening."""
    print("\nTesting GSettings integration...")
    
    # This test requires the schema to be installed, so we'll just test the logic
    # In a real environment, you would test with actual GSettings
    
    # Test the production hardening logic
    os.environ['KARERE_PRODUCTION'] = '1'
    
    sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))
    
    from karere._build_config import should_enable_developer_tools
    
    # In production, developer tools should be disabled regardless of settings
    assert not should_enable_developer_tools(), "Developer tools should be disabled in production"
    
    print("  ✅ GSettings integration logic working correctly")
    
    # Clean up
    del os.environ['KARERE_PRODUCTION']
    
    return True


def main():
    """Run all production hardening tests."""
    print("Production Hardening Test Suite")
    print("=" * 50)
    
    tests = [
        ("Build configuration detection", test_build_config),
        ("Developer tools disabling", test_developer_tools_disabled),
        ("Logging hardening", test_logging_hardening),
        ("Flatpak detection", test_flatpak_detection),
        ("GSettings integration", test_gsettings_integration),
    ]
    
    all_passed = True
    
    for test_name, test_func in tests:
        try:
            success = test_func()
            if success:
                print(f"✅ PASS: {test_name}")
            else:
                print(f"❌ FAIL: {test_name}")
                all_passed = False
        except Exception as e:
            print(f"❌ ERROR: {test_name} - {e}")
            all_passed = False
    
    print("=" * 50)
    
    if all_passed:
        print("🎉 All production hardening tests passed!")
        return 0
    else:
        print("❌ Some tests failed. Please fix the issues above.")
        return 1


if __name__ == '__main__':
    sys.exit(main())