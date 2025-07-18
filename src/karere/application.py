#!/usr/bin/env python3
"""
Main application module for Karere.
"""

import gi
import sys
import os

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
gi.require_version("WebKit", "6.0")

from gi.repository import Gtk, Adw, Gio, GLib

# Determine app ID based on environment (for dev/prod distinction)
def get_app_id():
    """Get the appropriate app ID based on environment."""
    # Check if we're running in Flatpak
    flatpak_id = os.environ.get('FLATPAK_ID')
    if flatpak_id:
        return flatpak_id
    
    # Check for dev mode indicator
    if os.environ.get('KARERE_DEV_MODE') == '1':
        return "io.github.tobagin.karere.dev"
    
    # Default to production
    return "io.github.tobagin.karere"

BUS_NAME = get_app_id()


class KarereApplication(Adw.Application):
    """Main application class for Karere."""
    
    def __init__(self):
        print("DEBUG: KarereApplication.__init__ starting")
        super().__init__(application_id=BUS_NAME)
        print(f"DEBUG: Application ID set to: {BUS_NAME}")
        self.main_window = None
        self.notification_enabled = True
        
        # Set up application to run in background
        self.set_flags(Gio.ApplicationFlags.HANDLES_OPEN)
        print("DEBUG: KarereApplication.__init__ completed")
        
    def do_activate(self):
        """Called when the application is activated."""
        print("DEBUG: Application activated")
        
        # If main window exists but is hidden, show it
        if self.main_window and not self.main_window.get_visible():
            print("DEBUG: Showing existing hidden window")
            self.main_window.present()
            return
        
        # Create new window if it doesn't exist
        if not self.main_window:
            print("DEBUG: Creating new window")
            from .window import KarereWindow
            self.main_window = KarereWindow(self)
            print("DEBUG: Window created")
        
        print("DEBUG: Presenting window")
        self.main_window.present()
        print("DEBUG: Window presented")

    def do_startup(self):
        """Called when the application starts up."""
        print("DEBUG: do_startup called", flush=True)
        try:
            Adw.Application.do_startup(self)
            print("DEBUG: Parent do_startup completed", flush=True)
            Adw.init()  # Initialize libadwaita
            print("DEBUG: Adwaita initialized", flush=True)
        except Exception as e:
            print(f"DEBUG: Error in do_startup: {e}", flush=True)
            raise
        
        # Load GResource
        resource_paths = [
            '/app/lib/python3.12/site-packages/karere-resources.gresource',  # Flatpak installed path
            '/app/share/karere/karere-resources.gresource',  # Alternative Flatpak path
            '/usr/share/karere/karere-resources.gresource',  # System path
            os.path.join(os.path.dirname(__file__), '..', '..', 'builddir', 'src', 'karere', 'ui', 'karere-resources.gresource'),  # Development path
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
        
        # Set up application actions
        self._setup_actions()
    
    def _setup_actions(self):
        """Set up application-level actions."""
        print("DEBUG: Setting up application actions")
        
        # Show window action (for notifications)
        show_action = Gio.SimpleAction.new("show-window", None)
        show_action.connect("activate", self._on_show_window_action)
        self.add_action(show_action)
        
        # Quit action
        quit_action = Gio.SimpleAction.new("quit", None)
        quit_action.connect("activate", self._on_quit_action)
        self.add_action(quit_action)
        
        # Set up keyboard shortcuts
        self.set_accels_for_action("app.quit", ["<Control>q"])
        
        print("DEBUG: Application actions set up")
    
    def _on_show_window_action(self, action, param):
        """Handle show window action from notification."""
        print("DEBUG: Show window action triggered")
        self.do_activate()
    
    def _on_quit_action(self, action, param):
        """Handle quit action."""
        print("DEBUG: Quit action triggered")
        self.quit_application()
    
    def send_notification(self, title, message, icon_name=None):
        """Send a desktop notification."""
        if not self.notification_enabled:
            return
            
        try:
            notification = Gio.Notification()
            notification.set_title(title)
            notification.set_body(message)
            
            # Use dynamic app ID for icon if not specified
            if icon_name is None:
                icon_name = BUS_NAME
            
            # Add action to show window when notification is clicked
            notification.add_button("Show", "app.show-window")
            
            # Use simple ID for portal compatibility
            notification_id = f"msg-{int(GLib.get_monotonic_time())}"
            super().send_notification(notification_id, notification)
            
        except Exception as e:
            print(f"Failed to send notification: {e}")
    
    
    def on_window_delete_event(self):
        """Handle window close event - hide instead of quit."""
        print("DEBUG: Window close requested - hiding window instead of quitting")
        if self.main_window:
            self.main_window.set_visible(False)
        
        # Send notification to inform user app is running in background
        self.send_notification(
            "Karere", 
            "Application is running in the background. Click here to show the window."
        )
        return True  # Prevent default close behavior
    
    def quit_application(self):
        """Actually quit the application."""
        print("DEBUG: Quitting application completely")
        if self.main_window:
            self.main_window.destroy()
        self.quit()
    


def main():
    """Main entry point for the application."""
    import sys
    print("DEBUG: Creating KarereApplication")
    app = KarereApplication()
    print("DEBUG: Manually activating application")
    app.activate()
    print("DEBUG: Running application")
    result = app.run(sys.argv)
    print(f"DEBUG: Application.run() returned: {result}")
    return result


if __name__ == "__main__":
    exit(main())