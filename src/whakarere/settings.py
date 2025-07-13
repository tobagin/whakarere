"""
Settings dialog for Whakarere application.
"""

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Gtk, Adw, Gio


@Gtk.Template(resource_path='/com/mudeprolinux/whakarere/settings.ui')
class WhakarereSettingsDialog(Adw.PreferencesDialog):
    """Settings dialog for configuring application preferences."""
    
    __gtype_name__ = 'WhakarereSettingsDialog'
    
    theme_row = Gtk.Template.Child()
    persistent_cookies_row = Gtk.Template.Child()
    developer_tools_row = Gtk.Template.Child()
    
    def __init__(self, parent_window):
        super().__init__()
        self.parent_window = parent_window
        self.settings = Gio.Settings.new("com.mudeprolinux.whakarere")
        
        self._setup_signals()
        self._load_settings()
    
    def _setup_signals(self):
        """Set up signal connections."""
        self.theme_row.connect("notify::selected", self._on_theme_changed)
        self.persistent_cookies_row.connect("notify::active", self._on_persistent_cookies_changed)
        self.developer_tools_row.connect("notify::active", self._on_developer_tools_changed)
    
    def _load_settings(self):
        """Load current settings from GSettings."""
        # Load theme setting
        theme = self.settings.get_string("theme")
        theme_index = {"follow-system": 0, "light": 1, "dark": 2}.get(theme, 0)
        self.theme_row.set_selected(theme_index)
        
        # Load persistent cookies setting
        self.persistent_cookies_row.set_active(self.settings.get_boolean("persistent-cookies"))
        
        # Load developer tools setting
        self.developer_tools_row.set_active(self.settings.get_boolean("developer-tools"))
    
    def _on_theme_changed(self, row, param):
        """Handle theme selection change."""
        selected = row.get_selected()
        themes = ["follow-system", "light", "dark"]
        if selected < len(themes):
            theme = themes[selected]
            self.settings.set_string("theme", theme)
            self._apply_theme(theme)
    
    def _on_persistent_cookies_changed(self, row, param):
        """Handle persistent cookies toggle."""
        self.settings.set_boolean("persistent-cookies", row.get_active())
    
    def _on_developer_tools_changed(self, row, param):
        """Handle developer tools toggle."""
        active = row.get_active()
        self.settings.set_boolean("developer-tools", active)
        # Apply to webview if it exists
        if hasattr(self.parent_window, 'webview') and self.parent_window.webview:
            settings = self.parent_window.webview.get_settings()
            settings.set_enable_developer_extras(active)
    
    def _apply_theme(self, theme):
        """Apply the selected theme."""
        style_manager = Adw.StyleManager.get_default()
        
        if theme == "light":
            style_manager.set_color_scheme(Adw.ColorScheme.FORCE_LIGHT)
        elif theme == "dark":
            style_manager.set_color_scheme(Adw.ColorScheme.FORCE_DARK)
        else:  # follow-system
            style_manager.set_color_scheme(Adw.ColorScheme.DEFAULT)