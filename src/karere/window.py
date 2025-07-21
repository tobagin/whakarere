"""
Main window for Karere application.
"""

import gi
import os

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
gi.require_version("WebKit", "6.0")

from gi.repository import Gtk, Adw, WebKit, Gio, GLib
from .settings import KarereSettingsDialog
from .about import create_about_dialog
from .logging_config import get_logger
from ._build_config import should_enable_developer_tools


@Gtk.Template(resource_path='/io/github/tobagin/karere/window.ui')
class KarereWindow(Adw.ApplicationWindow):
    """Main application window containing the WebView."""
    
    __gtype_name__ = 'KarereWindow'
    
    webview_container = Gtk.Template.Child()
    
    def __init__(self, app):
        super().__init__(application=app)
        self.app = app
        
        # Set up logging
        self.logger = get_logger('window')
        self.logger.info("KarereWindow initializing")
        
        # Initialize settings
        self.settings = Gio.Settings.new("io.github.tobagin.karere")
        
        # Set up actions and webview
        self._setup_actions()
        self._setup_webview()
        self._apply_settings()
        
        # Connect close event to background running
        self.connect("close-request", self._on_close_request)
        
        # Connect window focus events for background notification tracking
        self.connect("notify::is-active", self._on_window_focus_changed)
        
        self.logger.info("KarereWindow initialization complete")
    
    def _setup_actions(self):
        """Set up application actions."""
        self.logger.info("Setting up window actions")
        # Settings action
        settings_action = Gio.SimpleAction.new("settings", None)
        settings_action.connect("activate", self._on_settings_action)
        self.app.add_action(settings_action)
        
        # About action
        about_action = Gio.SimpleAction.new("about", None)
        about_action.connect("activate", self._on_about_action)
        self.app.add_action(about_action)
    
    def _setup_webview(self):
        """Set up the WebKit WebView with data manager for persistent cookies and error handling."""
        self.logger.info("Setting up WebView")
        
        try:
            # Use XDG directories for Flatpak compatibility
            data_dir = os.environ.get('XDG_DATA_HOME', os.path.expanduser('~/.local/share')) + '/karere'
            cache_dir = os.environ.get('XDG_CACHE_HOME', os.path.expanduser('~/.cache')) + '/karere'
            
            # Ensure directories exist with proper error handling
            try:
                os.makedirs(data_dir, exist_ok=True)
                os.makedirs(cache_dir, exist_ok=True)
                self.logger.info(f"WebView data directory: {data_dir}")
                self.logger.info(f"WebView cache directory: {cache_dir}")
            except PermissionError as e:
                self.logger.error(f"Permission denied creating directories: {e}")
                self._show_error_dialog("Permission Error", 
                                       "Cannot create data directories. Please check file permissions.")
                return
            except OSError as e:
                self.logger.error(f"OS error creating directories: {e}")
                self._show_error_dialog("File System Error", 
                                       "Cannot create data directories. Please check disk space and permissions.")
                return
            
            # Create WebsiteDataManager with data directories
            try:
                self.website_data_manager = WebKit.WebsiteDataManager(
                    base_data_directory=data_dir,
                    base_cache_directory=cache_dir
                )
            except Exception as e:
                self.logger.error(f"Failed to create WebsiteDataManager: {e}")
                self._show_error_dialog("WebView Error", 
                                       "Failed to initialize WebView data manager. Please check your WebKit installation.")
                return
            
            # Create NetworkSession with the data manager
            try:
                self.network_session = WebKit.NetworkSession.new(data_directory=data_dir, cache_directory=cache_dir)
            except Exception as e:
                self.logger.error(f"Failed to create NetworkSession: {e}")
                self._show_error_dialog("Network Error", 
                                       "Failed to initialize network session. Please check your network configuration.")
                return
            
            # Get the cookie manager from the network session
            try:
                self.cookie_manager = self.network_session.get_cookie_manager()
                
                # Configure cookie persistence
                cookie_file = os.path.join(data_dir, 'cookies.sqlite')
                self.cookie_manager.set_persistent_storage(cookie_file, WebKit.CookiePersistentStorage.SQLITE)
                self.logger.info("Cookie persistence configured")
            except Exception as e:
                self.logger.error(f"Failed to configure cookie persistence: {e}")
                self.logger.warning("Continuing without persistent cookies")
            
        except Exception as e:
            self.logger.error(f"Critical error setting up WebView directories: {e}")
            self._show_error_dialog("WebView Setup Error", 
                                   "Failed to set up WebView. Please check your system configuration.")
        
        # Create WebView with error handling
        try:
            self.webview = WebKit.WebView.new()
            self.logger.info("WebView created")
        except Exception as e:
            self.logger.error(f"Failed to create WebView: {e}")
            self._show_error_dialog("WebView Error", 
                                   "Failed to create WebView. Please check your WebKit installation.")
            return
        
        # Configure WebView settings with error handling
        try:
            webkit_settings = self.webview.get_settings()
            webkit_settings.set_enable_javascript(True)
            webkit_settings.set_enable_media_stream(True)
            webkit_settings.set_enable_webgl(True)
            webkit_settings.set_hardware_acceleration_policy(WebKit.HardwareAccelerationPolicy.ALWAYS)
            
            # Enable clipboard access for screenshot paste functionality
            webkit_settings.set_javascript_can_access_clipboard(True)
            self.logger.info("Clipboard access enabled for screenshot paste")
            
            # Enable media capture and other permissions that might be needed for notifications
            webkit_settings.set_enable_media(True)
            webkit_settings.set_enable_media_capabilities(True)
            webkit_settings.set_auto_load_images(True)
            self.logger.info("Additional WebKit permissions enabled")
            
            # Use default user agent for testing - custom user agent disabled
            # from .application import BUS_NAME
            # app_name = "Karere.dev" if BUS_NAME.endswith('.dev') else "Karere"
            # # WhatsApp Web detects the Chrome part, so replace it with our app name
            # user_agent = f"Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) {app_name}/120.0.0.0 Safari/537.36"
            # webkit_settings.set_user_agent(user_agent)
            self.logger.info("Using default WebKit user agent for notification testing")
            
            self.logger.info("WebView settings configured")
        except Exception as e:
            self.logger.error(f"Failed to configure WebView settings: {e}")
            self.logger.warning("Continuing with default WebView settings")
        
        # Configure spell checking after WebView is created
        self._setup_spell_checking()
        
        # Native WebKit notification handling replaces JavaScript message handlers
        # No script message handlers needed - using WebKit's native notification system
        
        # Add WebView to container with expand properties
        self.webview.set_vexpand(True)
        self.webview.set_hexpand(True)
        self.webview_container.append(self.webview)
        
        # Page load events handled by error handlers setup
        
        # Set up native WebKit notification handling
        self.webview.connect("permission-request", self._on_permission_request)
        self.webview.connect("show-notification", self._on_show_notification)
        
        # Set up download handling
        self.setup_download_directory()
        self.webview.connect("decide-policy", self._on_decide_policy)
        
        # Set up WebView event handlers for error handling
        self._setup_webview_error_handlers()
        
        # User agent override disabled for testing
        # self._inject_user_agent_override()
        self.logger.info("User agent override disabled for notification testing")
        
        # Load WhatsApp Web with error handling
        try:
            self.webview.load_uri("https://web.whatsapp.com")
            self.logger.info("Loading WhatsApp Web")
        except Exception as e:
            self.logger.error(f"Failed to load WhatsApp Web: {e}")
            self._show_error_dialog("Network Error", 
                                   "Failed to load WhatsApp Web. Please check your internet connection.")
    
    def _inject_user_agent_override(self):
        """Inject JavaScript to override user agent detection."""
        from .application import BUS_NAME
        app_name = "Karere.dev" if BUS_NAME.endswith('.dev') else "Karere"
        
        user_agent_script = f"""
        (function() {{
            console.log('Karere: Overriding user agent detection');
            
            // Override navigator.userAgent property
            Object.defineProperty(navigator, 'userAgent', {{
                get: function() {{
                    return 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) {app_name}/120.0.0.0 Safari/537.36';
                }},
                configurable: true
            }});
            
            // Override navigator.appVersion
            Object.defineProperty(navigator, 'appVersion', {{
                get: function() {{
                    return '5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) {app_name}/120.0.0.0 Safari/537.36';
                }},
                configurable: true
            }});
            
            console.log('Karere: User agent overridden to:', navigator.userAgent);
        }})();
        """
        
        user_content_manager = self.webview.get_user_content_manager()
        script = WebKit.UserScript.new(
            user_agent_script,
            WebKit.UserContentInjectedFrames.TOP_FRAME,
            WebKit.UserScriptInjectionTime.START,
            None, None
        )
        # user_content_manager.add_script(script)
        self.logger.info("User agent override method disabled for notification testing")
    
    def _setup_webview_error_handlers(self):
        """Set up WebView error handlers for production error handling."""
        try:
            # Connect to load events for error handling
            self.webview.connect("load-failed", self._on_load_failed)
            self.webview.connect("load-changed", self._on_load_changed_with_error_handling)
            
            # Connect to network error events
            self.webview.connect("resource-load-started", self._on_resource_load_started)
            
            self.logger.info("WebView error handlers configured")
        except Exception as e:
            self.logger.error(f"Failed to set up WebView error handlers: {e}")
    
    def _on_load_failed(self, webview, load_event, failing_uri, error):
        """Handle WebView load failures with automatic recovery."""
        self.logger.error(f"WebView load failed: {error.message} for URI: {failing_uri}")
        
        # Initialize retry counter if not exists
        if not hasattr(self, '_load_retry_count'):
            self._load_retry_count = 0
        
        # Attempt automatic recovery for network issues
        if self._load_retry_count < 3 and ("network" in error.message.lower() or "connection" in error.message.lower()):
            self._load_retry_count += 1
            self.logger.info(f"Attempting automatic retry {self._load_retry_count}/3")
            
            # Wait a bit before retrying
            GLib.timeout_add_seconds(5, self._retry_load_whatsapp)
            
            # Show a less intrusive message for automatic retries
            if hasattr(self.app, 'send_notification'):
                self.app.send_notification("Connection Issue", 
                                         f"Network error occurred. Retrying... ({self._load_retry_count}/3)")
            return True
        
        # Reset retry counter on success or after max retries
        self._load_retry_count = 0
        
        # Show user-friendly error message based on error type
        if "network" in error.message.lower() or "connection" in error.message.lower():
            self._show_error_dialog("Network Error", 
                                   "Cannot connect to WhatsApp Web. Please check your internet connection and try again.")
        elif "ssl" in error.message.lower() or "certificate" in error.message.lower():
            self._show_error_dialog("Security Error", 
                                   "SSL certificate error. Please check your system's date and time settings.")
        elif "timeout" in error.message.lower():
            self._show_error_dialog("Connection Timeout", 
                                   "Connection to WhatsApp Web timed out. Please check your internet connection and try again.")
        else:
            self._show_error_dialog("Load Error", 
                                   f"Failed to load WhatsApp Web. Please try again later.")
        
        return True  # Prevent default error handling
    
    def _retry_load_whatsapp(self):
        """Retry loading WhatsApp Web."""
        try:
            if hasattr(self, 'webview') and self.webview:
                self.logger.info("Retrying WhatsApp Web load")
                self.webview.load_uri("https://web.whatsapp.com")
        except Exception as e:
            self.logger.error(f"Error during retry: {e}")
        
        return False  # Don't repeat the timeout
    
    def _on_load_changed_with_error_handling(self, webview, load_event):
        """Handle WebView load events with error handling."""
        try:
            if load_event == WebKit.LoadEvent.FINISHED:
                self.logger.info("Page load finished - using native WebKit notifications")
                # Native WebKit notification handling enabled via permission-request and show-notification signals
                # JavaScript notification injection system removed for better reliability and performance
                
                # Inject debug script to monitor notification status
                self._inject_notification_debug_script()
            elif load_event == WebKit.LoadEvent.STARTED:
                self.logger.info("Page load started")
            elif load_event == WebKit.LoadEvent.COMMITTED:
                self.logger.info("Page load committed")
        except Exception as e:
            self.logger.error(f"Error handling load event: {e}")
    
    def _inject_notification_debug_script(self):
        """Inject debug script to monitor and enable notification permissions."""
        debug_script = """
        (function() {
            console.log('Karere Debug: Checking notification permissions');
            
            // Log current notification permission
            if ('Notification' in window) {
                console.log('Karere Debug: Notification API available, permission:', Notification.permission);
                
                // If permission is default, try to request it
                if (Notification.permission === 'default') {
                    console.log('Karere Debug: Requesting notification permission...');
                    Notification.requestPermission().then(permission => {
                        console.log('Karere Debug: Notification permission result:', permission);
                    }).catch(error => {
                        console.log('Karere Debug: Permission request error:', error);
                    });
                }
                
                // Override Notification constructor to log when notifications are created
                const OriginalNotification = window.Notification;
                window.Notification = function(title, options) {
                    console.log('Karere Debug: WhatsApp attempting to create notification:', title, options);
                    return new OriginalNotification(title, options);
                };
                
                // Copy static properties
                Object.setPrototypeOf(window.Notification, OriginalNotification);
                Object.defineProperty(window.Notification, 'permission', {
                    get: () => OriginalNotification.permission
                });
                window.Notification.requestPermission = OriginalNotification.requestPermission.bind(OriginalNotification);
                
                // Try to force WhatsApp to show notification settings after page loads
                setTimeout(() => {
                    console.log('Karere Debug: Attempting to trigger WhatsApp notification setup...');
                    
                    // Look for notification settings in WhatsApp Web
                    const settingsSelectors = [
                        '[data-testid="menu"]',
                        '[title="Menu"]',
                        '[aria-label*="menu" i]'
                    ];
                    
                    let foundSettings = false;
                    for (const selector of settingsSelectors) {
                        const element = document.querySelector(selector);
                        if (element) {
                            console.log('Karere Debug: Found WhatsApp menu element:', selector);
                            foundSettings = true;
                            break;
                        }
                    }
                    
                    if (foundSettings) {
                        console.log('Karere Debug: WhatsApp Web loaded, notifications should be available');
                    } else {
                        console.log('Karere Debug: WhatsApp Web menu not found, may still be loading');
                    }
                }, 5000);
                
            } else {
                console.log('Karere Debug: Notification API not available');
            }
        })();
        """
        
        try:
            self.webview.evaluate_javascript(debug_script, -1, None, None, None, None, None)
            self.logger.info("Notification debug script injected")
        except Exception as e:
            self.logger.error(f"Failed to inject notification debug script: {e}")
    
    def _on_resource_load_started(self, webview, resource, request):
        """Handle resource load start for error monitoring."""
        try:
            uri = request.get_uri()
            self.logger.debug(f"Loading resource: {uri}")
        except Exception as e:
            self.logger.error(f"Error monitoring resource load: {e}")
    
    def _show_error_dialog(self, title, message):
        """Show an error dialog to the user."""
        try:
            # Create error dialog
            dialog = Adw.MessageDialog.new(
                self,
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
    
    def _apply_settings(self):
        """Apply current settings to the application."""
        self.logger.info("Applying settings")
        # Apply theme
        theme = self.settings.get_string("theme")
        self._apply_theme(theme)
        
        # Apply developer tools setting (with production hardening)
        if hasattr(self, 'webview'):
            webkit_settings = self.webview.get_settings()
            
            # Check if developer tools should be enabled
            if should_enable_developer_tools():
                # Development build - respect user setting
                developer_tools_enabled = self.settings.get_boolean("developer-tools")
                self.logger.info(f"Developer tools setting: {developer_tools_enabled} (development build)")
            else:
                # Production build - force disable
                developer_tools_enabled = False
                self.logger.info("Developer tools disabled (production build)")
            
            webkit_settings.set_enable_developer_extras(developer_tools_enabled)
    
    def _apply_theme(self, theme):
        """Apply the selected theme."""
        style_manager = Adw.StyleManager.get_default()
        
        if theme == "light":
            style_manager.set_color_scheme(Adw.ColorScheme.FORCE_LIGHT)
        elif theme == "dark":
            style_manager.set_color_scheme(Adw.ColorScheme.FORCE_DARK)
        else:  # follow-system
            style_manager.set_color_scheme(Adw.ColorScheme.DEFAULT)
    
    def _setup_spell_checking(self):
        """Set up spell checking for the WebView."""
        try:
            # Get the default WebContext (WebKitGTK 6.0 approach)
            web_context = WebKit.WebContext.get_default()
            if web_context:
                self._configure_spell_checking(web_context)
                self.logger.info("Spell checking setup completed")
            else:
                self.logger.warning("No default WebContext available for spell checking setup")
        except Exception as e:
            self.logger.error(f"Failed to set up spell checking: {e}")
    
    def _configure_spell_checking(self, web_context):
        """Configure spell checking settings on the WebContext."""
        try:
            # Check if spell checking is enabled
            spell_checking_enabled = self.settings.get_boolean("spell-checking-enabled")
            self.logger.info(f"Configuring spell checking: enabled={spell_checking_enabled}")
            
            # Check current state first
            try:
                current_enabled = web_context.get_spell_checking_enabled()
                self.logger.info(f"Current WebContext spell checking state: {current_enabled}")
            except Exception as e:
                self.logger.warning(f"Could not get current spell checking state: {e}")
            
            # Enable or disable spell checking
            try:
                web_context.set_spell_checking_enabled(spell_checking_enabled)
                self.logger.info(f"Called set_spell_checking_enabled({spell_checking_enabled})")
                
                # Verify it was set
                new_state = web_context.get_spell_checking_enabled()
                self.logger.info(f"Verified spell checking state after setting: {new_state}")
            except Exception as e:
                self.logger.error(f"Failed to set spell checking enabled: {e}")
                return
            
            if spell_checking_enabled:
                # Configure spell checking languages
                languages = self._get_spell_checking_languages()
                self.logger.info(f"Setting spell checking languages: {languages}")
                
                if languages:
                    try:
                        web_context.set_spell_checking_languages(languages)
                        self.logger.info(f"Called set_spell_checking_languages({languages})")
                        
                        # Verify languages were set
                        try:
                            current_languages = web_context.get_spell_checking_languages()
                            self.logger.info(f"Verified spell checking languages: {current_languages}")
                        except Exception as e:
                            self.logger.warning(f"Could not verify spell checking languages: {e}")
                    except Exception as e:
                        self.logger.error(f"Failed to set spell checking languages: {e}")
                else:
                    self.logger.warning("No spell checking languages configured")
        except Exception as e:
            self.logger.error(f"Failed to configure spell checking: {e}")
    
    def _get_spell_checking_languages(self):
        """Get the list of spell checking languages to use."""
        try:
            auto_detect = self.settings.get_boolean("spell-checking-auto-detect")
            
            if auto_detect:
                # Auto-detect from system locale
                import locale
                import os
                
                try:
                    # Get the current locale
                    current_locale = locale.getlocale()[0]
                    if current_locale:
                        return [current_locale]
                    else:
                        # Fallback to environment variables
                        lang = os.environ.get('LANG', 'en_US.UTF-8')
                        lang_code = lang.split('.')[0]  # Extract just the language part
                        return [lang_code]
                except Exception as e:
                    self.logger.warning(f"Failed to auto-detect locale: {e}")
                    return ['en_US']  # Fallback
            else:
                # Use custom languages from settings
                languages = self.settings.get_strv("spell-checking-languages")
                return languages if languages else ['en_US']  # Fallback
        except Exception as e:
            self.logger.error(f"Error getting spell checking languages: {e}")
            return ['en_US']  # Fallback
    
    def _update_spell_checking(self):
        """Update spell checking configuration (called from settings dialog)."""
        try:
            # Get the default WebContext (WebKitGTK 6.0 approach)
            web_context = WebKit.WebContext.get_default()
            if web_context:
                self._configure_spell_checking(web_context)
                self.logger.info("Spell checking configuration updated")
            else:
                self.logger.warning("No default WebContext available for spell checking update")
        except Exception as e:
            self.logger.error(f"Failed to update spell checking: {e}")
    
    def _on_settings_action(self, action, param):
        """Handle settings action."""
        settings_dialog = KarereSettingsDialog(self)
        settings_dialog.present(self)
    
    def _on_about_action(self, action, param):
        """Handle about action."""
        about_dialog = create_about_dialog(self)
        about_dialog.present(self)
    
    def _on_close_request(self, window):
        """Handle window close request - hide instead of quit."""
        self.logger.info("Window close request received")
        return self.app.on_window_delete_event()
    
    # Removed duplicate _on_load_changed method - now using _on_load_changed_with_error_handling directly
    
    
    # CSS injection system removed - not needed for current functionality

    # JavaScript result handler removed - no longer needed with native WebKit notifications
    
    # Old JavaScript-based notification message handler removed
    # Now using native WebKit notifications via show-notification signal
    
    # JavaScript property extraction method removed - no longer needed with native WebKit notifications

    def _on_window_focus_changed(self, window, pspec):
        """Handle window focus changes for background notification tracking."""
        try:
            is_focused = self.is_active()
            self.logger.info(f"Window focus changed: {'focused' if is_focused else 'unfocused'}")
            
            if hasattr(self.app, 'notification_manager') and self.app.notification_manager:
                self.app.notification_manager.on_window_focus_changed(is_focused)
                self.logger.info(f"Notification manager updated with focus state: {is_focused}")
            else:
                self.logger.warning("Notification manager not available for focus change")
        except Exception as e:
            self.logger.error(f"Error handling window focus change: {e}")

    def setup_download_directory(self):
        """Set up the downloads directory with comprehensive error handling."""
        # List of preferred download directories in order of preference
        preferred_dirs = [
            os.path.join(os.path.expanduser('~'), 'Downloads'),
            os.path.join(os.path.expanduser('~'), 'Desktop'),
            os.path.expanduser('~'),
            '/tmp'
        ]
        
        for downloads_dir in preferred_dirs:
            try:
                # Check if directory exists
                if not os.path.exists(downloads_dir):
                    try:
                        os.makedirs(downloads_dir, exist_ok=True)
                        self.logger.info(f"Created downloads directory: {downloads_dir}")
                    except PermissionError:
                        self.logger.warning(f"Permission denied creating directory: {downloads_dir}")
                        continue
                    except OSError as e:
                        self.logger.warning(f"OS error creating directory {downloads_dir}: {e}")
                        continue
                
                # Check if directory is writable
                if not os.access(downloads_dir, os.W_OK):
                    self.logger.warning(f"Directory not writable: {downloads_dir}")
                    continue
                
                # Check available disk space (at least 100MB)
                try:
                    statvfs = os.statvfs(downloads_dir)
                    free_bytes = statvfs.f_frsize * statvfs.f_bavail
                    if free_bytes < 100 * 1024 * 1024:  # 100MB
                        self.logger.warning(f"Insufficient disk space in {downloads_dir}: {free_bytes} bytes")
                        continue
                except (OSError, AttributeError):
                    # statvfs not available on some systems
                    self.logger.debug(f"Could not check disk space for {downloads_dir}")
                
                # Directory is suitable
                self.downloads_dir = downloads_dir
                self.logger.info(f"Downloads directory set to: {self.downloads_dir}")
                return
                
            except Exception as e:
                self.logger.error(f"Error checking downloads directory {downloads_dir}: {e}")
                continue
        
        # If we get here, no suitable directory was found
        self.logger.error("No suitable downloads directory found")
        self.downloads_dir = os.path.expanduser('~')  # Last resort
        self._show_error_dialog("Download Directory Error", 
                               "Could not find a suitable downloads directory. Downloads may not work properly.")

    def _on_decide_policy(self, webview, decision, decision_type):
        """Handle policy decisions including downloads and navigation."""
        from gi.repository import WebKit
        
        
        
        # Check if this is a navigation decision (link click)
        if decision_type == WebKit.PolicyDecisionType.NAVIGATION_ACTION:
            pass  # Handle navigation actions
        elif decision_type == WebKit.PolicyDecisionType.NEW_WINDOW_ACTION:
            try:
                navigation_action = decision.get_navigation_action()
                if navigation_action:
                    request = navigation_action.get_request()
                    if request:
                        uri = request.get_uri()
                        
                        if self._should_open_externally(uri):
                            self._open_external_link(uri)
                            decision.ignore()
                            return True
                        else:
                            decision.use()
                            return True
            except Exception as e:
                return False
        
        # Original navigation action handling
        if decision_type == WebKit.PolicyDecisionType.NAVIGATION_ACTION:
            try:
                navigation_action = decision.get_navigation_action()
                if navigation_action:
                    request = navigation_action.get_request()
                    if request:
                        uri = request.get_uri()
                        navigation_type = navigation_action.get_navigation_type()
                        
                        
                        # Handle external links (clicked links that leave WhatsApp Web)
                        if navigation_type == WebKit.NavigationType.LINK_CLICKED:
                            if self._should_open_externally(uri):
                                self._open_external_link(uri)
                                decision.ignore()
                                return True
                            else:
                                decision.use()
                                return True
                        else:
                            pass  # Handle other navigation types
                    else:
                        pass  # Handle requests without URI
                else:
                    pass  # Handle navigation without action
            except Exception as e:
                return False
        
        # Check if this is a download decision
        elif decision_type == WebKit.PolicyDecisionType.RESPONSE:
            response = decision.get_response()
            if response and response.get_suggested_filename():
                # This is a download
                return self._handle_download(webview, decision, response)
        
        # Let WebKit handle other decisions normally
        return False
    
    def _on_permission_request(self, webview, request):
        """Handle WebKit permission requests, including notification permissions."""
        from gi.repository import WebKit
        
        try:
            self.logger.info(f"Permission request received: {type(request)}")
            
            if isinstance(request, WebKit.NotificationPermissionRequest):
                # Always allow notification permissions for WhatsApp Web
                # This enables native web notifications to work
                request.allow()
                self.logger.info("Notification permission granted to WhatsApp Web")
                return True
            else:
                # For other permission types, use default behavior
                self.logger.debug(f"Permission request of type {type(request)} - using default behavior")
                return False
                
        except Exception as e:
            self.logger.error(f"Error handling permission request: {e}")
            return False
    
    def _on_show_notification(self, webview, notification):
        """Handle native WebKit notifications from WhatsApp Web."""
        self.logger.info("WEBKIT SHOW-NOTIFICATION SIGNAL TRIGGERED!")
        
        try:
            # Extract notification data from WebKitNotification
            title = notification.get_title() or "WhatsApp"
            body = notification.get_body() or "New message"
            tag = notification.get_tag() or None
            notification_id = notification.get_id() or None
            
            self.logger.info(f"WebKit notification details - Title: '{title}', Body: '{body}', Tag: '{tag}', ID: '{notification_id}'")
            
            # Send through existing notification manager for filtering and preferences
            if hasattr(self.app, 'send_notification'):
                self.logger.info("Calling app.send_notification...")
                try:
                    self.app.send_notification(
                        title,
                        body,
                        notification_type="web_notification",
                        notification_id=notification_id,
                        tag=tag
                    )
                    self.logger.info("Successfully called app.send_notification")
                except Exception as send_error:
                    self.logger.error(f"Error in app.send_notification: {send_error}")
            else:
                self.logger.error("app.send_notification method not available!")
                
            # Handle notification click by connecting to the clicked signal
            notification.connect("clicked", self._on_notification_clicked)
            notification.connect("closed", self._on_notification_closed)
            
            self.logger.info("WebKit notification handler completed successfully")
            return True  # We handled the notification
            
        except Exception as e:
            self.logger.error(f"Error handling web notification: {e}")
            import traceback
            self.logger.error(f"Traceback: {traceback.format_exc()}")
            return False  # Let WebKit handle it
    
    def _on_notification_clicked(self, notification):
        """Handle when a web notification is clicked."""
        try:
            # Focus the window when notification is clicked
            self.present()
            self.logger.info("Notification clicked - focusing window")
        except Exception as e:
            self.logger.error(f"Error handling notification click: {e}")
    
    def _on_notification_closed(self, notification):
        """Handle when a web notification is closed."""
        try:
            self.logger.debug("Notification closed")
        except Exception as e:
            self.logger.error(f"Error handling notification close: {e}")
    
    def _should_open_externally(self, uri):
        """Determine if a URI should be opened in the external browser."""
        if not uri:
            return False
        
        
        # Parse the URI to check domain
        try:
            from urllib.parse import urlparse
            parsed = urlparse(uri)
            domain = parsed.netloc.lower()
            scheme = parsed.scheme.lower()
            
            
            # Always handle internal schemes internally
            if scheme in ['data', 'blob', 'javascript', 'about']:
                return False
            
            # WhatsApp domains that should stay internal
            whatsapp_domains = [
                'web.whatsapp.com',
                'whatsapp.com',
                'www.whatsapp.com',
                'static.whatsapp.net',
                'pps.whatsapp.net'
            ]
            
            # If it's a WhatsApp domain, allow internal navigation
            if any(domain == wd or domain.endswith('.' + wd) for wd in whatsapp_domains):
                return False
            
            # If there's no domain (relative URLs), keep internal
            if not domain:
                return False
            
            # Only open external domains in browser
            return True
            
        except Exception as e:
            return False
    
    def _open_external_link(self, uri):
        """Open a URI in the system's default browser using Flatpak portal."""
        try:
            self.logger.info(f"Opening external link via portal: {uri}")
            
            # Use Gio.AppInfo.launch_default_for_uri_async for proper portal support
            from gi.repository import Gio
            
            # This will automatically use the portal in Flatpak environments
            Gio.AppInfo.launch_default_for_uri_async(
                uri, 
                None,  # launch_context
                None,  # cancellable
                self._on_external_link_opened,  # callback
                uri    # user_data
            )
            
            self.logger.info(f"External link launch initiated: {uri}")
            
        except Exception as e:
            self.logger.error(f"Error opening external link {uri}: {e}")
            # Fallback: try the synchronous version
            try:
                from gi.repository import Gio
                Gio.AppInfo.launch_default_for_uri(uri, None)
                self.logger.info(f"Opened external link with fallback method: {uri}")
            except Exception as e2:
                self.logger.error(f"Failed to open external link with fallback: {e2}")
    
    def _on_external_link_opened(self, source, result, user_data):
        """Callback for external link opening."""
        try:
            from gi.repository import Gio
            Gio.AppInfo.launch_default_for_uri_finish(result)
            self.logger.info(f"Successfully opened external link: {user_data}")
        except Exception as e:
            self.logger.error(f"Failed to open external link {user_data}: {e}")
    
    def _handle_download(self, webview, decision, response):
        """Handle download requests from WhatsApp Web with comprehensive error handling."""
        try:
            # Get download info
            uri = response.get_uri()
            suggested_filename = response.get_suggested_filename()
            
            if not uri:
                self.logger.error("Download URI is empty")
                self._show_error_dialog("Download Error", "Invalid download URL.")
                decision.ignore()
                return True
            
            # Validate filename and generate if none suggested
            if not suggested_filename:
                try:
                    from urllib.parse import urlparse
                    parsed = urlparse(uri)
                    suggested_filename = os.path.basename(parsed.path) or "whatsapp_download"
                except Exception as e:
                    self.logger.error(f"Error parsing download URI: {e}")
                    suggested_filename = "whatsapp_download"
            
            # Sanitize filename to prevent path traversal
            suggested_filename = os.path.basename(suggested_filename)
            if not suggested_filename or suggested_filename in ['.', '..']:
                suggested_filename = "whatsapp_download"
            
            # Check if downloads directory is available
            if not hasattr(self, 'downloads_dir') or not self.downloads_dir:
                self.logger.error("Downloads directory not available")
                self._show_error_dialog("Download Error", 
                                       "Downloads directory not available. Please check your system configuration.")
                decision.ignore()
                return True
            
            # Check if downloads directory is writable
            if not os.access(self.downloads_dir, os.W_OK):
                self.logger.error(f"Downloads directory not writable: {self.downloads_dir}")
                self._show_error_dialog("Download Error", 
                                       "Downloads directory is not writable. Please check permissions.")
                decision.ignore()
                return True
            
            # Check available disk space (at least 10MB for safety)
            try:
                statvfs = os.statvfs(self.downloads_dir)
                free_bytes = statvfs.f_frsize * statvfs.f_bavail
                if free_bytes < 10 * 1024 * 1024:  # 10MB
                    self.logger.error(f"Insufficient disk space: {free_bytes} bytes")
                    self._show_error_dialog("Download Error", 
                                           "Insufficient disk space for download. Please free up space and try again.")
                    decision.ignore()
                    return True
            except (OSError, AttributeError):
                # statvfs not available on some systems
                self.logger.debug("Could not check disk space for download")
            
            # Ensure unique filename
            counter = 1
            base_name, ext = os.path.splitext(suggested_filename)
            file_path = os.path.join(self.downloads_dir, suggested_filename)
            
            while os.path.exists(file_path):
                new_filename = f"{base_name}_{counter}{ext}"
                file_path = os.path.join(self.downloads_dir, new_filename)
                counter += 1
                
                # Prevent infinite loop
                if counter > 1000:
                    self.logger.error("Too many files with similar names")
                    self._show_error_dialog("Download Error", 
                                           "Too many files with similar names. Please clean up downloads directory.")
                    decision.ignore()
                    return True
            
            # Start the download manually
            try:
                from gi.repository import WebKit
                download = webview.download_uri(uri)
                if download:
                    try:
                        download.set_destination(file_path)
                        
                        # Connect to download completion
                        download.connect("finished", self._on_download_finished)
                        download.connect("failed", self._on_download_failed)
                        
                        # Send notification about download start
                        if hasattr(self.app, 'send_notification'):
                            self.app.send_notification(
                                "Download Started",
                                f"Starting download: {os.path.basename(file_path)}"
                            )
                        
                        self.logger.info(f"Download started: {file_path}")
                        
                    except Exception as e:
                        self.logger.error(f"Error setting up download: {e}")
                        self._show_error_dialog("Download Error", 
                                               "Failed to set up download. Please try again.")
                else:
                    self.logger.error("Failed to create download object")
                    self._show_error_dialog("Download Error", 
                                           "Failed to start download. Please try again.")
            except Exception as e:
                self.logger.error(f"Error starting download: {e}")
                self._show_error_dialog("Download Error", 
                                       "Failed to start download. Please check your network connection.")
            
            # Prevent the default action
            decision.ignore()
            return True
            
        except Exception as e:
            self.logger.error(f"Critical error in download handler: {e}")
            self._show_error_dialog("Download Error", 
                                   "An unexpected error occurred during download. Please try again.")
            decision.ignore()
            return True

    def _on_download_finished(self, download):
        """Handle completed downloads."""
        try:
            destination = download.get_destination()
            if destination:
                from urllib.parse import urlparse
                parsed = urlparse(destination)
                filename = os.path.basename(parsed.path)
                
                
                # Send completion notification
                if hasattr(self.app, 'send_notification'):
                    self.app.send_notification(
                        "Download Complete",
                        f"Downloaded: {filename}"
                    )
                    
        except Exception as e:
            self.logger.error(f"Error handling download completion: {e}")

    def _on_download_failed(self, download, error):
        """Handle failed downloads."""
        try:
            destination = download.get_destination()
            filename = "file"
            if destination:
                from urllib.parse import urlparse
                parsed = urlparse(destination)
                filename = os.path.basename(parsed.path)
            
            
            # Send failure notification
            if hasattr(self.app, 'send_notification'):
                self.app.send_notification(
                    "Download Failed",
                    f"Failed to download: {filename}"
                )
                
        except Exception as e:
            self.logger.error(f"Error handling download failure: {e}")
    
    def restore_window_state(self):
        """Restore window state from settings."""
        try:
            self.logger.info("Restoring window state")
            
            # Get saved window state
            width = self.settings.get_int("window-width")
            height = self.settings.get_int("window-height")
            is_maximized = self.settings.get_boolean("window-maximized")
            x = self.settings.get_int("window-x")
            y = self.settings.get_int("window-y")
            
            # Apply window geometry
            if width > 0 and height > 0:
                self.set_default_size(width, height)
                self.logger.info(f"Window size restored to: {width}x{height}")
            
            # Apply window position (only if not maximized and position was saved)
            if not is_maximized and x >= 0 and y >= 0:
                # Note: GTK4 position setting is limited on Wayland
                # This works better on X11
                try:
                    # We can't directly set position in GTK4/Wayland
                    # The window manager will place the window
                    self.logger.info(f"Window position was: ({x},{y}) - position restore limited on Wayland")
                except Exception as e:
                    self.logger.debug(f"Could not restore window position: {e}")
            
            # Apply maximized state
            if is_maximized:
                self.maximize()
                self.logger.info("Window maximized state restored")
            
        except Exception as e:
            self.logger.error(f"Failed to restore window state: {e}")
    
    def cleanup_webview(self):
        """Clean up WebView resources."""
        try:
            if hasattr(self, 'webview') and self.webview:
                self.logger.info("Cleaning up WebView resources")
                
                # Stop any ongoing loads
                self.webview.stop_loading()
                
                # Clear any pending JavaScript operations
                try:
                    if hasattr(self.webview, 'evaluate_javascript'):
                        self.webview.evaluate_javascript("window.stop();", -1, None, None, None, None, None)
                    elif hasattr(self.webview, 'run_javascript'):
                        self.webview.run_javascript("window.stop();", None, None, None)
                    else:
                        self.logger.debug("No JavaScript execution method available")
                except Exception as e:
                    self.logger.debug(f"JavaScript cleanup failed: {e}")
                
                # Disconnect signal handlers
                self._disconnect_webview_signals()
                
                # Clean up website data manager
                if hasattr(self, 'website_data_manager') and self.website_data_manager:
                    self._cleanup_website_data_manager()
                
                # Clean up network session
                if hasattr(self, 'network_session') and self.network_session:
                    self._cleanup_network_session()
                
                self.logger.info("WebView cleanup completed")
                
        except Exception as e:
            self.logger.error(f"Failed to clean up WebView: {e}")
    
    def _disconnect_webview_signals(self):
        """Disconnect WebView signal handlers."""
        try:
            if hasattr(self, 'webview') and self.webview:
                self.logger.debug("Disconnecting WebView signals")
                
                # Disconnect all signal handlers
                self.webview.disconnect_by_func(self._on_load_changed)
                self.webview.disconnect_by_func(self._on_decide_policy)
                
                # Disconnect other signal handlers if they exist
                if hasattr(self, '_on_load_failed'):
                    self.webview.disconnect_by_func(self._on_load_failed)
                
                self.logger.debug("WebView signals disconnected")
                
        except Exception as e:
            self.logger.error(f"Failed to disconnect WebView signals: {e}")
    
    def _cleanup_website_data_manager(self):
        """Clean up website data manager."""
        try:
            if hasattr(self, 'website_data_manager') and self.website_data_manager:
                self.logger.debug("Cleaning up website data manager")
                
                # Clear any cached data if needed
                # Note: Be careful not to clear persistent data like cookies
                # unless explicitly requested by the user
                
                self.logger.debug("Website data manager cleanup completed")
                
        except Exception as e:
            self.logger.error(f"Failed to clean up website data manager: {e}")
    
    def _cleanup_network_session(self):
        """Clean up network session."""
        try:
            if hasattr(self, 'network_session') and self.network_session:
                self.logger.debug("Cleaning up network session")
                
                # Clean up any pending network operations
                # Note: NetworkSession cleanup is mostly handled by WebKit
                
                self.logger.debug("Network session cleanup completed")
                
        except Exception as e:
            self.logger.error(f"Failed to clean up network session: {e}")
    
    def cleanup_downloads(self):
        """Clean up any active downloads."""
        try:
            if hasattr(self, 'active_downloads') and self.active_downloads:
                self.logger.info("Cleaning up active downloads")
                
                # Cancel any active downloads
                for download in self.active_downloads:
                    try:
                        download.cancel()
                        self.logger.debug(f"Cancelled download: {download.get_destination()}")
                    except Exception as e:
                        self.logger.warning(f"Failed to cancel download: {e}")
                
                self.active_downloads.clear()
                self.logger.info("Active downloads cleanup completed")
                
        except Exception as e:
            self.logger.error(f"Failed to clean up downloads: {e}")
    
    def force_cleanup(self):
        """Force cleanup of window resources."""
        try:
            self.logger.info("Performing force cleanup of window resources")
            
            # Force cleanup of WebView
            self.cleanup_webview()
            
            # Force cleanup of downloads
            self.cleanup_downloads()
            
            # Force cleanup of any other resources
            self._cleanup_other_resources()
            
            self.logger.info("Force cleanup completed")
            
        except Exception as e:
            self.logger.error(f"Failed to perform force cleanup: {e}")
    
    def _cleanup_other_resources(self):
        """Clean up other window resources."""
        try:
            self.logger.debug("Cleaning up other window resources")
            
            # Clean up any timers or scheduled operations
            if hasattr(self, '_timers'):
                for timer in self._timers:
                    try:
                        GLib.source_remove(timer)
                    except Exception:
                        pass
                self._timers.clear()
            
            # Clean up any other resources
            # Add more cleanup as needed
            
            self.logger.debug("Other resources cleanup completed")
            
        except Exception as e:
            self.logger.error(f"Failed to clean up other resources: {e}")
