#!/usr/bin/env python3
"""
Test script to verify version consistency across the Karere project.

This script validates that all version references use the centralized source
and that the version is correctly propagated throughout the application.
"""

import os
import sys
import re
from pathlib import Path


def test_meson_version():
    """Test that meson.build has a valid version."""
    meson_file = Path(__file__).parent.parent / 'meson.build'
    
    if not meson_file.exists():
        return False, "meson.build not found"
    
    with open(meson_file, 'r') as f:
        content = f.read()
    
    version_pattern = r"project\([^,]+,\s*version:\s*['\"]([^'\"]+)['\"]"
    match = re.search(version_pattern, content)
    
    if not match:
        return False, "No version found in meson.build"
    
    version = match.group(1)
    if not re.match(r'^\d+\.\d+\.\d+$', version):
        return False, f"Invalid version format: {version}"
    
    return True, version


def test_python_version():
    """Test that Python package version is correct."""
    try:
        sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))
        import karere
        return True, karere.__version__
    except ImportError as e:
        return False, f"Failed to import karere: {e}"
    except AttributeError as e:
        return False, f"No __version__ attribute: {e}"


def test_about_dialog_version():
    """Test that about dialog uses centralized version."""
    about_file = Path(__file__).parent.parent / 'src' / 'karere' / 'about.py'
    
    if not about_file.exists():
        return False, "about.py not found"
    
    with open(about_file, 'r') as f:
        content = f.read()
    
    # Check that it imports __version__
    if 'from . import __version__' not in content:
        return False, "about.py doesn't import __version__"
    
    # Check that it uses __version__ instead of hardcoded version
    if 'set_version(__version__)' not in content:
        return False, "about.py doesn't use __version__ in set_version()"
    
    # Check that there are no hardcoded version strings
    if re.search(r'set_version\(["\'][\d\.]+["\']', content):
        return False, "about.py has hardcoded version strings"
    
    return True, "Uses centralized version"


def test_metainfo_template():
    """Test that metainfo.xml.in uses template variable."""
    metainfo_file = Path(__file__).parent.parent / 'data' / 'io.github.tobagin.karere.metainfo.xml.in'
    
    if not metainfo_file.exists():
        return False, "metainfo.xml.in not found"
    
    with open(metainfo_file, 'r') as f:
        content = f.read()
    
    # Check that it uses @VERSION@ template
    if '@VERSION@' not in content:
        return False, "metainfo.xml.in doesn't use @VERSION@ template"
    
    # Check that there are no hardcoded current version references
    # (historical versions are OK)
    current_version = test_meson_version()[1]
    if current_version and f'version="{current_version}"' in content:
        return False, f"metainfo.xml.in has hardcoded current version {current_version}"
    
    return True, "Uses template variable"


def test_main_version_flag():
    """Test that main.py supports --version flag."""
    main_file = Path(__file__).parent.parent / 'src' / 'karere' / 'main.py'
    
    if not main_file.exists():
        return False, "main.py not found"
    
    with open(main_file, 'r') as f:
        content = f.read()
    
    # Check that it imports __version__
    if 'from . import __version__' not in content:
        return False, "main.py doesn't import __version__"
    
    # Check that it has version argument
    if '--version' not in content:
        return False, "main.py doesn't support --version flag"
    
    return True, "Supports --version flag"


def test_no_hardcoded_versions():
    """Test that there are no hardcoded version strings in Python files."""
    src_dir = Path(__file__).parent.parent / 'src'
    problematic_files = []
    
    for py_file in src_dir.rglob('*.py'):
        if py_file.name == '_version.py':
            continue  # Skip the version module (it has fallbacks)
        
        with open(py_file, 'r') as f:
            content = f.read()
        
        # Look for hardcoded version patterns
        if re.search(r'["\']0\.\d+\.\d+["\']', content):
            problematic_files.append(py_file.relative_to(src_dir))
    
    if problematic_files:
        return False, f"Files with hardcoded versions: {problematic_files}"
    
    return True, "No hardcoded versions found"


def main():
    """Run all version consistency tests."""
    tests = [
        ("Meson version", test_meson_version),
        ("Python version", test_python_version),
        ("About dialog version", test_about_dialog_version),
        ("Metainfo template", test_metainfo_template),
        ("Main version flag", test_main_version_flag),
        ("No hardcoded versions", test_no_hardcoded_versions),
    ]
    
    print("Version Consistency Test")
    print("=" * 50)
    
    all_passed = True
    results = []
    
    for test_name, test_func in tests:
        try:
            success, message = test_func()
            status = "✅ PASS" if success else "❌ FAIL"
            print(f"{status}: {test_name}")
            if not success:
                print(f"    Error: {message}")
                all_passed = False
            else:
                results.append((test_name, message))
        except Exception as e:
            print(f"❌ ERROR: {test_name} - {e}")
            all_passed = False
    
    print("\n" + "=" * 50)
    
    if all_passed:
        print("🎉 All version consistency tests passed!")
        print("\nVersion Information:")
        for test_name, result in results:
            if "version" in result or result.startswith("0."):
                print(f"  {test_name}: {result}")
    else:
        print("❌ Some tests failed. Please fix the issues above.")
        sys.exit(1)


if __name__ == '__main__':
    main()