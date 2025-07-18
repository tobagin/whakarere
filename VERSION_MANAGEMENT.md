# Version Management

This document describes the centralized version management system for Karere.

## Overview

Karere uses a centralized version management system where **meson.build** serves as the single source of truth for version information. All other components read the version from this central location.

## Architecture

### Single Source of Truth
- **meson.build**: Contains the authoritative version in the `project()` declaration
- All other files derive their version from this source

### Version Flow

```
meson.build (version: '0.1.9')
    ├── src/karere/_version.py (reads from meson.build)
    ├── src/karere/__init__.py (imports from _version.py)
    ├── src/karere/about.py (imports from __init__.py)
    ├── data/io.github.tobagin.karere.metainfo.xml.in (uses @VERSION@ template)
    ├── setup.py (reads from meson.build)
    └── pyproject.toml (reads from karere.__version__)
```

## Components

### 1. Core Version Module (`src/karere/_version.py`)
- Provides centralized version reading logic
- Implements fallback strategy for different environments
- Supports multiple version sources in priority order:
  1. Package metadata (when installed)
  2. meson.build file (development)
  3. `__init__.py` fallback
  4. Environment variable (`KARERE_VERSION`)
  5. Hardcoded fallback

### 2. Package Initialization (`src/karere/__init__.py`)
- Imports version from `_version.py`
- Exports `__version__` for application use

### 3. Application Components
- **about.py**: Uses `__version__` from package root
- **metainfo.xml.in**: Uses `@VERSION@` template replaced by meson

### 4. Build System Integration
- **meson.build**: Defines version and exposes it as `@VERSION@`
- **setup.py**: Reads version from meson.build for pip compatibility
- **pyproject.toml**: Uses dynamic version from package metadata

## Usage

### For Developers

#### Updating Version
Use the provided script:
```bash
# Show current version
python3 scripts/update_version.py --show

# Update to new version
python3 scripts/update_version.py --set 0.2.0 --validate

# Regenerate build files
meson setup builddir
```

#### Manual Version Update
1. Edit `meson.build` and change the version in `project()` declaration
2. Run `meson setup builddir` to regenerate build files
3. Test that version appears correctly in application

### For Users

#### Checking Version
```bash
# From command line (if installed)
karere --version

# From Python
python3 -c "import karere; print(karere.__version__)"

# From application
# Check Help → About dialog
```

## Files Involved

### Core Files
- `meson.build` - Single source of truth
- `src/karere/_version.py` - Version reading logic
- `src/karere/__init__.py` - Package version export

### Template Files
- `data/io.github.tobagin.karere.metainfo.xml.in` - Uses `@VERSION@`

### Build Files
- `setup.py` - Reads from meson.build
- `pyproject.toml` - Uses dynamic version

### Utility Files
- `scripts/update_version.py` - Version update script
- `VERSION_MANAGEMENT.md` - This documentation

## Version Format

Karere follows Semantic Versioning (semver):
- Format: `MAJOR.MINOR.PATCH`
- Example: `0.1.9`
- Validation: `^\d+\.\d+\.\d+$`

## Environment Variables

### `KARERE_VERSION`
Override version for development/testing:
```bash
export KARERE_VERSION=0.2.0-dev
```

### `KARERE_LOG_LEVEL`
Control logging verbosity (unrelated to version):
```bash
export KARERE_LOG_LEVEL=DEBUG
```

## Best Practices

### For Version Updates
1. Always use the update script for consistency
2. Test the application after version changes
3. Update relevant documentation if needed
4. Create git tags for releases: `git tag v0.1.9`

### For Development
1. Never hardcode version numbers in application code
2. Always import version from `karere.__version__`
3. Use the centralized version system for all version references
4. Test version display in both development and installed environments

## Troubleshooting

### Version Not Updating
1. Check that meson.build was updated correctly
2. Run `meson setup builddir` to regenerate build files
3. Verify that Python imports are working: `python3 -c "import karere; print(karere.__version__)"`

### Version Mismatch
1. Ensure all version references use the centralized system
2. Check that no files have hardcoded version strings
3. Verify meson configuration is up to date

### Development vs Production
- Development: Version read from meson.build
- Installed: Version read from package metadata
- Both should show the same version if properly configured

## Future Enhancements

Possible improvements to the version system:
- Automatic version bumping based on git tags
- Integration with CI/CD pipelines
- Version validation in tests
- Automatic changelog generation