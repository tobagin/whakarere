#!/usr/bin/env python3
"""
Entry point script for Karere application.
"""

import sys
import signal
import argparse
import traceback
from .application import main
from . import __version__
from .crash_reporter import install_crash_handler

# Global variable to store the application instance for signal handling
_app_instance = None


def signal_handler(signum, frame):
    """Handle system signals for graceful shutdown."""
    global _app_instance
    
    signal_names = {
        signal.SIGINT: "SIGINT (Ctrl+C)",
        signal.SIGTERM: "SIGTERM (Terminate)",
        signal.SIGHUP: "SIGHUP (Hangup)"
    }
    
    signal_name = signal_names.get(signum, f"Signal {signum}")
    
    print(f"\nReceived {signal_name}. Initiating graceful shutdown...", file=sys.stderr)
    
    if _app_instance:
        try:
            # Try graceful shutdown first
            _app_instance.quit_application()
        except Exception as e:
            print(f"Error during graceful shutdown: {e}", file=sys.stderr)
            print("Forcing shutdown...", file=sys.stderr)
            try:
                _app_instance.force_quit()
            except Exception as e2:
                print(f"Error during force quit: {e2}", file=sys.stderr)
    
    # Exit with appropriate code
    exit_code = 130 if signum == signal.SIGINT else 128 + signum
    sys.exit(exit_code)


def setup_signal_handlers():
    """Set up signal handlers for graceful shutdown."""
    try:
        # Set up signal handlers
        signal.signal(signal.SIGINT, signal_handler)   # Ctrl+C
        signal.signal(signal.SIGTERM, signal_handler)  # Terminate
        
        # SIGHUP is not available on Windows
        if hasattr(signal, 'SIGHUP'):
            signal.signal(signal.SIGHUP, signal_handler)  # Hangup
        
        print("Signal handlers configured for graceful shutdown", file=sys.stderr)
        
    except Exception as e:
        print(f"Warning: Failed to set up signal handlers: {e}", file=sys.stderr)


def parse_args():
    """Parse command line arguments."""
    try:
        parser = argparse.ArgumentParser(
            description='Karere - GTK4 WhatsApp Client',
            prog='karere'
        )
        
        parser.add_argument(
            '--version', '-v',
            action='version',
            version=f'Karere {__version__}'
        )
        
        parser.add_argument(
            '--debug',
            action='store_true',
            help='Enable debug mode (show detailed error information)'
        )
        
        return parser.parse_args()
    except Exception as e:
        print(f"Error parsing command line arguments: {e}", file=sys.stderr)
        sys.exit(1)


def show_error_dialog(message, details=None):
    """Show a user-friendly error dialog using GTK."""
    try:
        import gi
        gi.require_version("Gtk", "4.0")
        gi.require_version("Adw", "1")
        from gi.repository import Gtk, Adw
        
        # Initialize GTK
        Gtk.init()
        
        # Create error dialog
        dialog = Adw.MessageDialog.new(
            None,
            "Karere Error",
            message
        )
        
        if details:
            dialog.set_body(f"{message}\n\nDetails: {details}")
        
        dialog.add_response("close", "Close")
        dialog.set_default_response("close")
        
        # Show dialog
        dialog.present()
        
        # Run a simple main loop to show the dialog
        app = Gtk.Application()
        app.run([])
        
    except Exception:
        # Fallback to console error if GTK fails
        print(f"Error: {message}", file=sys.stderr)
        if details:
            print(f"Details: {details}", file=sys.stderr)


def handle_startup_error(error, debug_mode=False):
    """Handle application startup errors with user-friendly messages."""
    error_type = type(error).__name__
    
    # Map common errors to user-friendly messages
    user_messages = {
        'ImportError': "Failed to import required system libraries. Please ensure GTK4 and other dependencies are installed.",
        'FileNotFoundError': "Required application files are missing. Please reinstall Karere.",
        'PermissionError': "Permission denied. Please check file permissions or run with appropriate privileges.",
        'ModuleNotFoundError': "Required Python modules are missing. Please ensure all dependencies are installed.",
        'RuntimeError': "Application startup failed. This may be due to missing system libraries or configuration issues.",
        'GLib.Error': "System library error occurred. Please check your GTK4 installation.",
        'OSError': "Operating system error occurred. Please check system resources and permissions."
    }
    
    # Get user-friendly message
    user_message = user_messages.get(error_type, "An unexpected error occurred during application startup.")
    
    # Show detailed error in debug mode
    if debug_mode:
        details = f"{error_type}: {str(error)}\n\nTraceback:\n{traceback.format_exc()}"
        show_error_dialog(user_message, details)
        print(f"Debug Info: {details}", file=sys.stderr)
    else:
        show_error_dialog(user_message)
        print(f"Error: {user_message}", file=sys.stderr)
        print(f"Run with --debug for more information.", file=sys.stderr)


if __name__ == "__main__":
    try:
        # Parse command line arguments
        args = parse_args()
        
        # Set up signal handlers for graceful shutdown
        setup_signal_handlers()
        
        # Initialize crash reporting (before starting the application)
        try:
            crash_reporter = install_crash_handler("Karere", enable_reporting=True)
            print("Crash reporting initialized", file=sys.stderr)
        except Exception as e:
            print(f"Warning: Failed to initialize crash reporting: {e}", file=sys.stderr)
        
        # Start the application with error handling
        try:
            result = main()
            sys.exit(result)
        except KeyboardInterrupt:
            print("\nApplication interrupted by user.", file=sys.stderr)
            sys.exit(130)  # Standard exit code for SIGINT
        except Exception as e:
            handle_startup_error(e, getattr(args, 'debug', False))
            sys.exit(1)
            
    except SystemExit:
        # Re-raise SystemExit (from argparse --help, --version, etc.)
        raise
    except Exception as e:
        # Handle any other unexpected errors
        print(f"Critical error in main entry point: {e}", file=sys.stderr)
        print(f"Please report this issue at https://github.com/tobagin/karere/issues", file=sys.stderr)
        sys.exit(1)