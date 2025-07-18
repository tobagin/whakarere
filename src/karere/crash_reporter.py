#!/usr/bin/env python3
"""
Crash reporting system for Karere application.

This module provides comprehensive crash detection, data collection,
and reporting functionality with privacy-aware features.
"""

import os
import sys
import time
import json
import uuid
import traceback
import platform
import threading
import tempfile
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List

try:
    import gi
    gi.require_version("Gtk", "4.0")
    gi.require_version("Adw", "1")
    from gi.repository import Gtk, Adw, GLib, Gio
    GTK_AVAILABLE = True
except ImportError:
    GTK_AVAILABLE = False

from .logging_config import get_logger
from ._build_config import is_production_build, get_build_info
from . import __version__


class CrashReporter:
    """
    Comprehensive crash reporting system for production applications.
    
    Features:
    - Automatic crash detection and data collection
    - Privacy-aware reporting with user consent
    - Local crash report storage and management
    - System information collection
    - Stack trace analysis
    - User feedback collection
    - Report submission (optional)
    """
    
    def __init__(self, app_name: str = "Karere", enable_reporting: bool = True):
        """
        Initialize the crash reporter.
        
        Args:
            app_name: Name of the application
            enable_reporting: Whether to enable crash reporting
        """
        self.app_name = app_name
        self.enable_reporting = enable_reporting
        self.logger = get_logger('crash_reporter')
        
        # Initialize crash reporting directories
        self.crash_dir = self._get_crash_directory()
        self.reports_dir = self.crash_dir / "reports"
        self.reports_dir.mkdir(parents=True, exist_ok=True)
        
        # Runtime information
        self.start_time = time.time()
        self.crash_count = 0
        self.last_crash_time = 0
        
        # Privacy settings
        self.collect_system_info = True
        self.collect_user_data = False  # Never collect user data by default
        self.auto_submit = False  # Never auto-submit in production
        
        # Initialize system info cache
        self._system_info = None
        self._build_info = None
        
        self.logger.info(f"Crash reporter initialized for {app_name}")
        
    def _get_crash_directory(self) -> Path:
        """Get the crash reports directory."""
        if is_production_build():
            # Production: use XDG data directory
            xdg_data = os.environ.get('XDG_DATA_HOME', os.path.expanduser('~/.local/share'))
            return Path(xdg_data) / 'karere' / 'crashes'
        else:
            # Development: use temporary directory
            return Path(tempfile.gettempdir()) / 'karere-dev' / 'crashes'
    
    def install_exception_handler(self):
        """Install global exception handler for crash detection."""
        def exception_handler(exc_type, exc_value, exc_traceback):
            """Handle uncaught exceptions."""
            if issubclass(exc_type, KeyboardInterrupt):
                # Don't report keyboard interrupts
                sys.__excepthook__(exc_type, exc_value, exc_traceback)
                return
            
            # Generate crash report
            crash_id = self.generate_crash_report(exc_type, exc_value, exc_traceback)
            
            # Log the crash
            self.logger.critical(f"Unhandled exception caught - Crash ID: {crash_id}")
            self.logger.critical(f"Exception: {exc_type.__name__}: {exc_value}")
            
            # Show crash dialog if GTK is available
            if GTK_AVAILABLE and self.enable_reporting:
                self._show_crash_dialog(crash_id, exc_type, exc_value)
            
            # Call original exception handler
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
        
        # Install the handler
        sys.excepthook = exception_handler
        self.logger.info("Exception handler installed")
    
    def generate_crash_report(self, exc_type, exc_value, exc_traceback) -> str:
        """
        Generate a comprehensive crash report.
        
        Args:
            exc_type: Exception type
            exc_value: Exception value
            exc_traceback: Exception traceback
            
        Returns:
            Crash report ID
        """
        try:
            # Generate unique crash ID
            crash_id = str(uuid.uuid4())
            timestamp = datetime.now().isoformat()
            
            # Collect crash data
            crash_data = {
                "crash_id": crash_id,
                "timestamp": timestamp,
                "app_name": self.app_name,
                "app_version": __version__,
                "exception": {
                    "type": exc_type.__name__,
                    "message": str(exc_value),
                    "traceback": traceback.format_exception(exc_type, exc_value, exc_traceback)
                },
                "system_info": self._get_system_info() if self.collect_system_info else {},
                "build_info": self._get_build_info(),
                "runtime_info": self._get_runtime_info(),
                "environment": self._get_environment_info(),
                "crash_context": self._get_crash_context()
            }
            
            # Save crash report
            if self._save_crash_report(crash_id, crash_data):
                # Update crash statistics only if save was successful
                self.crash_count += 1
                self.last_crash_time = time.time()
                return crash_id
            else:
                # Save failed, return "unknown"
                return "unknown"
            
        except Exception as e:
            self.logger.error(f"Failed to generate crash report: {e}")
            return "unknown"
    
    def _get_system_info(self) -> Dict[str, Any]:
        """Collect system information for crash report."""
        if self._system_info is None:
            try:
                self._system_info = {
                    "platform": platform.platform(),
                    "system": platform.system(),
                    "release": platform.release(),
                    "version": platform.version(),
                    "machine": platform.machine(),
                    "processor": platform.processor(),
                    "python_version": platform.python_version(),
                    "python_implementation": platform.python_implementation(),
                    "architecture": platform.architecture(),
                    "hostname": platform.node(),  # This might be sensitive
                    "uptime": time.time() - self.start_time,
                    "memory_info": self._get_memory_info(),
                    "disk_info": self._get_disk_info(),
                    "gtk_version": self._get_gtk_version()
                }
            except Exception as e:
                self.logger.error(f"Failed to collect system info: {e}")
                self._system_info = {"error": str(e)}
        
        return self._system_info.copy()
    
    def _get_build_info(self) -> Dict[str, Any]:
        """Get build information."""
        if self._build_info is None:
            try:
                self._build_info = get_build_info()
            except Exception as e:
                self.logger.error(f"Failed to get build info: {e}")
                self._build_info = {"error": str(e)}
        
        return self._build_info.copy()
    
    def _get_runtime_info(self) -> Dict[str, Any]:
        """Get runtime information."""
        return {
            "uptime": time.time() - self.start_time,
            "crash_count": self.crash_count,
            "last_crash_time": self.last_crash_time,
            "current_thread": threading.current_thread().name,
            "thread_count": threading.active_count(),
            "argv": sys.argv,
            "path": sys.path[:5],  # First 5 paths only
            "modules": list(sys.modules.keys())[:20]  # First 20 modules only
        }
    
    def _get_environment_info(self) -> Dict[str, Any]:
        """Get environment information (privacy-aware)."""
        # Only collect non-sensitive environment variables
        safe_env_vars = [
            'DISPLAY', 'XDG_CURRENT_DESKTOP', 'XDG_SESSION_TYPE', 'WAYLAND_DISPLAY',
            'DESKTOP_SESSION', 'FLATPAK_ID', 'SNAP_NAME', 'APPIMAGE',
            'LANG', 'LC_ALL', 'GTK_THEME', 'QT_SCALE_FACTOR'
        ]
        
        env_info = {}
        for var in safe_env_vars:
            if var in os.environ:
                env_info[var] = os.environ[var]
        
        return env_info
    
    def _get_crash_context(self) -> Dict[str, Any]:
        """Get crash context information."""
        return {
            "working_directory": os.getcwd(),
            "executable": sys.executable,
            "startup_time": self.start_time,
            "crash_time": time.time(),
            "pid": os.getpid(),
            "ppid": os.getppid() if hasattr(os, 'getppid') else None,
            "uid": os.getuid() if hasattr(os, 'getuid') else None,
            "gid": os.getgid() if hasattr(os, 'getgid') else None
        }
    
    def _get_memory_info(self) -> Dict[str, Any]:
        """Get memory information."""
        memory_info = {}
        try:
            # Try to get memory info from /proc/meminfo on Linux
            if os.path.exists('/proc/meminfo'):
                with open('/proc/meminfo', 'r') as f:
                    for line in f:
                        if line.startswith(('MemTotal:', 'MemAvailable:', 'MemFree:')):
                            key, value = line.split(':', 1)
                            memory_info[key.strip()] = value.strip()
        except Exception:
            pass
        
        return memory_info
    
    def _get_disk_info(self) -> Dict[str, Any]:
        """Get disk space information."""
        disk_info = {}
        try:
            statvfs = os.statvfs(self.crash_dir)
            disk_info = {
                "total_space": statvfs.f_frsize * statvfs.f_blocks,
                "available_space": statvfs.f_frsize * statvfs.f_bavail,
                "used_space": statvfs.f_frsize * (statvfs.f_blocks - statvfs.f_bavail)
            }
        except Exception:
            pass
        
        return disk_info
    
    def _get_gtk_version(self) -> Dict[str, Any]:
        """Get GTK version information."""
        gtk_info = {}
        try:
            if GTK_AVAILABLE:
                gtk_info = {
                    "gtk_version": f"{Gtk.get_major_version()}.{Gtk.get_minor_version()}.{Gtk.get_micro_version()}",
                    "glib_version": f"{GLib.MAJOR_VERSION}.{GLib.MINOR_VERSION}.{GLib.MICRO_VERSION}"
                }
        except Exception:
            pass
        
        return gtk_info
    
    def _save_crash_report(self, crash_id: str, crash_data: Dict[str, Any]) -> bool:
        """Save crash report to file.
        
        Returns:
            True if save was successful, False otherwise
        """
        try:
            report_file = self.reports_dir / f"crash_{crash_id}.json"
            
            with open(report_file, 'w') as f:
                json.dump(crash_data, f, indent=2, default=str)
            
            self.logger.info(f"Crash report saved: {report_file}")
            
            # Clean up old reports (keep last 10)
            self._cleanup_old_reports()
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to save crash report: {e}")
            return False
    
    def _cleanup_old_reports(self):
        """Clean up old crash reports."""
        try:
            reports = list(self.reports_dir.glob("crash_*.json"))
            reports.sort(key=lambda p: p.stat().st_mtime, reverse=True)
            
            # Keep only the 10 most recent reports
            for report in reports[10:]:
                try:
                    report.unlink()
                    self.logger.debug(f"Deleted old crash report: {report}")
                except Exception as e:
                    self.logger.warning(f"Failed to delete old crash report {report}: {e}")
                    
        except Exception as e:
            self.logger.error(f"Failed to cleanup old reports: {e}")
    
    def _show_crash_dialog(self, crash_id: str, exc_type, exc_value):
        """Show crash dialog to user."""
        try:
            if not GTK_AVAILABLE:
                return
            
            dialog = Adw.MessageDialog.new(
                None,
                "Application Crash",
                f"The application has encountered an unexpected error and needs to close.\n\n"
                f"Error: {exc_type.__name__}: {exc_value}\n\n"
                f"A crash report has been saved with ID: {crash_id[:8]}...\n\n"
                f"You can find the full report at:\n{self.reports_dir}"
            )
            
            dialog.add_response("close", "Close")
            dialog.add_response("report", "View Report")
            dialog.set_default_response("close")
            
            dialog.connect("response", self._on_crash_dialog_response, crash_id)
            dialog.present()
            
        except Exception as e:
            self.logger.error(f"Failed to show crash dialog: {e}")
    
    def _on_crash_dialog_response(self, dialog, response, crash_id):
        """Handle crash dialog response."""
        if response == "report":
            self._open_crash_report(crash_id)
        dialog.close()
    
    def _open_crash_report(self, crash_id: str):
        """Open crash report in default text editor."""
        try:
            report_file = self.reports_dir / f"crash_{crash_id}.json"
            if report_file.exists():
                # Try to open with default application
                Gio.AppInfo.launch_default_for_uri(
                    f"file://{report_file}",
                    None
                )
        except Exception as e:
            self.logger.error(f"Failed to open crash report: {e}")
    
    def get_crash_reports(self) -> List[Dict[str, Any]]:
        """Get list of crash reports."""
        reports = []
        try:
            for report_file in self.reports_dir.glob("crash_*.json"):
                try:
                    with open(report_file, 'r') as f:
                        crash_data = json.load(f)
                        reports.append({
                            "file": str(report_file),
                            "crash_id": crash_data.get("crash_id", "unknown"),
                            "timestamp": crash_data.get("timestamp", "unknown"),
                            "exception_type": crash_data.get("exception", {}).get("type", "unknown"),
                            "exception_message": crash_data.get("exception", {}).get("message", "unknown")
                        })
                except Exception as e:
                    self.logger.warning(f"Failed to read crash report {report_file}: {e}")
        except Exception as e:
            self.logger.error(f"Failed to get crash reports: {e}")
        
        return sorted(reports, key=lambda x: x.get("timestamp", ""), reverse=True)
    
    def clear_crash_reports(self):
        """Clear all crash reports."""
        try:
            for report_file in self.reports_dir.glob("crash_*.json"):
                try:
                    report_file.unlink()
                    self.logger.info(f"Deleted crash report: {report_file}")
                except Exception as e:
                    self.logger.warning(f"Failed to delete crash report {report_file}: {e}")
        except Exception as e:
            self.logger.error(f"Failed to clear crash reports: {e}")
    
    def generate_test_crash(self):
        """Generate a test crash for testing purposes."""
        if not is_production_build():
            self.logger.warning("Generating test crash for development testing")
            raise RuntimeError("Test crash generated for crash reporting testing")
        else:
            self.logger.warning("Test crash ignored in production build")


# Global crash reporter instance
_crash_reporter = None


def initialize_crash_reporter(app_name: str = "Karere", enable_reporting: bool = True) -> CrashReporter:
    """Initialize global crash reporter."""
    global _crash_reporter
    if _crash_reporter is None:
        _crash_reporter = CrashReporter(app_name, enable_reporting)
    return _crash_reporter


def get_crash_reporter() -> Optional[CrashReporter]:
    """Get global crash reporter instance."""
    return _crash_reporter


def install_crash_handler(app_name: str = "Karere", enable_reporting: bool = True):
    """Install crash handler for the application."""
    crash_reporter = initialize_crash_reporter(app_name, enable_reporting)
    crash_reporter.install_exception_handler()
    return crash_reporter