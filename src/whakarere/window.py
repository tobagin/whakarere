"""
Main window for Whakarere application.
"""

import gi
import os

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
gi.require_version("WebKit", "6.0")

from gi.repository import Gtk, Adw, WebKit, Gio, GLib
from .settings import WhakarereSettingsDialog
from .about import create_about_dialog


@Gtk.Template(resource_path='/com/mudeprolinux/whakarere/window.ui')
class WhakarereWindow(Adw.ApplicationWindow):
    """Main application window containing the WebView."""
    
    __gtype_name__ = 'WhakarereWindow'
    
    webview_container = Gtk.Template.Child()
    
    def __init__(self, app):
        print("DEBUG: Window __init__ started")
        super().__init__(application=app)
        self.app = app
        print("DEBUG: Template initialized")
        
        # Initialize settings
        self.settings = Gio.Settings.new("com.mudeprolinux.whakarere")
        print("DEBUG: GSettings initialized")
        
        # Set up actions and webview
        self._setup_actions()
        self._setup_webview()
        self._apply_settings()
        print("DEBUG: Window __init__ completed")
    
    def _setup_actions(self):
        """Set up application actions."""
        print("DEBUG: Setting up actions")
        # Settings action
        settings_action = Gio.SimpleAction.new("settings", None)
        settings_action.connect("activate", self._on_settings_action)
        self.app.add_action(settings_action)
        
        # About action
        about_action = Gio.SimpleAction.new("about", None)
        about_action.connect("activate", self._on_about_action)
        self.app.add_action(about_action)
        print("DEBUG: Actions set up")
    
    def _setup_webview(self):
        """Set up the WebKit WebView with data manager for persistent cookies."""
        print("DEBUG: Setting up WebView")
        
        # Use XDG directories for Flatpak compatibility
        data_dir = os.environ.get('XDG_DATA_HOME', os.path.expanduser('~/.local/share')) + '/whakarere'
        cache_dir = os.environ.get('XDG_CACHE_HOME', os.path.expanduser('~/.cache')) + '/whakarere'
        
        # Ensure directories exist
        os.makedirs(data_dir, exist_ok=True)
        os.makedirs(cache_dir, exist_ok=True)
        print(f"DEBUG: Data dir: {data_dir}, Cache dir: {cache_dir}")
        
        # Create WebsiteDataManager with data directories
        self.website_data_manager = WebKit.WebsiteDataManager(
            base_data_directory=data_dir,
            base_cache_directory=cache_dir
        )
        
        # Create NetworkSession with the data manager
        self.network_session = WebKit.NetworkSession.new(data_directory=data_dir, cache_directory=cache_dir)
        
        # Create WebView 
        self.webview = WebKit.WebView.new()
        print("DEBUG: WebView created")
        
        # Get the cookie manager from the network session
        self.cookie_manager = self.network_session.get_cookie_manager()
        
        # Configure cookie persistence
        cookie_file = os.path.join(data_dir, 'cookies.sqlite')
        self.cookie_manager.set_persistent_storage(cookie_file, WebKit.CookiePersistentStorage.SQLITE)
        print("DEBUG: Cookie persistence configured")
        
        # Configure WebView settings
        webkit_settings = self.webview.get_settings()
        webkit_settings.set_enable_javascript(True)
        webkit_settings.set_enable_media_stream(True)
        webkit_settings.set_enable_webgl(True)
        webkit_settings.set_hardware_acceleration_policy(WebKit.HardwareAccelerationPolicy.ALWAYS)
        
        # Set user agent to avoid mobile version
        webkit_settings.set_user_agent("Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        print("DEBUG: WebView settings configured")
        
        # Add WebView to container with expand properties
        self.webview.set_vexpand(True)
        self.webview.set_hexpand(True)
        self.webview_container.append(self.webview)
        print("DEBUG: WebView added to container")
        
        # Load WhatsApp Web
        self.webview.load_uri("https://web.whatsapp.com")
        print("DEBUG: Loading WhatsApp Web")
    
    def _apply_settings(self):
        """Apply current settings to the application."""
        print("DEBUG: Applying settings")
        # Apply theme
        theme = self.settings.get_string("theme")
        self._apply_theme(theme)
        print(f"DEBUG: Applied theme: {theme}")
        
        # Apply developer tools setting
        if hasattr(self, 'webview'):
            webkit_settings = self.webview.get_settings()
            webkit_settings.set_enable_developer_extras(
                self.settings.get_boolean("developer-tools")
            )
            print("DEBUG: Developer tools setting applied")
    
    def _apply_theme(self, theme):
        """Apply the selected theme."""
        style_manager = Adw.StyleManager.get_default()
        
        if theme == "light":
            style_manager.set_color_scheme(Adw.ColorScheme.FORCE_LIGHT)
        elif theme == "dark":
            style_manager.set_color_scheme(Adw.ColorScheme.FORCE_DARK)
        else:  # follow-system
            style_manager.set_color_scheme(Adw.ColorScheme.DEFAULT)
    
    def _on_settings_action(self, action, param):
        """Handle settings action."""
        settings_dialog = WhakarereSettingsDialog(self)
        settings_dialog.present(self)
    
    def _on_about_action(self, action, param):
        """Handle about action."""
        about_dialog = create_about_dialog(self)
        about_dialog.present(self)