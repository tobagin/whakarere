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
    
    # General page template children
    theme_row = Gtk.Template.Child()
    persistent_cookies_row = Gtk.Template.Child()
    developer_tools_row = Gtk.Template.Child()
    
    # Notifications page template children
    message_notifications_row = Gtk.Template.Child()
    background_frequency_row = Gtk.Template.Child()
    system_notifications_row = Gtk.Template.Child()
    message_settings_group = Gtk.Template.Child()
    message_preview_row = Gtk.Template.Child()
    message_preview_length_row = Gtk.Template.Child()
    message_when_focused_row = Gtk.Template.Child()
    dnd_enabled_row = Gtk.Template.Child()
    dnd_background_row = Gtk.Template.Child()
    dnd_schedule_row = Gtk.Template.Child()
    dnd_start_entry = Gtk.Template.Child()
    dnd_end_entry = Gtk.Template.Child()
    
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
        # General settings signals
        self.theme_row.connect("notify::selected", self._on_theme_changed)
        self.persistent_cookies_row.connect("notify::active", self._on_persistent_cookies_changed)
        self.developer_tools_row.connect("notify::active", self._on_developer_tools_changed)
        
        # Notification settings signals
        self.message_notifications_row.connect("notify::active", self._on_message_notifications_changed)
        self.background_frequency_row.connect("notify::selected", self._on_background_frequency_changed)
        self.system_notifications_row.connect("notify::active", self._on_system_notifications_changed)
        self.message_preview_row.connect("notify::active", self._on_message_preview_changed)
        self.message_preview_length_row.connect("notify::value", self._on_message_preview_length_changed)
        self.message_when_focused_row.connect("notify::active", self._on_message_when_focused_changed)
        
        # DND settings signals
        self.dnd_enabled_row.connect("notify::active", self._on_dnd_enabled_changed)
        self.dnd_background_row.connect("notify::active", self._on_dnd_background_changed)
        self.dnd_schedule_row.connect("notify::active", self._on_dnd_schedule_changed)
        self.dnd_start_entry.connect("notify::text", self._on_dnd_start_time_changed)
        self.dnd_end_entry.connect("notify::text", self._on_dnd_end_time_changed)
    
    def _load_settings(self):
        """Load current settings from GSettings."""
        # Load general settings
        theme = self.settings.get_string("theme")
        theme_index = {"follow-system": 0, "light": 1, "dark": 2}.get(theme, 0)
        self.theme_row.set_selected(theme_index)
        
        self.persistent_cookies_row.set_active(self.settings.get_boolean("persistent-cookies"))
        self.developer_tools_row.set_active(self.settings.get_boolean("developer-tools"))
        
        # Load notification settings
        self.message_notifications_row.set_active(self.settings.get_boolean("show-message-notifications"))
        
        bg_freq = self.settings.get_string("background-notification-frequency")
        bg_freq_index = {"always": 0, "first-session-only": 1, "never": 2}.get(bg_freq, 0)
        self.background_frequency_row.set_selected(bg_freq_index)
        
        self.system_notifications_row.set_active(self.settings.get_boolean("show-system-notifications"))
        self.message_preview_row.set_active(self.settings.get_boolean("message-preview-enabled"))
        self.message_preview_length_row.set_value(self.settings.get_int("message-preview-length"))
        self.message_when_focused_row.set_active(self.settings.get_boolean("message-notification-when-focused"))
        
        # Load DND settings
        self.dnd_enabled_row.set_active(self.settings.get_boolean("dnd-mode-enabled"))
        self.dnd_background_row.set_active(self.settings.get_boolean("dnd-allow-background-notifications"))
        self.dnd_schedule_row.set_active(self.settings.get_boolean("dnd-schedule-enabled"))
        self.dnd_start_entry.set_text(self.settings.get_string("dnd-start-time"))
        self.dnd_end_entry.set_text(self.settings.get_string("dnd-end-time"))
        
        # Update DND status and visibility
        self._update_dnd_status()
        self._update_dnd_visibility()
        self._update_message_settings_visibility()
    
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
    
    # Notification settings signal handlers
    def _on_message_notifications_changed(self, row, param):
        """Handle message notifications toggle."""
        enabled = row.get_active()
        self.settings.set_boolean("show-message-notifications", enabled)
        self._update_message_settings_visibility()
    
    def _on_background_frequency_changed(self, row, param):
        """Handle background notification frequency change."""
        selected = row.get_selected()
        frequencies = ["always", "first-session-only", "never"]
        if selected < len(frequencies):
            frequency = frequencies[selected]
            self.settings.set_string("background-notification-frequency", frequency)
    
    def _on_system_notifications_changed(self, row, param):
        """Handle system notifications toggle."""
        self.settings.set_boolean("show-system-notifications", row.get_active())
    
    def _on_message_preview_changed(self, row, param):
        """Handle message preview toggle."""
        enabled = row.get_active()
        self.settings.set_boolean("message-preview-enabled", enabled)
        self._update_message_preview_length_visibility()
    
    def _on_message_preview_length_changed(self, row, param):
        """Handle message preview length change."""
        self.settings.set_int("message-preview-length", int(row.get_value()))
    
    def _on_message_when_focused_changed(self, row, param):
        """Handle message when focused toggle."""
        self.settings.set_boolean("message-notification-when-focused", row.get_active())
    
    # DND settings signal handlers
    def _on_dnd_enabled_changed(self, row, param):
        """Handle DND enabled toggle."""
        enabled = row.get_active()
        self.settings.set_boolean("dnd-mode-enabled", enabled)
        self._update_dnd_status()
        self._update_dnd_visibility()
    
    def _on_dnd_background_changed(self, row, param):
        """Handle DND background notifications toggle."""
        self.settings.set_boolean("dnd-allow-background-notifications", row.get_active())
    
    def _on_dnd_schedule_changed(self, row, param):
        """Handle DND schedule toggle."""
        enabled = row.get_active()
        self.settings.set_boolean("dnd-schedule-enabled", enabled)
        self._update_dnd_time_visibility()
    
    def _on_dnd_start_time_changed(self, entry, param):
        """Handle DND start time change."""
        time_text = entry.get_text()
        if self._validate_time_format(time_text):
            self.settings.set_string("dnd-start-time", time_text)
            self._update_dnd_status()
    
    def _on_dnd_end_time_changed(self, entry, param):
        """Handle DND end time change."""
        time_text = entry.get_text()
        if self._validate_time_format(time_text):
            self.settings.set_string("dnd-end-time", time_text)
            self._update_dnd_status()
    
    def _validate_time_format(self, time_str):
        """Validate time format (HH:MM)."""
        try:
            parts = time_str.split(":")
            if len(parts) != 2:
                return False
            hours, minutes = int(parts[0]), int(parts[1])
            return 0 <= hours <= 23 and 0 <= minutes <= 59
        except (ValueError, IndexError):
            return False
    
    def _update_dnd_status(self):
        """Update DND status display."""
        # DND status page was removed - this method now only serves as a placeholder
        # for potential future DND status updates
        pass
    
    def _update_dnd_visibility(self):
        """Update visibility of DND sub-options based on main DND toggle."""
        dnd_enabled = self.settings.get_boolean("dnd-mode-enabled")
        
        # Show/hide DND sub-options
        self.dnd_background_row.set_visible(dnd_enabled)
        self.dnd_schedule_row.set_visible(dnd_enabled)
        
        # Update time entries visibility
        self._update_dnd_time_visibility()
    
    def _update_dnd_time_visibility(self):
        """Update visibility of DND time entries based on scheduled DND toggle."""
        dnd_enabled = self.settings.get_boolean("dnd-mode-enabled")
        schedule_enabled = self.settings.get_boolean("dnd-schedule-enabled")
        
        # Show time entries only if both DND and scheduled DND are enabled
        show_times = dnd_enabled and schedule_enabled
        self.dnd_start_entry.set_visible(show_times)
        self.dnd_end_entry.set_visible(show_times)
    
    def _update_message_settings_visibility(self):
        """Update visibility of message settings based on message notifications toggle."""
        message_notifications_enabled = self.settings.get_boolean("show-message-notifications")
        
        # Show/hide entire message settings group
        self.message_settings_group.set_visible(message_notifications_enabled)
        
        # Update preview length visibility (only if group is visible)
        if message_notifications_enabled:
            self._update_message_preview_length_visibility()
    
    def _update_message_preview_length_visibility(self):
        """Update visibility of preview length based on message notifications and preview toggles."""
        message_notifications_enabled = self.settings.get_boolean("show-message-notifications")
        message_preview_enabled = self.settings.get_boolean("message-preview-enabled")
        
        # Show preview length only if both message notifications and preview are enabled
        show_preview_length = message_notifications_enabled and message_preview_enabled
        self.message_preview_length_row.set_visible(show_preview_length)