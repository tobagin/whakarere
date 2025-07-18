# Production Hardening

This document describes the production hardening features implemented in Karere to ensure developer tools and debug features are properly disabled in production builds.

## Overview

Karere implements automatic production hardening that detects the build environment and applies appropriate security and performance optimizations. This ensures that developer tools, debug features, and development artifacts are not exposed in production deployments.

## Build Environment Detection

### Production Environment Detection
The application automatically detects production environments using multiple methods:

1. **Explicit Environment Variable**: `KARERE_PRODUCTION=1`
2. **Flatpak Environment**: Presence of `FLATPAK_ID` environment variable
3. **Installation Path**: Installed in system directories (`/usr/lib`, `/usr/local/lib`, `/app/lib`)
4. **Python Optimization**: `python -O` or `python -OO` execution
5. **Directory Structure**: Absence of development directory structure

### Development Environment Detection
Development environments are detected by:
- Presence of `src/karere` directory structure
- Presence of `meson.build` in project root
- `KARERE_DEV_MODE=1` environment variable
- Running from uninstalled source directory

## Hardening Features

### 1. Developer Tools Disabling

**Production Behavior**:
- WebKit developer tools are force-disabled
- Developer tools settings are hidden from UI
- Developer tools toggle is made insensitive
- GSettings `developer-tools` key is forced to `false`

**Development Behavior**:
- Developer tools respect user settings
- Settings UI shows developer tools toggle
- WebKit inspector can be enabled/disabled by user

### 2. Debug Logging Hardening

**Production Behavior**:
- Default log level is `INFO` instead of `DEBUG`
- Debug log level is blocked unless `KARERE_DEBUG=1`
- Debug features are disabled by default

**Development Behavior**:
- Default log level is `DEBUG`
- All logging levels are available
- Debug features are enabled by default

### 3. Settings UI Hardening

**Production Behavior**:
- Developer settings section is hidden
- Debug-related settings are not accessible
- Production-safe defaults are enforced

**Development Behavior**:
- All settings are visible and configurable
- Developer settings are accessible
- Debug settings are available

## Environment Variables

### Production Control
- `KARERE_PRODUCTION=1` - Force production mode
- `KARERE_DEBUG=1` - Enable debug features in production (override)

### Development Control
- `KARERE_DEV_MODE=1` - Force development mode
- `KARERE_LOG_LEVEL=DEBUG` - Set specific log level

### Build Detection
- `FLATPAK_ID` - Automatically detected (indicates Flatpak environment)
- `PYTHONOPTIMIZE` - Automatically detected (indicates optimized Python)

## API Reference

### Build Configuration Module (`_build_config.py`)

#### Functions

**`is_production_build()`**
- Returns: `bool` - True if running in production environment
- Checks multiple indicators to determine production status

**`is_development_build()`**
- Returns: `bool` - True if running in development environment
- Inverse of `is_production_build()`

**`should_enable_developer_tools()`**
- Returns: `bool` - True if developer tools should be available
- Always `False` in production, `True` in development

**`should_show_developer_settings()`**
- Returns: `bool` - True if developer settings should be visible in UI
- Always `False` in production, `True` in development

**`get_default_log_level()`**
- Returns: `str` - Default log level for current environment
- Returns `"INFO"` for production, `"DEBUG"` for development

**`should_enable_debug_features()`**
- Returns: `bool` - True if debug features should be enabled
- Checks environment and `KARERE_DEBUG` override

**`get_build_info()`**
- Returns: `dict` - Comprehensive build and environment information
- Includes detection results, environment variables, and feature flags

## Integration

### Application Integration

The hardening system is integrated into key application components:

**Settings Dialog** (`settings.py`):
```python
from ._build_config import should_show_developer_settings, should_enable_developer_tools

def _configure_production_hardening(self):
    if not should_show_developer_settings():
        self.developer_tools_row.set_visible(False)
    
    if not should_enable_developer_tools():
        self.settings.set_boolean("developer-tools", False)
        self.developer_tools_row.set_sensitive(False)
```

**Window Component** (`window.py`):
```python
from ._build_config import should_enable_developer_tools

def _apply_settings(self):
    if should_enable_developer_tools():
        developer_tools_enabled = self.settings.get_boolean("developer-tools")
    else:
        developer_tools_enabled = False
    
    webkit_settings.set_enable_developer_extras(developer_tools_enabled)
```

**Application** (`application.py`):
```python
from ._build_config import get_default_log_level, should_enable_debug_features

def _setup_logging(self):
    log_level = settings.get_string("log-level") or get_default_log_level()
    
    if log_level == "DEBUG" and not should_enable_debug_features():
        log_level = "INFO"
```

### Build System Integration

Production hardening is validated during the build process:

```meson
test('production-hardening', py_installation,
  args: [production_hardening_script],
  suite: 'validation',
  timeout: 30
)
```

## Testing

### Manual Testing

```bash
# Test development environment
python3 scripts/test_production_hardening.py

# Test production environment
KARERE_PRODUCTION=1 python3 scripts/test_production_hardening.py

# Test Flatpak environment
FLATPAK_ID=io.github.tobagin.karere python3 scripts/test_production_hardening.py

# Test debug override
KARERE_PRODUCTION=1 KARERE_DEBUG=1 python3 scripts/test_production_hardening.py
```

### Build Testing

```bash
# Run all validation tests including production hardening
meson test -C builddir --suite validation

# Run only production hardening test
meson test -C builddir production-hardening
```

### Test Coverage

The production hardening test suite covers:
- Build environment detection accuracy
- Developer tools disabling in production
- Logging hardening and debug level blocking
- Flatpak environment detection
- GSettings integration and forced values
- Debug override functionality

## Deployment Considerations

### Flatpak Deployment
- Automatically detected as production environment
- Developer tools are force-disabled
- Debug logging is restricted to INFO level
- No additional configuration required

### System Package Deployment
- Detected as production when installed in system directories
- All production hardening features are active
- Can be overridden with `KARERE_DEBUG=1` if needed

### Development Deployment
- Detected when running from source directory
- All developer features are available
- Debug logging is enabled by default
- Settings UI shows all options

## Security Considerations

### Developer Tools Security
- WebKit developer tools provide access to JavaScript execution
- Console access could expose sensitive information
- Network inspection could reveal API details
- DOM manipulation could alter application behavior

### Debug Logging Security
- Debug logs may contain sensitive information
- User data could be inadvertently logged
- API keys or tokens might appear in debug output
- Performance impact of detailed logging

### Override Safety
- `KARERE_DEBUG=1` override should be used carefully
- Only enable debug features when necessary for troubleshooting
- Consider removing debug override in highly secure environments
- Monitor for unauthorized use of debug features

## Best Practices

### For Developers
1. Test both production and development modes
2. Never assume developer tools are available
3. Use appropriate log levels for different information
4. Implement graceful fallbacks when debug features are disabled

### For Distributors
1. Ensure production environment detection works correctly
2. Test that developer tools are properly disabled
3. Verify debug logging is appropriately restricted
4. Document any debug override usage

### For System Administrators
1. Understand the production hardening features
2. Use debug overrides sparingly and temporarily
3. Monitor for unexpected debug feature usage
4. Implement additional security measures if needed

## Troubleshooting

### Developer Tools Not Available
- Check if running in production environment
- Verify `KARERE_PRODUCTION` is not set
- Ensure not running from Flatpak
- Check that source directory structure is present

### Debug Logging Not Working
- Verify log level is set to DEBUG
- Check if running in production environment
- Use `KARERE_DEBUG=1` to override in production
- Ensure console logging is enabled

### Environment Detection Issues
- Review build environment detection logic
- Check environment variables
- Verify installation paths
- Test with different deployment methods

### Settings UI Missing Options
- Confirm running in development environment
- Check that developer settings are not hidden
- Verify production hardening is not active
- Test with `KARERE_DEV_MODE=1`

## Future Enhancements

Potential improvements to the production hardening system:
- Additional security features for production builds
- More granular control over debug features
- Integration with system security policies
- Enhanced logging security and filtering
- Automated security scanning integration