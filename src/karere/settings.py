"""
Settings dialog for Karere application.
"""

import gi
import logging

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Gtk, Adw, Gio
from ._build_config import should_show_developer_settings, should_enable_developer_tools


@Gtk.Template(resource_path='/io/github/tobagin/karere/settings.ui')
class KarereSettingsDialog(Adw.PreferencesDialog):
    """Settings dialog for configuring application preferences."""
    
    __gtype_name__ = 'KarereSettingsDialog'
    
    # General page template children
    theme_row = Gtk.Template.Child()
    persistent_cookies_row = Gtk.Template.Child()
    developer_tools_row = Gtk.Template.Child()
    webview_group = Gtk.Template.Child()
    privacy_group = Gtk.Template.Child()
    
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
    
    # Spell checking page template children
    spell_checking_enabled_row = Gtk.Template.Child()
    spell_check_auto_detect_row = Gtk.Template.Child()
    current_languages_label = Gtk.Template.Child()
    add_language_button = Gtk.Template.Child()
    
    # Crash reporting page template children
    crash_reporting_enabled_row = Gtk.Template.Child()
    include_system_info_row = Gtk.Template.Child()
    include_logs_row = Gtk.Template.Child()
    view_stats_button = Gtk.Template.Child()
    clear_reports_button = Gtk.Template.Child()
    
    def __init__(self, parent_window):
        super().__init__()
        self.parent_window = parent_window
        self.settings = Gio.Settings.new("io.github.tobagin.karere")
        self.logger = logging.getLogger("karere.settings")
        
        self._setup_signals()
        self._load_settings()
        self._configure_production_hardening()
        self._load_spell_checking_settings()
        self._load_crash_reporting_settings()
    
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
        
        # Spell checking signals
        self.spell_checking_enabled_row.connect("notify::active", self._on_spell_checking_enabled_changed)
        self.spell_check_auto_detect_row.connect("notify::active", self._on_spell_check_auto_detect_changed)
        self.add_language_button.connect("clicked", self._on_add_language_clicked)
        
        # Crash reporting signals
        self.crash_reporting_enabled_row.connect("notify::active", self._on_crash_reporting_enabled_changed)
        self.include_system_info_row.connect("notify::active", self._on_include_system_info_changed)
        self.include_logs_row.connect("notify::active", self._on_include_logs_changed)
        self.view_stats_button.connect("clicked", self._on_view_stats_clicked)
        self.clear_reports_button.connect("clicked", self._on_clear_reports_clicked)
    
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
            # Hide the entire WebView group if all its contents are hidden
            self.webview_group.set_visible(False)
            
        # Disable developer tools functionality in production
        if not should_enable_developer_tools():
            # Force disable developer tools setting
            self.settings.set_boolean("developer-tools", False)
            # Make the row insensitive if it's still visible
            self.developer_tools_row.set_sensitive(False)
    
    def _load_spell_checking_settings(self):
        """Load spell checking settings from GSettings."""
        # Load enabled state
        spell_checking_enabled = self.settings.get_boolean("spell-checking-enabled")
        self.spell_checking_enabled_row.set_active(spell_checking_enabled)
        
        # Load auto-detect state
        auto_detect = self.settings.get_boolean("spell-checking-auto-detect")
        self.spell_check_auto_detect_row.set_active(auto_detect)
        
        # Update current languages display
        self._update_current_languages_display()
    
    def _update_current_languages_display(self):
        """Update the display of current spell checking languages."""
        try:
            import locale
            import os
            
            if self.settings.get_boolean("spell-checking-auto-detect"):
                # Get system locale
                try:
                    # Get the current locale
                    current_locale = locale.getlocale()[0]
                    if current_locale:
                        # Convert to spell checking format (e.g., en_US)
                        self.current_languages_label.set_text(f"Auto: {current_locale}")
                    else:
                        # Fallback to environment variables
                        lang = os.environ.get('LANG', 'en_US.UTF-8')
                        lang_code = lang.split('.')[0]  # Extract just the language part
                        self.current_languages_label.set_text(f"Auto: {lang_code}")
                except Exception as e:
                    self.logger.warning(f"Failed to get system locale: {e}")
                    self.current_languages_label.set_text("Auto: en_US")
            else:
                # Show custom languages
                languages = self.settings.get_strv("spell-checking-languages")
                if languages:
                    self.current_languages_label.set_text(", ".join(languages))
                else:
                    self.current_languages_label.set_text("None set")
        except Exception as e:
            self.logger.error(f"Error updating languages display: {e}")
            self.current_languages_label.set_text("Error")
    
    def _load_crash_reporting_settings(self):
        """Load crash reporting settings from crash reporter."""
        try:
            from .crash_reporter import get_crash_reporter
            crash_reporter = get_crash_reporter()
            
            if crash_reporter:
                # Load current crash reporting settings
                self.crash_reporting_enabled_row.set_active(crash_reporter.enable_reporting)
                self.include_system_info_row.set_active(crash_reporter.collect_system_info)
                self.include_logs_row.set_active(getattr(crash_reporter, 'collect_logs', False))
            else:
                # Default values if crash reporter not available
                self.crash_reporting_enabled_row.set_active(True)
                self.include_system_info_row.set_active(True)
                self.include_logs_row.set_active(False)
                
        except Exception as e:
            self.logger.warning(f"Failed to load crash reporting settings: {e}")
            # Set default values on error
            self.crash_reporting_enabled_row.set_active(True)
            self.include_system_info_row.set_active(True)
            self.include_logs_row.set_active(False)
    
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
    
    # Spell checking signal handlers
    def _on_spell_checking_enabled_changed(self, row, param):
        """Handle spell checking enabled toggle."""
        enabled = row.get_active()
        self.settings.set_boolean("spell-checking-enabled", enabled)
        self.logger.info(f"Spell checking {'enabled' if enabled else 'disabled'}")
        
        # Notify window to update WebView spell checking
        if hasattr(self.parent_window, '_update_spell_checking'):
            self.parent_window._update_spell_checking()
    
    def _on_spell_check_auto_detect_changed(self, row, param):
        """Handle spell check auto-detect toggle."""
        auto_detect = row.get_active()
        self.settings.set_boolean("spell-checking-auto-detect", auto_detect)
        self.logger.info(f"Spell check auto-detect {'enabled' if auto_detect else 'disabled'}")
        
        # Update the languages display
        self._update_current_languages_display()
        
        # Notify window to update WebView spell checking
        if hasattr(self.parent_window, '_update_spell_checking'):
            self.parent_window._update_spell_checking()
    
    def _on_add_language_clicked(self, button):
        """Handle add language button click."""
        # For now, show a simple message dialog explaining the feature
        # This could be enhanced later with a proper language selection dialog
        dialog = Adw.MessageDialog.new(self.parent_window)
        dialog.set_heading("Add Spell Check Language")
        dialog.set_body("Custom language selection is not yet implemented.\n\n"
                       "To add languages, disable auto-detect and manually edit the "
                       "spell-checking-languages setting using dconf-editor or gsettings.\n\n"
                       "Example language codes: en_US, es_ES, fr_FR, de_DE")
        dialog.add_response("ok", "OK")
        dialog.present()
    
    # Crash reporting signal handlers
    def _on_crash_reporting_enabled_changed(self, row, param):
        """Handle crash reporting enabled toggle."""
        try:
            from .crash_reporter import get_crash_reporter
            crash_reporter = get_crash_reporter()
            if crash_reporter:
                crash_reporter.enable_reporting = row.get_active()
                self.logger.info(f"Crash reporting {'enabled' if row.get_active() else 'disabled'}")
        except Exception as e:
            self.logger.error(f"Error updating crash reporting enabled: {e}")
    
    def _on_include_system_info_changed(self, row, param):
        """Handle include system info toggle."""
        try:
            from .crash_reporter import get_crash_reporter
            crash_reporter = get_crash_reporter()
            if crash_reporter:
                crash_reporter.collect_system_info = row.get_active()
                self.logger.info(f"Include system info {'enabled' if row.get_active() else 'disabled'}")
        except Exception as e:
            self.logger.error(f"Error updating include system info: {e}")
    
    def _on_include_logs_changed(self, row, param):
        """Handle include logs toggle."""
        try:
            from .crash_reporter import get_crash_reporter
            crash_reporter = get_crash_reporter()
            if crash_reporter:
                # Use setattr since collect_logs might not exist
                setattr(crash_reporter, 'collect_logs', row.get_active())
                self.logger.info(f"Include logs {'enabled' if row.get_active() else 'disabled'}")
        except Exception as e:
            self.logger.error(f"Error updating include logs: {e}")
    
    def _on_view_stats_clicked(self, button):
        """Handle view statistics button click."""
        try:
            from .crash_reporter import get_crash_reporter
            crash_reporter = get_crash_reporter()
            if crash_reporter:
                reports = crash_reporter.get_crash_reports()
                total_reports = len(reports)
                last_crash = reports[-1]['timestamp'] if reports else 'None'
                
                # Create a simple info dialog with statistics
                dialog = Adw.MessageDialog.new(self.parent_window)
                dialog.set_heading("Crash Report Statistics")
                dialog.set_body(f"Reports stored: {total_reports}\n"
                               f"Last crash: {last_crash}")
                dialog.add_response("ok", "OK")
                dialog.present()
        except Exception as e:
            self.logger.error(f"Error viewing crash statistics: {e}")
    
    def _on_clear_reports_clicked(self, button):
        """Handle clear reports button click."""
        try:
            from .crash_reporter import get_crash_reporter
            crash_reporter = get_crash_reporter()
            if crash_reporter:
                # Show confirmation dialog
                dialog = Adw.MessageDialog.new(self.parent_window)
                dialog.set_heading("Clear Crash Reports")
                dialog.set_body("Are you sure you want to delete all stored crash reports? This action cannot be undone.")
                dialog.add_response("cancel", "Cancel")
                dialog.add_response("delete", "Delete All")
                dialog.set_response_appearance("delete", Adw.ResponseAppearance.DESTRUCTIVE)
                dialog.connect("response", self._on_clear_reports_response)
                dialog.present()
        except Exception as e:
            self.logger.error(f"Error clearing crash reports: {e}")
    
    def _on_clear_reports_response(self, dialog, response):
        """Handle clear reports confirmation response."""
        if response == "delete":
            try:
                from .crash_reporter import get_crash_reporter
                crash_reporter = get_crash_reporter()
                if crash_reporter:
                    crash_reporter.clear_crash_reports()
                    self.logger.info("All crash reports cleared")
            except Exception as e:
                self.logger.error(f"Error clearing crash reports: {e}")