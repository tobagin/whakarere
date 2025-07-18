# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Build System and Commands

This project uses **Meson** as its build system and follows modern Python packaging conventions.

### Build Commands
```bash
# Set up build directory
meson setup builddir

# Compile the project
meson compile -C builddir

# Install the application
meson install -C builddir

# Run tests
meson test -C builddir
```

### Development Commands
```bash
# Run the application directly during development (after building)
PYTHONPATH=src python3 -m karere.application

# Or run the main entry point
python3 src/karere/main.py

# For development with Blueprint UI, you need to build first
meson setup builddir
meson compile -C builddir
```

## Project Structure and Architecture

**Karere** is a modern GTK4/Libadwaita WhatsApp client restructured as a proper Python library with Meson build system.

### Core Architecture
- **Frontend**: Python3 + GTK4 + Libadwaita + WebKit WebView 6.0
- **Backend**: None - directly loads web.whatsapp.com
- **Build System**: Meson
- **Target Platform**: Linux desktop

### Project Structure
```
karere/
├── src/karere/          # Main Python package
│   ├── ui/                # Blueprint UI files
│   │   ├── window.blp     # Main window Blueprint template
│   │   ├── karere.gresource.xml  # GResource definition
│   │   └── meson.build    # UI build configuration
│   ├── __init__.py         # Package metadata
│   ├── application.py      # Main application class with GResource loading
│   ├── window.py          # Main window implementation using Blueprint
│   └── main.py            # Entry point script
├── data/                   # Application data files
│   ├── icons/             # Application icons (16x16 to 512x512)
│   ├── *.desktop.in       # Desktop file template
│   ├── *.metainfo.xml.in  # AppStream metadata template
│   └── *.gschema.xml      # GSettings schema
├── po/                     # Internationalization
├── meson.build            # Main build configuration
└── karere.in           # Executable script template
```

### Key Components
- **WhakarereApplication**: Main Adwaita application class (extends Adw.Application)
- **WhakarereWindow**: Main window class (extends Adw.ApplicationWindow)
- **WebView**: WebKit WebView component displaying web.whatsapp.com

### Dependencies
- GTK 4.0 (latest stable)
- Libadwaita 1 (latest stable)
- WebKitGTK 6.0 (latest stable)
- Python 3 with GObject introspection

### Configuration
- GSettings schema: `io.github.tobagin.karere`
- Application ID: `io.github.tobagin.karere`
- Author: Thiago Fernandes
- License: GPL-3.0-or-later

### Development Notes
- Proper Python package structure with modular organization
- **Blueprint UI**: Uses .blp files for declarative UI definition, compiled to GTK UI files
- Meson build system with desktop integration and Blueprint compilation
- GResource system for bundling UI files with the application
- Icon sets for all standard sizes (16x16 through 512x512)
- AppStream metadata for software center integration
- GSettings for configuration persistence
- Internationalization support (gettext)

### Blueprint UI System
- UI defined in `src/karere/ui/window.blp` using Blueprint markup
- Compiled to GTK UI files during build process using `blueprint-compiler`
- Bundled into GResource file for efficient loading
- Templates use `@Gtk.Template` decorator for automatic widget binding
- Requires build step before running application in development

## Memories
- now it works