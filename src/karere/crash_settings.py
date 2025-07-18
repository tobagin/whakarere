#!/usr/bin/env python3
"""
Crash reporting settings dialog for Karere application.
"""

import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Gtk, Adw, Gio
from .logging_config import get_logger
from .crash_reporter import get_crash_reporter
from ._build_config import is_development_build


class CrashReportingSettingsDialog(Adw.PreferencesWindow):
    """Dialog for managing crash reporting settings."""
    
    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self.logger = get_logger('crash_settings')
        
        # Set up dialog
        self.set_title("Crash Reporting Settings")
        self.set_default_size(600, 400)
        self.set_transient_for(parent)
        self.set_modal(True)
        
        # Initialize settings
        self.settings = Gio.Settings.new("io.github.tobagin.karere")
        self.crash_reporter = get_crash_reporter()
        
        # Create UI
        self._create_ui()
        
        # Load current settings
        self._load_settings()
    
    def _create_ui(self):
        """Create the settings UI."""
        # Main preferences page
        page = Adw.PreferencesPage()
        page.set_title("Crash Reporting")
        page.set_icon_name("dialog-warning-symbolic")
        self.add(page)
        
        # Crash reporting group
        crash_group = Adw.PreferencesGroup()
        crash_group.set_title("Crash Reporting")
        crash_group.set_description("Configure how crash reports are handled")
        page.add(crash_group)
        
        # Enable crash reporting
        self.enable_reporting_row = Adw.SwitchRow()
        self.enable_reporting_row.set_title("Enable Crash Reporting")
        self.enable_reporting_row.set_subtitle("Collect crash information to help improve the application")
        self.enable_reporting_row.connect("notify::active", self._on_enable_reporting_changed)
        crash_group.add(self.enable_reporting_row)
        
        # Collect system information
        self.collect_system_info_row = Adw.SwitchRow()
        self.collect_system_info_row.set_title("Collect System Information")
        self.collect_system_info_row.set_subtitle("Include system details in crash reports")
        self.collect_system_info_row.connect("notify::active", self._on_collect_system_info_changed)
        crash_group.add(self.collect_system_info_row)
        
        # Statistics group
        stats_group = Adw.PreferencesGroup()
        stats_group.set_title("Statistics")
        stats_group.set_description("Information about crash reports")
        page.add(stats_group)
        
        # Crash reports count
        self.reports_count_row = Adw.ActionRow()
        self.reports_count_row.set_title("Crash Reports")
        self.reports_count_row.set_subtitle("Number of crash reports stored")
        stats_group.add(self.reports_count_row)
        
        # Actions group
        actions_group = Adw.PreferencesGroup()
        actions_group.set_title("Actions")
        actions_group.set_description("Manage crash reports")
        page.add(actions_group)
        
        # View reports
        view_reports_row = Adw.ActionRow()
        view_reports_row.set_title("View Reports")
        view_reports_row.set_subtitle("Open crash reports directory")
        view_reports_button = Gtk.Button()
        view_reports_button.set_label("Open")
        view_reports_button.set_valign(Gtk.Align.CENTER)
        view_reports_button.connect("clicked", self._on_view_reports_clicked)
        view_reports_row.add_suffix(view_reports_button)
        actions_group.add(view_reports_row)
        
        # Clear reports
        clear_reports_row = Adw.ActionRow()
        clear_reports_row.set_title("Clear Reports")
        clear_reports_row.set_subtitle("Delete all crash reports")
        clear_reports_button = Gtk.Button()
        clear_reports_button.set_label("Clear")
        clear_reports_button.set_valign(Gtk.Align.CENTER)
        clear_reports_button.add_css_class("destructive-action")
        clear_reports_button.connect("clicked", self._on_clear_reports_clicked)
        clear_reports_row.add_suffix(clear_reports_button)
        actions_group.add(clear_reports_row)
        
        # Development group (only in dev mode)
        if is_development_build():
            dev_group = Adw.PreferencesGroup()
            dev_group.set_title("Development")
            dev_group.set_description("Testing and debugging features")
            page.add(dev_group)
            
            # Test crash
            test_crash_row = Adw.ActionRow()
            test_crash_row.set_title("Test Crash")
            test_crash_row.set_subtitle("Generate a test crash for testing")
            test_crash_button = Gtk.Button()
            test_crash_button.set_label("Test")
            test_crash_button.set_valign(Gtk.Align.CENTER)
            test_crash_button.add_css_class("destructive-action")
            test_crash_button.connect("clicked", self._on_test_crash_clicked)
            test_crash_row.add_suffix(test_crash_button)
            dev_group.add(test_crash_row)
    
    def _load_settings(self):
        """Load current settings."""
        try:
            # Load settings from GSettings
            enable_reporting = self.settings.get_boolean("enable-crash-reporting")
            collect_system_info = self.settings.get_boolean("collect-system-info")
            
            self.enable_reporting_row.set_active(enable_reporting)
            self.collect_system_info_row.set_active(collect_system_info)
            
            # Update crash reporter settings
            if self.crash_reporter:
                self.crash_reporter.enable_reporting = enable_reporting
                self.crash_reporter.collect_system_info = collect_system_info
            
            # Update statistics
            self._update_statistics()
            
        except Exception as e:
            self.logger.error(f"Failed to load crash reporting settings: {e}")
    
    def _update_statistics(self):
        """Update statistics display."""
        try:
            if self.crash_reporter:
                reports = self.crash_reporter.get_crash_reports()
                count = len(reports)
                self.reports_count_row.set_subtitle(f"{count} crash report(s) stored")
            else:
                self.reports_count_row.set_subtitle("Crash reporting not available")
        except Exception as e:
            self.logger.error(f"Failed to update statistics: {e}")
            self.reports_count_row.set_subtitle("Error loading statistics")
    
    def _on_enable_reporting_changed(self, row, pspec):
        """Handle enable reporting setting change."""
        try:
            enable_reporting = row.get_active()
            self.settings.set_boolean("enable-crash-reporting", enable_reporting)
            
            if self.crash_reporter:
                self.crash_reporter.enable_reporting = enable_reporting
            
            # Update sensitivity of other settings
            self.collect_system_info_row.set_sensitive(enable_reporting)
            
            self.logger.info(f"Crash reporting {'enabled' if enable_reporting else 'disabled'}")
            
        except Exception as e:
            self.logger.error(f"Failed to update crash reporting setting: {e}")
    
    def _on_collect_system_info_changed(self, row, pspec):
        """Handle collect system info setting change."""
        try:
            collect_system_info = row.get_active()
            self.settings.set_boolean("collect-system-info", collect_system_info)
            
            if self.crash_reporter:
                self.crash_reporter.collect_system_info = collect_system_info
            
            self.logger.info(f"System info collection {'enabled' if collect_system_info else 'disabled'}")
            
        except Exception as e:
            self.logger.error(f"Failed to update system info collection setting: {e}")
    
    def _on_view_reports_clicked(self, button):
        """Handle view reports button click."""
        try:
            if self.crash_reporter:
                reports_dir = self.crash_reporter.reports_dir
                Gio.AppInfo.launch_default_for_uri(f"file://{reports_dir}", None)
            else:
                self._show_error("Crash reporting not available")
        except Exception as e:
            self.logger.error(f"Failed to open reports directory: {e}")
            self._show_error("Failed to open reports directory")
    
    def _on_clear_reports_clicked(self, button):
        """Handle clear reports button click."""
        try:
            if not self.crash_reporter:
                self._show_error("Crash reporting not available")
                return
            
            # Show confirmation dialog
            dialog = Adw.MessageDialog.new(
                self,
                "Clear Crash Reports",
                "Are you sure you want to delete all crash reports? This action cannot be undone."
            )
            
            dialog.add_response("cancel", "Cancel")
            dialog.add_response("clear", "Clear All")
            dialog.set_response_appearance("clear", Adw.ResponseAppearance.DESTRUCTIVE)
            dialog.set_default_response("cancel")
            
            dialog.connect("response", self._on_clear_reports_response)
            dialog.present()
            
        except Exception as e:
            self.logger.error(f"Failed to show clear reports dialog: {e}")
            self._show_error("Failed to clear reports")
    
    def _on_clear_reports_response(self, dialog, response):
        """Handle clear reports confirmation response."""
        if response == "clear":
            try:
                if self.crash_reporter:
                    self.crash_reporter.clear_crash_reports()
                    self._update_statistics()
                    self._show_info("All crash reports have been cleared")
                else:
                    self._show_error("Crash reporting not available")
            except Exception as e:
                self.logger.error(f"Failed to clear crash reports: {e}")
                self._show_error("Failed to clear crash reports")
        
        dialog.close()
    
    def _on_test_crash_clicked(self, button):
        """Handle test crash button click."""
        try:
            if not self.crash_reporter:
                self._show_error("Crash reporting not available")
                return
            
            # Show warning dialog
            dialog = Adw.MessageDialog.new(
                self,
                "Test Crash",
                "This will generate a test crash to verify crash reporting is working. "
                "The application may close unexpectedly. Continue?"
            )
            
            dialog.add_response("cancel", "Cancel")
            dialog.add_response("test", "Generate Test Crash")
            dialog.set_response_appearance("test", Adw.ResponseAppearance.DESTRUCTIVE)
            dialog.set_default_response("cancel")
            
            dialog.connect("response", self._on_test_crash_response)
            dialog.present()
            
        except Exception as e:
            self.logger.error(f"Failed to show test crash dialog: {e}")
            self._show_error("Failed to generate test crash")
    
    def _on_test_crash_response(self, dialog, response):
        """Handle test crash confirmation response."""
        if response == "test":
            try:
                dialog.close()
                self.close()  # Close settings dialog first
                
                # Generate test crash
                if self.crash_reporter:
                    self.crash_reporter.generate_test_crash()
                else:
                    self._show_error("Crash reporting not available")
            except Exception as e:
                # This should trigger the crash reporter
                self.logger.error(f"Test crash generated: {e}")
        else:
            dialog.close()
    
    def _show_error(self, message):
        """Show error message."""
        dialog = Adw.MessageDialog.new(self, "Error", message)
        dialog.add_response("close", "Close")
        dialog.present()
    
    def _show_info(self, message):
        """Show info message."""
        dialog = Adw.MessageDialog.new(self, "Information", message)
        dialog.add_response("close", "Close")
        dialog.present()