"""
NotificationManager for Karere application.

Handles all notification logic, filtering, DND mode, and notification settings integration.
Part of Phase 1.3 of the comprehensive notification enhancement system.
"""

import gi
import logging
import time
from datetime import datetime, time as datetime_time
from typing import Optional, Dict, Any, Union

gi.require_version("Gtk", "4.0")
gi.require_version("Gio", "2.0")

from gi.repository import Gio, GLib


class NotificationManager:
    """
    Core notification management system for Karere.
    
    Handles notification filtering, DND mode, scheduling, and integration
    with the comprehensive notification settings system.
    """
    
    def __init__(self, application, settings: Gio.Settings):
        """
        Initialize the NotificationManager.
        
        Args:
            application: The main Karere application instance
            settings: GSettings instance for notification preferences
        """
        self.app = application
        self.settings = settings
        self.logger = logging.getLogger("karere.notification_manager")
        
        # Enhanced session state tracking
        self.session_background_shown = False
        self.session_start_time = time.time()
        self.background_notification_count = 0
        self.window_is_focused = True
        self.window_background_start_time = None
        self.last_background_notification_time = None
        
        # Background notification timing and rate limiting
        self._last_background_notification_time = 0
        self._background_session_notifications = []  # Track all background notifications in current session
        
        # Connect to settings changes for real-time updates
        self.settings.connect("changed", self._on_settings_changed)
        
        self.logger.info("NotificationManager initialized")
    
    # Background notification management methods
    
    def on_window_focus_changed(self, is_focused: bool):
        """Handle window focus state changes for background notification tracking."""
        previous_focus = self.window_is_focused
        self.window_is_focused = is_focused
        current_time = time.time()
        
        if previous_focus and not is_focused:
            # Window just went to background
            self.window_background_start_time = current_time
            self.logger.debug("Window moved to background, starting background tracking")
        elif not previous_focus and is_focused:
            # Window just came to foreground
            if self.window_background_start_time:
                background_duration = current_time - self.window_background_start_time
                self.logger.debug(f"Window returned to foreground after {background_duration:.1f}s in background")
            self.window_background_start_time = None
    
    def get_window_background_duration(self) -> float:
        """Get how long the window has been in the background (seconds)."""
        if self.window_is_focused or self.window_background_start_time is None:
            return 0.0
        return time.time() - self.window_background_start_time
    
    def track_background_notification(self, notification_type: str, title: str):
        """Track a background notification for session management."""
        current_time = time.time()
        notification_record = {
            'type': notification_type,
            'title': title,
            'timestamp': current_time,
            'session_time': current_time - self.session_start_time
        }
        
        self._background_session_notifications.append(notification_record)
        
        if notification_type == "background":
            self.background_notification_count += 1
            # Only set session_background_shown for "first-session-only" mode
            frequency = self.settings.get_string("background-notification-frequency")
            if frequency == "first-session-only":
                self.session_background_shown = True
            self.last_background_notification_time = current_time
            
        # Limit session notification history to last 100 notifications
        if len(self._background_session_notifications) > 100:
            self._background_session_notifications = self._background_session_notifications[-100:]
        
        self.logger.debug(f"Tracked background notification: {title} (total this session: {self.background_notification_count})")
    
    def get_background_notification_stats(self) -> dict:
        """Get comprehensive background notification statistics for current session."""
        current_time = time.time()
        session_duration = current_time - self.session_start_time
        
        background_notifications = [n for n in self._background_session_notifications if n['type'] == 'background']
        
        return {
            'session_duration_minutes': session_duration / 60,
            'total_notifications': len(self._background_session_notifications),
            'background_notifications': len(background_notifications),
            'notifications_per_hour': (len(self._background_session_notifications) / session_duration) * 3600 if session_duration > 0 else 0,
            'last_background_notification': self.last_background_notification_time,
            'window_currently_focused': self.window_is_focused,
            'current_background_duration': self.get_window_background_duration()
        }
    
    def should_show_notification(self, notification_type: str, **kwargs) -> bool:
        """
        Determine if a notification should be shown based on current settings and DND status.
        
        Args:
            notification_type: Type of notification ('message', 'background', 'system')
            **kwargs: Additional context for notification filtering
            
        Returns:
            bool: True if notification should be shown, False otherwise
        """
        try:
            # Check if DND is active and blocks this notification type
            if self._is_blocked_by_dnd(notification_type):
                self.logger.debug(f"Notification blocked by DND: {notification_type}")
                return False
            
            # Check type-specific rules
            if notification_type == "message":
                result = self._should_show_message_notification(**kwargs)
                self.logger.debug(f"Message notification check result: {result}")
                return result
            elif notification_type == "background":
                result = self._should_show_background_notification(**kwargs)
                self.logger.debug(f"Background notification check result: {result}")
                return result
            elif notification_type == "system":
                result = self._should_show_system_notification(**kwargs)
                self.logger.debug(f"System notification check result: {result}")
                return result
            else:
                self.logger.warning(f"Unknown notification type: {notification_type}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error determining notification visibility: {e}")
            return False
    
    def send_notification(self, title: str, message: str, notification_type: str = "system", 
                         **kwargs) -> bool:
        """
        Send a notification if it passes all filtering rules.
        
        Args:
            title: Notification title
            message: Notification message content
            notification_type: Type of notification ('message', 'background', 'system')
            **kwargs: Additional context for notification processing
            
        Returns:
            bool: True if notification was sent, False if filtered out
        """
        try:
            # Check if notification should be shown
            if not self.should_show_notification(notification_type, **kwargs):
                self.logger.debug(f"Notification filtered out: {title}")
                return False
            
            # Process message content if needed
            processed_message = self._process_message_content(message, notification_type, **kwargs)
            
            # Send the notification
            self._send_system_notification(title, processed_message, **kwargs)
            
            # Update session state and track background notifications
            self._update_session_state(notification_type, **kwargs)
            self.track_background_notification(notification_type, title)
            
            self.logger.info(f"Notification sent: {title}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error sending notification: {e}")
            return False
    
    def is_dnd_active(self) -> bool:
        """
        Check if Do Not Disturb mode is currently active.
        
        Returns:
            bool: True if DND is active (manual or scheduled), False otherwise
        """
        try:
            # Check manual DND toggle
            if self.settings.get_boolean("dnd-mode-enabled"):
                return True
            
            # Check scheduled DND
            if self._is_scheduled_dnd_active():
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error checking DND status: {e}")
            return False
    
    def get_dnd_status(self) -> Dict[str, Any]:
        """
        Get comprehensive DND status information.
        
        Returns:
            dict: DND status with details about active state, schedule, etc.
        """
        try:
            manual_enabled = self.settings.get_boolean("dnd-mode-enabled")
            schedule_enabled = self.settings.get_boolean("dnd-schedule-enabled")
            scheduled_active = self._is_scheduled_dnd_active()
            
            status = {
                "active": manual_enabled or scheduled_active,
                "manual_enabled": manual_enabled,
                "schedule_enabled": schedule_enabled,
                "scheduled_active": scheduled_active,
                "allow_background": self.settings.get_boolean("dnd-allow-background-notifications")
            }
            
            if schedule_enabled:
                status.update({
                    "schedule_start": self.settings.get_string("dnd-start-time"),
                    "schedule_end": self.settings.get_string("dnd-end-time")
                })
            
            return status
            
        except Exception as e:
            self.logger.error(f"Error getting DND status: {e}")
            return {"active": False, "error": str(e)}
    
    def reset_session_state(self):
        """Reset session-specific notification state (e.g., on app restart)."""
        self.session_background_shown = False
        self.last_background_notification_time = None
        self.logger.info("Notification session state reset")
    
    def _should_show_message_notification(self, **kwargs) -> bool:
        """Check if message notifications should be shown."""
        # Check if message notifications are enabled
        if not self.settings.get_boolean("show-message-notifications"):
            return False
        
        # Check if we should show notifications when window is focused
        window_focused = kwargs.get("window_focused", False)
        notify_when_focused = self.settings.get_boolean("message-notification-when-focused")
        
        if window_focused and not notify_when_focused:
            return False
        
        return True
    
    def _should_show_background_notification(self, **kwargs) -> bool:
        """Check if background notifications should be shown with enhanced session and timing logic."""
        frequency = self.settings.get_string("background-notification-frequency")
        self.logger.debug(f"Background notification check: frequency={frequency}, session_shown={self.session_background_shown}")
        
        if frequency == "never":
            self.logger.debug("Background notification blocked: frequency set to 'never'")
            return False
        elif frequency == "first-session-only":
            if self.session_background_shown:
                self.logger.debug("Background notification blocked: 'first-session-only' and already shown this session")
                return False
        # frequency == "always" - continue to additional checks
        
        # Enhanced rate limiting for background notifications (only for 'always' mode)
        current_time = time.time()
        
        # Apply cooldown only for "always" mode to prevent spam
        if frequency == "always":
            # Much shorter cooldown for "always" mode - allow every 30 seconds
            background_cooldown = 30  # 30 seconds cooldown for always mode
            if hasattr(self, '_last_background_notification_time'):
                time_since_last = current_time - self._last_background_notification_time
                if time_since_last < background_cooldown:
                    self.logger.debug(f"Background notification blocked by cooldown: {time_since_last:.1f}s < {background_cooldown}s")
                    return False
        
        # Check if window has been in background long enough to warrant notification
        background_grace_period = kwargs.get("background_grace_period", 30)  # 30 seconds grace period
        actual_background_duration = self.get_window_background_duration()
        
        # Special case: If this is a "background" type notification (window just closed),
        # bypass the grace period check since the user just performed the action
        # The notification_type is not in kwargs, we need to check the calling context
        is_window_close_notification = True  # For now, assume background notifications are immediate
        
        if not is_window_close_notification and actual_background_duration > 0 and actual_background_duration < background_grace_period:
            self.logger.debug(f"Background notification blocked by grace period: {actual_background_duration:.1f}s < {background_grace_period}s")
            return False
        
        # Track this notification attempt
        self._last_background_notification_time = current_time
        
        self.logger.debug("Background notification approved - all checks passed")
        return True
    
    def _should_show_system_notification(self, **kwargs) -> bool:
        """Check if system notifications should be shown."""
        return self.settings.get_boolean("show-system-notifications")
    
    def _is_blocked_by_dnd(self, notification_type: str) -> bool:
        """Check if notification type is blocked by DND."""
        if not self.is_dnd_active():
            return False
        
        # Background notifications can be allowed during DND
        if (notification_type == "background" and 
            self.settings.get_boolean("dnd-allow-background-notifications")):
            return False
        
        # All other notifications are blocked during DND
        return True
    
    def _is_scheduled_dnd_active(self) -> bool:
        """Check if scheduled DND is currently active."""
        try:
            if not self.settings.get_boolean("dnd-schedule-enabled"):
                return False
            
            start_time_str = self.settings.get_string("dnd-start-time")
            end_time_str = self.settings.get_string("dnd-end-time")
            
            # Parse times
            start_time = self._parse_time(start_time_str)
            end_time = self._parse_time(end_time_str)
            
            if start_time is None or end_time is None:
                self.logger.warning(f"Invalid DND schedule times: {start_time_str}, {end_time_str}")
                return False
            
            current_time = datetime.now().time()
            
            # Handle overnight schedules (e.g., 22:00 to 08:00)
            if start_time > end_time:
                return current_time >= start_time or current_time <= end_time
            else:
                return start_time <= current_time <= end_time
                
        except Exception as e:
            self.logger.error(f"Error checking scheduled DND: {e}")
            return False
    
    def _parse_time(self, time_str: str) -> Optional[datetime_time]:
        """Parse time string in HH:MM format."""
        try:
            parts = time_str.split(":")
            if len(parts) != 2:
                return None
            
            hours, minutes = int(parts[0]), int(parts[1])
            
            if not (0 <= hours <= 23 and 0 <= minutes <= 59):
                return None
            
            return datetime_time(hours, minutes)
            
        except (ValueError, IndexError):
            return None
    
    def _process_message_content(self, message: str, notification_type: str, **kwargs) -> str:
        """Process message content based on preview settings."""
        if notification_type != "message":
            return message
        
        # Check if preview is enabled
        if not self.settings.get_boolean("message-preview-enabled"):
            return "New message"  # Generic message when preview is disabled
        
        # Apply length limit
        max_length = self.settings.get_int("message-preview-length")
        if len(message) > max_length:
            return message[:max_length] + "..."
        
        return message
    
    def _send_system_notification(self, title: str, message: str, **kwargs):
        """Send notification using system notification service."""
        try:
            notification = Gio.Notification.new(title)
            notification.set_body(message)
            
            # Set notification priority based on type
            notification_type = kwargs.get("notification_type", "system")
            if notification_type == "message":
                notification.set_priority(Gio.NotificationPriority.HIGH)
            elif notification_type == "system":
                notification.set_priority(Gio.NotificationPriority.NORMAL)
            else:
                notification.set_priority(Gio.NotificationPriority.LOW)
            
            # Add icon if available
            if hasattr(self.app, 'get_application_id'):
                notification.set_icon(Gio.ThemedIcon.new("io.github.tobagin.karere"))
            
            # Send notification
            self.app.send_notification(None, notification)
            
        except Exception as e:
            self.logger.error(f"Error sending system notification: {e}")
    
    def _update_session_state(self, notification_type: str, **kwargs):
        """Update session state after sending notification."""
        if notification_type == "background":
            # Only set session_background_shown for "first-session-only" mode
            frequency = self.settings.get_string("background-notification-frequency")
            if frequency == "first-session-only":
                self.session_background_shown = True
            self.last_background_notification_time = datetime.now()
    
    def _on_settings_changed(self, settings, key):
        """Handle settings changes for real-time updates."""
        self.logger.debug(f"Notification setting changed: {key}")
        
        # Reset session state for certain settings changes
        if key == "background-notification-frequency":
            if settings.get_string(key) == "first-session-only":
                self.session_background_shown = False