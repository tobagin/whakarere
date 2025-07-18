"""
Settings dialog for Karere application.
"""

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Gtk, Adw, Gio
from ._build_config import should_show_developer_settings, should_enable_developer_tools
from .crash_settings import CrashReportingSettingsDialog


@Gtk.Template(resource_path='/io/github/tobagin/karere/settings.ui')
class KarereSettingsDialog(Adw.PreferencesDialog):
    """Settings dialog for configuring application preferences."""
    
    __gtype_name__ = 'KarereSettingsDialog'
    
    theme_row = Gtk.Template.Child()
    persistent_cookies_row = Gtk.Template.Child()
    developer_tools_row = Gtk.Template.Child()
    
    def __init__(self, parent_window):
        super().__init__()
        self.parent_window = parent_window
        self.settings = Gio.Settings.new("io.github.tobagin.karere")
        
        self._setup_signals()
        self._load_settings()
        self._configure_production_hardening()
        self._add_crash_reporting_settings()
    
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
    
    def _configure_production_hardening(self):
        """Configure production hardening features."""
        # Hide developer tools in production builds
        if not should_show_developer_settings():
            self.developer_tools_row.set_visible(False)
            
        # Disable developer tools functionality in production
        if not should_enable_developer_tools():
            # Force disable developer tools setting
            self.settings.set_boolean("developer-tools", False)
            # Make the row insensitive if it's still visible
            self.developer_tools_row.set_sensitive(False)
    
    def _add_crash_reporting_settings(self):
        """Add crash reporting settings to the dialog."""
        try:
            # Get the first (and likely only) page
            page = self.get_page_by_name("general")
            if not page:
                # If no page found, create one
                page = Adw.PreferencesPage()
                page.set_title("General")
                page.set_name("general")
                self.add(page)
            
            # Create crash reporting group
            crash_group = Adw.PreferencesGroup()
            crash_group.set_title("Crash Reporting")
            crash_group.set_description("Configure crash reporting and debugging")
            
            # Create crash reporting settings row
            crash_settings_row = Adw.ActionRow()
            crash_settings_row.set_title("Crash Reporting Settings")
            crash_settings_row.set_subtitle("Configure crash report collection and management")
            
            # Create settings button
            crash_settings_button = Gtk.Button()
            crash_settings_button.set_label("Configure")
            crash_settings_button.set_valign(Gtk.Align.CENTER)
            crash_settings_button.connect("clicked", self._on_crash_settings_clicked)
            
            crash_settings_row.add_suffix(crash_settings_button)
            crash_group.add(crash_settings_row)
            
            # Add group to page
            page.add(crash_group)
            
        except Exception as e:
            print(f"Warning: Failed to add crash reporting settings: {e}")
    
    def _on_crash_settings_clicked(self, button):
        """Handle crash settings button click."""
        try:
            crash_settings_dialog = CrashReportingSettingsDialog(self.parent_window)
            crash_settings_dialog.present()
        except Exception as e:
            print(f"Error opening crash settings dialog: {e}")