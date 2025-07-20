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
from .logging_config import setup_logging, get_logger, set_log_level, disable_console_logging, enable_console_logging
from ._build_config import get_default_log_level, should_enable_debug_features
from .crash_reporter import get_crash_reporter
from .notification_manager import NotificationManager

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
        super().__init__(application_id=BUS_NAME)
        self.main_window = None
        self.notification_enabled = True
        
        # Set up logging
        self._setup_logging()
        self.logger = get_logger('application')
        self.logger.info("KarereApplication initializing")
        
        # Set up application to run in background
        self.set_flags(Gio.ApplicationFlags.HANDLES_OPEN)
        
    def _setup_logging(self):
        """Set up logging based on settings and build configuration with error handling."""
        # Default settings for fallback
        log_level = get_default_log_level()
        enable_file_logging = True
        enable_console_logging = True
        
        try:
            # Get logging settings from GSettings
            settings = Gio.Settings.new("io.github.tobagin.karere")
            
            # Get configured log level, with production-aware default
            try:
                user_log_level = settings.get_string("log-level")
                if user_log_level:
                    log_level = user_log_level
            except Exception as e:
                print(f"Warning: Could not read log-level setting, using default: {e}", file=sys.stderr)
            
            try:
                enable_file_logging = settings.get_boolean("enable-file-logging")
                enable_console_logging = settings.get_boolean("enable-console-logging")
            except Exception as e:
                print(f"Warning: Could not read logging settings, using defaults: {e}", file=sys.stderr)
                
        except Exception as e:
            print(f"Warning: Could not initialize GSettings, using default logging configuration: {e}", file=sys.stderr)
            print("This may happen if the GSettings schema is not installed.", file=sys.stderr)
        
        # Production hardening: disable debug logging in production unless explicitly enabled
        if log_level == "DEBUG" and not should_enable_debug_features():
            log_level = "INFO"
        
        # Validate log level
        valid_log_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if log_level not in valid_log_levels:
            print(f"Warning: Invalid log level '{log_level}', using INFO", file=sys.stderr)
            log_level = "INFO"
        
        try:
            # Set up logging with configured options
            setup_logging(
                log_level=getattr(__import__('logging'), log_level),
                enable_file_logging=enable_file_logging
            )
        except Exception as e:
            print(f"Error setting up logging: {e}", file=sys.stderr)
            # Fallback to basic logging
            import logging
            logging.basicConfig(level=logging.INFO)
        
        # Handle console logging setting
        try:
            if not enable_console_logging:
                disable_console_logging()
        except Exception as e:
            print(f"Warning: Could not disable console logging: {e}", file=sys.stderr)
        
    def do_activate(self):
        """Called when the application is activated with error handling."""
        self.logger.info("Application activated")
        
        try:
            # If main window exists but is hidden, show it
            if self.main_window and not self.main_window.get_visible():
                self.logger.info("Showing existing hidden window")
                try:
                    self.main_window.present()
                    return
                except Exception as e:
                    self.logger.error(f"Error showing existing window: {e}")
                    # Try to recreate the window
                    self.main_window = None
            
            # Create new window if it doesn't exist
            if not self.main_window:
                self.logger.info("Creating new main window")
                try:
                    from .window import KarereWindow
                    self.main_window = KarereWindow(self)
                    
                    # Restore window state
                    self.main_window.restore_window_state()
                    
                except ImportError as e:
                    self.logger.error(f"Failed to import window module: {e}")
                    self._show_error_dialog("Failed to load application window", 
                                           "Could not import required window components. Please check your installation.")
                    return
                except Exception as e:
                    self.logger.error(f"Failed to create main window: {e}")
                    self._show_error_dialog("Failed to create application window", 
                                           "Could not create the main application window. Please check your system configuration.")
                    return
            
            # Present the window
            try:
                self.main_window.present()
            except Exception as e:
                self.logger.error(f"Error presenting window: {e}")
                self._show_error_dialog("Failed to display window", 
                                       "Could not display the application window. Please try restarting the application.")
                
        except Exception as e:
            self.logger.error(f"Critical error in do_activate: {e}")
            self._show_error_dialog("Application Error", 
                                   "A critical error occurred while starting the application. Please try restarting.")

    def do_startup(self):
        """Called when the application starts up."""
        self.logger.info("Application startup beginning")
        try:
            Adw.Application.do_startup(self)
            Adw.init()  # Initialize libadwaita
            self.logger.info("Libadwaita initialized successfully")
        except Exception as e:
            self.logger.error(f"Error in do_startup: {e}")
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
            if os.path.exists(resource_path):
                self.logger.info(f"Loading UI resources from: {resource_path}")
                resource = Gio.Resource.load(resource_path)
                Gio.resources_register(resource)
                resource_loaded = True
                break
        
        if not resource_loaded:
            self.logger.error("No UI resources found!")
        
        # Set up application actions
        self._setup_actions()
        
        # Initialize notification manager
        self._setup_notification_manager()
    
    def _setup_actions(self):
        """Set up application-level actions."""
        self.logger.info("Setting up application actions")
        
        # Show window action (for notifications)
        show_action = Gio.SimpleAction.new("show-window", None)
        show_action.connect("activate", self._on_show_window_action)
        self.add_action(show_action)
        
        # Quit action
        quit_action = Gio.SimpleAction.new("quit", None)
        quit_action.connect("activate", self._on_quit_action)
        self.add_action(quit_action)
        
        # Crash reports action
        crash_reports_action = Gio.SimpleAction.new("crash-reports", None)
        crash_reports_action.connect("activate", self._on_crash_reports_action)
        self.add_action(crash_reports_action)
        
        # Set up keyboard shortcuts
        self.set_accels_for_action("app.quit", ["<Control>q"])
        self.logger.info("Application actions configured")
    
    def _setup_notification_manager(self):
        """Initialize the notification manager."""
        try:
            settings = Gio.Settings.new("io.github.tobagin.karere")
            self.notification_manager = NotificationManager(self, settings)
            self.logger.info("NotificationManager initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize NotificationManager: {e}")
            # Create a fallback minimal notification manager
            self.notification_manager = None
    
    def _on_show_window_action(self, action, param):
        """Handle show window action from notification."""
        self.logger.info("Show window action triggered")
        self.do_activate()
    
    def _on_quit_action(self, action, param):
        """Handle quit action."""
        self.logger.info("Quit action triggered")
        self.quit_application()
    
    def _on_crash_reports_action(self, action, param):
        """Handle crash reports action."""
        self.logger.info("Crash reports action triggered")
        self._show_crash_reports_dialog()
    
    def _show_crash_reports_dialog(self):
        """Show crash reports dialog."""
        try:
            crash_reporter = get_crash_reporter()
            if not crash_reporter:
                self._show_error_dialog("Crash Reports", "Crash reporting is not available.")
                return
            
            reports = crash_reporter.get_crash_reports()
            
            if not reports:
                self._show_error_dialog("Crash Reports", "No crash reports found.")
                return
            
            # Create crash reports dialog
            dialog = Adw.MessageDialog.new(
                self.main_window if self.main_window else None,
                "Crash Reports",
                f"Found {len(reports)} crash report(s):\n\n" +
                "\n".join([f"• {r['timestamp']}: {r['exception_type']}" for r in reports[:5]]) +
                (f"\n... and {len(reports) - 5} more" if len(reports) > 5 else "")
            )
            
            dialog.add_response("close", "Close")
            dialog.add_response("open", "Open Reports Folder")
            dialog.add_response("clear", "Clear All Reports")
            dialog.set_default_response("close")
            
            dialog.connect("response", self._on_crash_reports_response, crash_reporter)
            dialog.present()
            
        except Exception as e:
            self.logger.error(f"Failed to show crash reports dialog: {e}")
            self._show_error_dialog("Error", "Failed to display crash reports.")
    
    def _on_crash_reports_response(self, dialog, response, crash_reporter):
        """Handle crash reports dialog response."""
        if response == "open":
            try:
                reports_dir = crash_reporter.reports_dir
                Gio.AppInfo.launch_default_for_uri(f"file://{reports_dir}", None)
            except Exception as e:
                self.logger.error(f"Failed to open reports folder: {e}")
        elif response == "clear":
            try:
                crash_reporter.clear_crash_reports()
                self._show_error_dialog("Crash Reports", "All crash reports have been cleared.")
            except Exception as e:
                self.logger.error(f"Failed to clear crash reports: {e}")
        
        dialog.close()
    
    def _show_error_dialog(self, title, message):
        """Show an error dialog to the user."""
        try:
            # Create error dialog
            dialog = Adw.MessageDialog.new(
                self.main_window if self.main_window else None,
                title,
                message
            )
            
            dialog.add_response("close", "Close")
            dialog.set_default_response("close")
            
            # Show dialog
            dialog.present()
            
        except Exception as e:
            self.logger.error(f"Failed to show error dialog: {e}")
            # Fallback to console error
            print(f"Error: {title} - {message}", file=sys.stderr)
    
    def send_notification(self, title, message, icon_name=None, notification_type="system", **kwargs):
        """Send a desktop notification with error recovery and filtering."""
        if not self.notification_enabled:
            self.logger.debug("Notifications disabled, skipping")
            return
        
        # Use NotificationManager for filtering if available
        if hasattr(self, 'notification_manager') and self.notification_manager:
            try:
                # Check if notification should be sent
                if not self.notification_manager.should_show_notification(notification_type, **kwargs):
                    self.logger.debug(f"Notification filtered by NotificationManager: {title}")
                    return
                
                # Process message content through NotificationManager
                processed_message = self.notification_manager._process_message_content(message, notification_type, **kwargs)
                message = processed_message
                
                # Track the notification in the manager
                self.notification_manager.track_background_notification(notification_type, title)
                
            except Exception as e:
                self.logger.error(f"Error in NotificationManager filtering: {e}")
                # Continue with original notification if manager fails
            
        try:
            self.logger.info(f"Sending notification: {title} - {message}")
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
            self.logger.error(f"Failed to send notification: {e}")
            # Don't show error dialog for notification failures (too disruptive)
            # Just log the error and continue
    
    def recover_from_error(self, error_context="unknown"):
        """Implement error recovery mechanisms."""
        self.logger.info(f"Attempting recovery from error context: {error_context}")
        
        try:
            # Check if main window is responsive
            if self.main_window:
                try:
                    self.main_window.get_visible()
                    self.logger.info("Main window is responsive")
                except Exception as e:
                    self.logger.error(f"Main window not responsive: {e}")
                    # Try to recreate window
                    self._recreate_main_window()
            
            # Check WebView health if available
            if hasattr(self.main_window, 'webview') and self.main_window.webview:
                try:
                    uri = self.main_window.webview.get_uri()
                    if not uri or "whatsapp.com" not in uri:
                        self.logger.warning("WebView not on WhatsApp Web, reloading")
                        self._reload_whatsapp_web()
                except Exception as e:
                    self.logger.error(f"WebView health check failed: {e}")
                    
        except Exception as e:
            self.logger.error(f"Error during recovery: {e}")
    
    def _recreate_main_window(self):
        """Recreate the main window as a recovery mechanism."""
        try:
            if self.main_window:
                try:
                    self.main_window.destroy()
                except Exception:
                    pass
                self.main_window = None
            
            # Create new window
            self.do_activate()
            
        except Exception as e:
            self.logger.error(f"Failed to recreate main window: {e}")
            self._show_error_dialog("Recovery Error", 
                                   "Failed to recover application window. Please restart the application.")
    
    def _reload_whatsapp_web(self):
        """Reload WhatsApp Web as a recovery mechanism."""
        try:
            if hasattr(self.main_window, 'webview') and self.main_window.webview:
                self.main_window.webview.reload()
                self.logger.info("WhatsApp Web reloaded")
            else:
                self.logger.warning("Cannot reload WebView - not available")
                
        except Exception as e:
            self.logger.error(f"Failed to reload WhatsApp Web: {e}")
    
    
    def on_window_delete_event(self):
        """Handle window close event - hide instead of quit."""
        self.logger.info("Window close event - hiding to background")
        if self.main_window:
            self.main_window.set_visible(False)
        
        # Send background notification through NotificationManager
        self.send_notification(
            "Karere", 
            "Application is running in the background. Click here to show the window.",
            notification_type="background"
        )
        return True  # Prevent default close behavior
    
    def quit_application(self):
        """Actually quit the application with graceful shutdown."""
        self.logger.info("Initiating graceful application shutdown")
        
        try:
            # Perform graceful shutdown procedures
            self._graceful_shutdown()
            
        except Exception as e:
            self.logger.error(f"Error during graceful shutdown: {e}")
            # Continue with shutdown even if graceful shutdown fails
        
        finally:
            # Final cleanup and quit
            self.logger.info("Completing application shutdown")
            if self.main_window:
                try:
                    self.main_window.destroy()
                except Exception as e:
                    self.logger.error(f"Error destroying main window: {e}")
            
            self.quit()
    
    def _graceful_shutdown(self):
        """Perform graceful shutdown procedures."""
        self.logger.info("Performing graceful shutdown procedures")
        
        # Step 1: Save window state
        self._save_window_state()
        
        # Step 2: Clean up WebView resources
        self._cleanup_webview()
        
        # Step 3: Close crash reporter
        self._cleanup_crash_reporter()
        
        # Step 4: Clean up notification manager
        self._cleanup_notification_manager()
        
        # Step 5: Clean up logging
        self._cleanup_logging()
        
        # Step 6: Clean up settings
        self._cleanup_settings()
        
        # Step 7: Clean up temporary files
        self._cleanup_temporary_files()
        
        self.logger.info("Graceful shutdown procedures completed")
    
    def _save_window_state(self):
        """Save window state before shutdown."""
        try:
            if self.main_window:
                self.logger.info("Saving window state")
                
                # Get window geometry
                width = self.main_window.get_width()
                height = self.main_window.get_height()
                is_maximized = self.main_window.is_maximized()
                
                # Get window position (only if not maximized)
                x, y = -1, -1
                if not is_maximized:
                    # Get the window position
                    try:
                        surface = self.main_window.get_surface()
                        if surface:
                            # For Wayland/X11 compatibility, we'll use the surface position
                            # Note: Position saving might not work on all Wayland compositors
                            pass  # GTK4 doesn't provide direct position access
                    except Exception as e:
                        self.logger.debug(f"Could not get window position: {e}")
                
                # Save to settings
                settings = Gio.Settings.new("io.github.tobagin.karere")
                settings.set_int("window-width", width)
                settings.set_int("window-height", height)
                settings.set_boolean("window-maximized", is_maximized)
                settings.set_int("window-x", x)
                settings.set_int("window-y", y)
                
                # Force settings sync
                settings.sync()
                
                self.logger.info(f"Window state saved: {width}x{height} at ({x},{y}), maximized: {is_maximized}")
                
        except Exception as e:
            self.logger.error(f"Failed to save window state: {e}")
    
    def _cleanup_webview(self):
        """Clean up WebView resources."""
        try:
            if self.main_window and hasattr(self.main_window, 'cleanup_webview'):
                self.logger.info("Cleaning up WebView resources")
                
                # Use window's cleanup method
                self.main_window.cleanup_webview()
                    
                self.logger.info("WebView cleanup completed")
                    
        except Exception as e:
            self.logger.error(f"Failed to clean up WebView: {e}")
    
    def _cleanup_crash_reporter(self):
        """Clean up crash reporter resources."""
        try:
            from .crash_reporter import get_crash_reporter
            
            crash_reporter = get_crash_reporter()
            if crash_reporter:
                self.logger.info("Cleaning up crash reporter")
                
                # Disable crash reporting during shutdown
                crash_reporter.enable_reporting = False
                
                # Clean up any pending operations
                if hasattr(crash_reporter, 'cleanup'):
                    crash_reporter.cleanup()
                
                self.logger.info("Crash reporter cleanup completed")
                
        except Exception as e:
            self.logger.error(f"Failed to clean up crash reporter: {e}")
    
    def _cleanup_notification_manager(self):
        """Clean up notification manager resources."""
        try:
            if hasattr(self, 'notification_manager') and self.notification_manager:
                self.logger.info("Cleaning up notification manager")
                
                # Reset session state
                self.notification_manager.reset_session_state()
                
                # Clean up any pending operations
                if hasattr(self.notification_manager, 'cleanup'):
                    self.notification_manager.cleanup()
                
                self.logger.info("Notification manager cleanup completed")
                
        except Exception as e:
            self.logger.error(f"Failed to clean up notification manager: {e}")
    
    def _cleanup_logging(self):
        """Clean up logging resources."""
        try:
            self.logger.info("Cleaning up logging resources")
            
            # Flush all handlers
            import logging
            logging.shutdown()
            
            self.logger.info("Logging cleanup completed")
            
        except Exception as e:
            # Don't use logger here as it may be shutting down
            print(f"Failed to clean up logging: {e}", file=sys.stderr)
    
    def _cleanup_settings(self):
        """Clean up settings resources."""
        try:
            self.logger.info("Cleaning up settings resources")
            
            # Force settings sync
            settings = Gio.Settings.new("io.github.tobagin.karere")
            settings.sync()
            
            self.logger.info("Settings cleanup completed")
            
        except Exception as e:
            self.logger.error(f"Failed to clean up settings: {e}")
    
    def _cleanup_temporary_files(self):
        """Clean up temporary files and resources."""
        try:
            self.logger.info("Cleaning up temporary files")
            
            import os
            import tempfile
            from pathlib import Path
            
            # Clean up any temporary files we might have created
            temp_dir = Path(tempfile.gettempdir())
            karere_temp_files = temp_dir.glob("karere_*")
            
            for temp_file in karere_temp_files:
                try:
                    if temp_file.exists():
                        temp_file.unlink()
                        self.logger.debug(f"Removed temporary file: {temp_file}")
                except Exception as e:
                    self.logger.warning(f"Could not remove temporary file {temp_file}: {e}")
            
            self.logger.info("Temporary files cleanup completed")
            
        except Exception as e:
            self.logger.error(f"Failed to clean up temporary files: {e}")
    
    def force_quit(self):
        """Force quit the application without graceful shutdown."""
        self.logger.warning("Force quitting application without graceful shutdown")
        
        if self.main_window:
            try:
                self.main_window.destroy()
            except Exception:
                pass
        
        self.quit()
    


def main():
    """Main entry point for the application."""
    import sys
    from . import main as main_module
    
    # Create application instance
    app = KarereApplication()
    
    # Store app instance globally for signal handling
    main_module._app_instance = app
    
    # Run the application (activate will be called automatically)
    result = app.run(sys.argv)
    
    # Clear global reference
    main_module._app_instance = None
    
    return result


if __name__ == "__main__":
    exit(main())