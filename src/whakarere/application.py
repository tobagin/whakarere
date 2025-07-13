#!/usr/bin/env python3
"""
Main application module for Whakarere.
"""

import gi
import sys
import os

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
gi.require_version("WebKit", "6.0")

from gi.repository import Gtk, Adw, Gio

BUS_NAME = "com.mudeprolinux.whakarere"


class WhakarereApplication(Adw.Application):
    """Main application class for Whakarere."""
    
    def __init__(self):
        super().__init__(application_id=BUS_NAME)
        
    def do_activate(self):
        """Called when the application is activated."""
        print("DEBUG: Application activated")
        win = self.props.active_window
        if not win:
            print("DEBUG: Creating new window")
            from .window import WhakarereWindow
            win = WhakarereWindow(self)
            print("DEBUG: Window created")
        print("DEBUG: Presenting window")
        win.present()
        print("DEBUG: Window presented")

    def do_startup(self):
        """Called when the application starts up."""
        print("DEBUG: do_startup called", flush=True)
        Adw.Application.do_startup(self)
        print("DEBUG: Initializing Adwaita", flush=True)
        Adw.init()  # Initialize libadwaita
        print("DEBUG: Adwaita initialized", flush=True)
        
        # Load GResource
        resource_paths = [
            '/app/lib/python3.12/site-packages/whakarere-resources.gresource',  # Flatpak installed path
            '/app/share/whakarere/whakarere-resources.gresource',  # Alternative Flatpak path
            '/usr/share/whakarere/whakarere-resources.gresource',  # System path
            os.path.join(os.path.dirname(__file__), '..', '..', 'builddir', 'src', 'whakarere', 'ui', 'whakarere-resources.gresource'),  # Development path
        ]
        
        resource_loaded = False
        for resource_path in resource_paths:
            print(f"Checking resource path: {resource_path}")
            if os.path.exists(resource_path):
                print(f"Loading resource from: {resource_path}")
                resource = Gio.Resource.load(resource_path)
                Gio.resources_register(resource)
                resource_loaded = True
                break
        
        if not resource_loaded:
            print("ERROR: No UI resources found!")


def main():
    """Main entry point for the application."""
    print("DEBUG: Creating WhakarereApplication")
    app = WhakarereApplication()
    print("DEBUG: Running application")
    result = app.run()
    print(f"DEBUG: Application.run() returned: {result}")
    return result


if __name__ == "__main__":
    exit(main())