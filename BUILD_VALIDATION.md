# Build Validation

This document describes the build-time validation system for Karere that ensures version consistency and build quality.

## Overview

The build validation system automatically runs during the build process to catch version inconsistencies, format issues, and structural problems before they reach production.

## Validation Tests

### 1. Version Format Validation
**Script**: `scripts/test_version_format.py.in`
**Purpose**: Validates that the version follows semantic versioning (X.Y.Z) format
**Build Integration**: Meson test `version-format`

**Checks**:
- Version matches `^\d+\.\d+\.\d+$` pattern
- Version components are reasonable (≤ 99.99.99)
- No invalid characters or formats

### 2. Version Consistency Validation
**Script**: `scripts/test_version_consistency.py`
**Purpose**: Ensures all version references use the centralized system
**Build Integration**: Meson test `version-consistency`

**Checks**:
- Meson version format and validity
- Python package version import
- About dialog version usage
- Metainfo template variables
- Main script version flag support
- No hardcoded version strings in code

### 3. Build-time Version Validation
**Script**: `scripts/validate_build_version.py`
**Purpose**: Comprehensive build-time validation
**Build Integration**: Meson test `build-version-validation`

**Checks**:
- Meson version format compliance
- Git tag consistency (if applicable)
- Template file usage of @VERSION@ variables
- No hardcoded current version in Python files
- Build file structure consistency

## Running Validation

### During Build Process
```bash
# Set up build directory
meson setup builddir

# Run all validation tests
meson test -C builddir --suite validation

# Run specific validation test
meson test -C builddir version-consistency
```

### Manual Validation
```bash
# Run comprehensive version consistency test
python3 scripts/test_version_consistency.py

# Run build-time validation
python3 scripts/validate_build_version.py

# Check version format (requires built version)
python3 builddir/test_version_format.py
```

## Build Integration

### Meson Configuration
The validation tests are integrated into the meson build system:

```meson
# Version validation tests
test('version-consistency', py_installation,
  args: [version_consistency_script],
  suite: 'validation',
  timeout: 30
)

test('build-version-validation', py_installation,
  args: [build_validation_script],
  suite: 'validation',
  timeout: 30
)

test('version-format', py_installation,
  args: [version_format_script],
  suite: 'validation',
  timeout: 10
)
```

### Test Suites
- **validation**: All version validation tests
- **default**: Includes validation tests plus other project tests

## Validation Results

### Success Output
```
✅ PASS: Meson version format (0.1.9)
✅ PASS: Python version (0.1.9)
✅ PASS: About dialog version (Uses centralized version)
✅ PASS: Metainfo template (Uses template variable)
✅ PASS: Main version flag (Supports --version flag)
✅ PASS: No hardcoded versions (No hardcoded versions found)
🎉 All validation tests passed!
```

### Failure Scenarios
The validation system will fail the build if:
- Version format is invalid (not X.Y.Z)
- Version components are unreasonable (> 99)
- Hardcoded version strings are found in code
- Template files don't use @VERSION@ variable
- Required files are missing
- Version references are inconsistent

## Continuous Integration

### Local Development
```bash
# Before committing changes
meson test -C builddir --suite validation
```

### CI/CD Pipeline
The validation tests should be run as part of the CI/CD pipeline:
```yaml
# Example GitHub Actions step
- name: Run validation tests
  run: |
    meson setup builddir
    meson test -C builddir --suite validation
```

## Troubleshooting

### Version Format Errors
```
❌ FAIL: Invalid version format '0.1.9-dev'
Expected format: X.Y.Z (e.g., 0.1.9)
```
**Solution**: Update version in meson.build to use proper semver format

### Hardcoded Version Errors
```
❌ FAIL: Files with hardcoded version 0.1.9: ['src/karere/example.py']
```
**Solution**: Replace hardcoded version with import from centralized source

### Template Variable Errors
```
❌ FAIL: Template file data/example.xml.in doesn't use @VERSION@
```
**Solution**: Update template file to use @VERSION@ variable instead of hardcoded version

### Missing File Errors
```
❌ FAIL: Required file not found: src/karere/_version.py
```
**Solution**: Ensure all required files are present in the repository

## Files Involved

### Validation Scripts
- `scripts/test_version_consistency.py` - Comprehensive version consistency test
- `scripts/validate_build_version.py` - Build-time validation
- `scripts/test_version_format.py.in` - Version format validation template

### Build Configuration
- `meson.build` - Test definitions and build integration
- `BUILD_VALIDATION.md` - This documentation

### Version Management
- `src/karere/_version.py` - Central version logic
- `src/karere/__init__.py` - Version export
- `data/io.github.tobagin.karere.metainfo.xml.in` - Version template

## Best Practices

### For Developers
1. Always run validation tests before committing
2. Never hardcode version strings in code
3. Use centralized version system for all references
4. Test version changes with validation suite

### For Maintainers
1. Ensure validation tests are run in CI/CD
2. Update validation logic when adding new version references
3. Keep validation tests up to date with project structure
4. Review validation failures carefully before overriding

### For Release Management
1. Validation tests must pass before creating releases
2. Use version update script for consistent version changes
3. Verify validation passes after version updates
4. Include validation in release checklists

## Future Enhancements

Potential improvements to the validation system:
- Integration with git hooks for automatic validation
- Performance benchmarks for validation execution
- Extended validation for translation files
- Integration with package managers for version consistency
- Automated version suggestion based on git history