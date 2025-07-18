#!/usr/bin/env python3
"""
Version update script for Karere.

This script updates the version in meson.build, which is the single source of truth
for version information throughout the application.
"""

import argparse
import os
import re
import sys
from pathlib import Path


def update_meson_version(new_version):
    """Update the version in meson.build file."""
    meson_file = Path(__file__).parent.parent / 'meson.build'
    
    if not meson_file.exists():
        print(f"Error: meson.build not found at {meson_file}")
        return False
    
    # Read current content
    with open(meson_file, 'r') as f:
        content = f.read()
    
    # Update version line
    version_pattern = r"(project\([^,]+,\s*version:\s*)['\"]([^'\"]+)['\"]"
    new_content = re.sub(version_pattern, rf"\1'{new_version}'", content)
    
    if content == new_content:
        print("Warning: No version found or version already up to date")
        return False
    
    # Write updated content
    with open(meson_file, 'w') as f:
        f.write(new_content)
    
    print(f"Updated version in meson.build to: {new_version}")
    return True


def get_current_version():
    """Get the current version from meson.build."""
    meson_file = Path(__file__).parent.parent / 'meson.build'
    
    if not meson_file.exists():
        print(f"Error: meson.build not found at {meson_file}")
        return None
    
    with open(meson_file, 'r') as f:
        content = f.read()
    
    # Find version in meson.build
    version_pattern = r"project\([^,]+,\s*version:\s*['\"]([^'\"]+)['\"]"
    match = re.search(version_pattern, content)
    
    if match:
        return match.group(1)
    
    return None


def validate_version(version_str):
    """Validate version string format."""
    if not re.match(r'^\d+\.\d+\.\d+$', version_str):
        return False
    return True


def main():
    parser = argparse.ArgumentParser(
        description='Update version in Karere project',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --show                    # Show current version
  %(prog)s --set 0.2.0               # Set version to 0.2.0
  %(prog)s --set 0.2.0 --validate    # Set version and validate format
        """
    )
    
    parser.add_argument(
        '--show', 
        action='store_true',
        help='Show current version'
    )
    
    parser.add_argument(
        '--set', 
        type=str,
        help='Set new version (format: X.Y.Z)'
    )
    
    parser.add_argument(
        '--validate',
        action='store_true',
        help='Validate version format'
    )
    
    args = parser.parse_args()
    
    if args.show:
        current_version = get_current_version()
        if current_version:
            print(f"Current version: {current_version}")
        else:
            print("Error: Could not determine current version")
            sys.exit(1)
    
    if args.set:
        new_version = args.set
        
        if args.validate and not validate_version(new_version):
            print(f"Error: Invalid version format '{new_version}'. Expected format: X.Y.Z")
            sys.exit(1)
        
        current_version = get_current_version()
        if current_version:
            print(f"Current version: {current_version}")
        
        if update_meson_version(new_version):
            print(f"Version updated successfully to: {new_version}")
            print("\nNext steps:")
            print("1. Run 'meson setup builddir' to regenerate build files")
            print("2. Test the application to ensure version appears correctly")
            print("3. Commit the changes")
            print("4. Create a git tag: git tag v{new_version}")
        else:
            print("Error: Failed to update version")
            sys.exit(1)
    
    if not args.show and not args.set:
        parser.print_help()


if __name__ == '__main__':
    main()