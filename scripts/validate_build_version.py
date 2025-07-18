#!/usr/bin/env python3
"""
Build-time version validation script for Karere.

This script performs comprehensive version validation that runs during the build process
to ensure version consistency and format compliance.
"""

import os
import sys
import re
import subprocess
from pathlib import Path


def validate_meson_version():
    """Validate that meson.build has a proper version."""
    meson_file = Path(__file__).parent.parent / 'meson.build'
    
    if not meson_file.exists():
        return False, "meson.build not found"
    
    with open(meson_file, 'r') as f:
        content = f.read()
    
    # Find version in meson.build
    version_pattern = r"project\([^,]+,\s*version:\s*['\"]([^'\"]+)['\"]"
    match = re.search(version_pattern, content)
    
    if not match:
        return False, "No version found in meson.build project() declaration"
    
    version = match.group(1)
    
    # Validate semantic versioning format
    if not re.match(r'^\d+\.\d+\.\d+$', version):
        return False, f"Invalid version format '{version}'. Expected: X.Y.Z"
    
    # Validate reasonable ranges
    parts = version.split('.')
    major, minor, patch = int(parts[0]), int(parts[1]), int(parts[2])
    
    if major > 99 or minor > 99 or patch > 99:
        return False, f"Version component too large: {version}. Max: 99.99.99"
    
    return True, version


def validate_git_tag_consistency():
    """Validate that git tags are consistent with version (if in git repo)."""
    try:
        # Check if we're in a git repository
        subprocess.run(['git', 'rev-parse', '--git-dir'], 
                      capture_output=True, check=True)
        
        # Get current version
        success, version = validate_meson_version()
        if not success:
            return False, f"Cannot get version: {version}"
        
        # Check if tag exists
        try:
            subprocess.run(['git', 'rev-parse', f'v{version}'], 
                          capture_output=True, check=True)
            return True, f"Git tag v{version} exists"
        except subprocess.CalledProcessError:
            # Tag doesn't exist - this is OK for development builds
            return True, f"Git tag v{version} not found (OK for development)"
            
    except subprocess.CalledProcessError:
        # Not in git repo - this is OK
        return True, "Not in git repository (OK)"
    except Exception as e:
        return False, f"Git validation error: {e}"


def validate_template_files():
    """Validate that template files use proper version variables."""
    template_files = [
        'data/io.github.tobagin.karere.metainfo.xml.in',
        'scripts/test_version_format.py.in',
    ]
    
    project_root = Path(__file__).parent.parent
    
    for template_file in template_files:
        file_path = project_root / template_file
        if not file_path.exists():
            return False, f"Template file not found: {template_file}"
        
        with open(file_path, 'r') as f:
            content = f.read()
        
        # Check that template uses @VERSION@ variable
        if '@VERSION@' not in content:
            return False, f"Template file {template_file} doesn't use @VERSION@"
    
    return True, "All template files use @VERSION@ variable"


def validate_no_hardcoded_versions():
    """Validate that no Python files have hardcoded version strings."""
    project_root = Path(__file__).parent.parent
    src_dir = project_root / 'src'
    
    if not src_dir.exists():
        return False, "Source directory not found"
    
    # Get current version for comparison
    success, current_version = validate_meson_version()
    if not success:
        return False, f"Cannot get current version: {current_version}"
    
    problematic_files = []
    
    for py_file in src_dir.rglob('*.py'):
        # Skip the version module (it has legitimate fallbacks)
        if py_file.name == '_version.py':
            continue
        
        with open(py_file, 'r') as f:
            content = f.read()
        
        # Look for hardcoded current version
        if current_version in content and '__version__' not in content:
            problematic_files.append(py_file.relative_to(project_root))
    
    if problematic_files:
        return False, f"Files with hardcoded version {current_version}: {problematic_files}"
    
    return True, "No hardcoded current version found in Python files"


def validate_build_consistency():
    """Validate that build files are consistent."""
    project_root = Path(__file__).parent.parent
    
    # Check that meson.build exists and is readable
    meson_file = project_root / 'meson.build'
    if not meson_file.exists():
        return False, "meson.build not found"
    
    # Check that required directories exist
    required_dirs = ['src', 'data', 'scripts']
    for dir_name in required_dirs:
        dir_path = project_root / dir_name
        if not dir_path.exists():
            return False, f"Required directory not found: {dir_name}"
    
    # Check that key files exist
    required_files = [
        'src/karere/__init__.py',
        'src/karere/_version.py',
        'data/io.github.tobagin.karere.metainfo.xml.in',
    ]
    
    for file_name in required_files:
        file_path = project_root / file_name
        if not file_path.exists():
            return False, f"Required file not found: {file_name}"
    
    return True, "Build file structure is consistent"


def main():
    """Run all build-time version validation tests."""
    tests = [
        ("Meson version format", validate_meson_version),
        ("Git tag consistency", validate_git_tag_consistency),
        ("Template files", validate_template_files),
        ("No hardcoded versions", validate_no_hardcoded_versions),
        ("Build consistency", validate_build_consistency),
    ]
    
    print("Build-time Version Validation")
    print("=" * 40)
    
    all_passed = True
    version_info = None
    
    for test_name, test_func in tests:
        try:
            success, message = test_func()
            status = "✅ PASS" if success else "❌ FAIL"
            print(f"{status}: {test_name}")
            
            if not success:
                print(f"    Error: {message}")
                all_passed = False
            else:
                if test_name == "Meson version format":
                    version_info = message
                print(f"    {message}")
        except Exception as e:
            print(f"❌ ERROR: {test_name} - {e}")
            all_passed = False
    
    print("=" * 40)
    
    if all_passed:
        print(f"🎉 All validation tests passed! Version: {version_info}")
        return 0
    else:
        print("❌ Build validation failed. Please fix the issues above.")
        return 1


if __name__ == '__main__':
    sys.exit(main())