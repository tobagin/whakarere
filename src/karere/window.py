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
            
            # Set user agent to avoid mobile version and show custom app name
            from .application import BUS_NAME
            app_name = "Karere.dev" if BUS_NAME.endswith('.dev') else "Karere"
            # WhatsApp Web detects the Chrome part, so replace it with our app name
            user_agent = f"Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) {app_name}/120.0.0.0 Safari/537.36"
            webkit_settings.set_user_agent(user_agent)
            
            self.logger.info("WebView settings configured")
        except Exception as e:
            self.logger.error(f"Failed to configure WebView settings: {e}")
            self.logger.warning("Continuing with default WebView settings")
        
        # Set up script message handler for notifications with error handling
        try:
            user_content_manager = self.webview.get_user_content_manager()
            user_content_manager.connect("script-message-received::notification", self._on_notification_message)
            user_content_manager.register_script_message_handler("notification")
            self.logger.info("Script message handler configured")
        except Exception as e:
            self.logger.error(f"Failed to set up script message handler: {e}")
            self.logger.warning("Continuing without notification script handler")
        
        # Add WebView to container with expand properties
        self.webview.set_vexpand(True)
        self.webview.set_hexpand(True)
        self.webview_container.append(self.webview)
        
        # Connect to page load events to inject JavaScript
        self.webview.connect("load-changed", self._on_load_changed)
        
        # Set up download handling
        self.setup_download_directory()
        self.webview.connect("decide-policy", self._on_decide_policy)
        
        # Set up WebView event handlers for error handling
        self._setup_webview_error_handlers()
        
        # Inject user agent override script
        self._inject_user_agent_override()
        
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
        user_content_manager.add_script(script)
        self.logger.info(f"User agent override script injected for {app_name}")
    
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
                self.logger.info("Page load finished, injecting notification script and CSS fixes")
                self._inject_notification_script()
                self._inject_css_fixes()
            elif load_event == WebKit.LoadEvent.STARTED:
                self.logger.info("Page load started")
            elif load_event == WebKit.LoadEvent.COMMITTED:
                self.logger.info("Page load committed")
        except Exception as e:
            self.logger.error(f"Error handling load event: {e}")
    
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
    
    def _on_load_changed(self, webview, load_event):
        """Handle WebView load events to inject JavaScript for notifications."""
        # Delegate to the error-handling version
        self._on_load_changed_with_error_handling(webview, load_event)
    
    def _inject_notification_script(self):
        """Inject JavaScript to detect new WhatsApp messages."""
        js_script = """
        (function() {
            console.log('Karere: Notification script injected');
            
            let lastMessageCount = 0;
            let isWindowFocused = true;
            let lastNotificationTime = 0;
            let lastMessageText = '';
            
            // Check if window is focused
            window.addEventListener('focus', () => { 
                isWindowFocused = true; 
                console.log('Karere: Window focused');
            });
            window.addEventListener('blur', () => { 
                isWindowFocused = false; 
                console.log('Karere: Window blurred');
            });
            
            
            // Simple DOM check for debugging
            function inspectDOM() {
                const unreadElements = document.querySelectorAll('[data-icon="unread-count"], [data-testid="unread-count"]');
                if (unreadElements.length > 0) {
                    console.log('Karere: Found', unreadElements.length, 'unread indicators');
                }
            }
            
            function checkForNewMessages() {
                try {
                    let totalUnread = 0;
                    let hasNewMessages = false;
                    let foundElements = [];
                    
                    // Enhanced detection with multiple approaches
                    const detectionMethods = [
                        // Method 1: Standard unread count selectors
                        () => {
                            const selectors = [
                                '[data-icon="unread-count"]',
                                '[data-testid="unread-count"]', 
                                'span[data-icon="unread-count"]'
                            ];
                            let count = 0;
                            for (const selector of selectors) {
                                const elements = document.querySelectorAll(selector);
                                elements.forEach(el => {
                                    const text = el.textContent || el.innerText;
                                    const num = parseInt(text?.replace(/[^0-9]/g, '')) || 0;
                                    if (num > 0) {
                                        count += num;
                                        foundElements.push({selector, text, num});
                                    }
                                });
                            }
                            return count;
                        },
                        
                        // Method 2: Aria-label based detection
                        () => {
                            const elements = document.querySelectorAll('[aria-label*="unread"], [aria-label*="message"]');
                            let count = 0;
                            elements.forEach(el => {
                                const ariaLabel = el.getAttribute('aria-label') || '';
                                const matches = ariaLabel.match(/\\d+/g);
                                if (matches) {
                                    const num = parseInt(matches[0]) || 0;
                                    if (num > 0) {
                                        count += num;
                                        foundElements.push({method: 'aria-label', ariaLabel, num});
                                    }
                                }
                            });
                            return count;
                        },
                        
                        // Method 3: Visual indicator dots
                        () => {
                            const indicators = document.querySelectorAll('[data-icon="unread"], span[data-icon="unread"]');
                            if (indicators.length > 0) {
                                foundElements.push({method: 'visual-dots', count: indicators.length});
                                return indicators.length;
                            }
                            return 0;
                        },
                        
                        // Method 4: Chat container analysis
                        () => {
                            const chatContainers = document.querySelectorAll('div[data-testid="cell-frame-container"]');
                            let count = 0;
                            chatContainers.forEach(container => {
                                const spans = container.querySelectorAll('span');
                                spans.forEach(span => {
                                    const text = span.textContent?.trim();
                                    if (text && /^\\d+$/.test(text)) {
                                        const num = parseInt(text);
                                        if (num > 0 && num < 100) { // Reasonable message count
                                            count += num;
                                            foundElements.push({method: 'chat-container', text, num});
                                        }
                                    }
                                });
                            });
                            return count;
                        }
                    ];
                    
                    // Run all detection methods
                    for (const method of detectionMethods) {
                        const methodCount = method();
                        totalUnread += methodCount;
                        if (methodCount > 0) hasNewMessages = true;
                    }
                    
                    // Log detection results when there are changes
                    if (totalUnread !== lastMessageCount) {
                        console.log('Karere: Unread count changed:', totalUnread);
                    }
                    
                    // Check for new message content
                    const messageElements = document.querySelectorAll('[data-testid="msg-container"], [data-testid="conversation-panel-messages"] > div:last-child');
                    let latestMessageText = '';
                    if (messageElements.length > 0) {
                        const lastMessage = messageElements[messageElements.length - 1];
                        latestMessageText = lastMessage.textContent?.substring(0, 100) || '';
                    }
                    
                    // Trigger notification based on multiple conditions
                    const now = Date.now();
                    const shouldNotify = !isWindowFocused && (
                        (hasNewMessages && totalUnread > lastMessageCount) ||
                        (latestMessageText && latestMessageText !== lastMessageText && latestMessageText.length > 0)
                    ) && (now - lastNotificationTime) > 3000; // Reduced cooldown
                    
                    if (shouldNotify) {
                        // Try to get the sender name
                        let senderName = 'WhatsApp';
                        const senderSelectors = [
                            '[aria-selected="true"] [title]',
                            '[data-testid="conversation-title"]',
                            'header [data-testid="conversation-info-header"] span[title]',
                            '._ao3e ._aou8 + div'
                        ];
                        
                        for (const selector of senderSelectors) {
                            const element = document.querySelector(selector);
                            if (element) {
                                senderName = element.textContent || element.getAttribute('title') || senderName;
                                break;
                            }
                        }
                        
                        // Send notification
                        if (window.webkit && window.webkit.messageHandlers && window.webkit.messageHandlers.notification) {
                            window.webkit.messageHandlers.notification.postMessage({
                                sender: senderName,
                                message: totalUnread > 0 ? `${totalUnread} new message(s)` : 'New message received',
                                count: totalUnread || 1
                            });
                            lastNotificationTime = now;
                            console.log('Karere: Notification sent for:', senderName);
                        }
                    }
                    
                    lastMessageCount = totalUnread;
                    lastMessageText = latestMessageText;
                    
                } catch (error) {
                    console.error('Karere: Error checking messages:', error);
                }
            }
            
            // DOM inspection after 5 seconds (for debugging)
            setTimeout(inspectDOM, 5000);
            
            // Check every 2 seconds for new messages
            setInterval(checkForNewMessages, 2000);
            
            // Also listen for DOM changes with throttling
            let timeoutId;
            const observer = new MutationObserver((mutations) => {
                // Check if any relevant changes occurred
                const relevantMutation = mutations.some(mutation => {
                    return mutation.type === 'childList' || 
                           (mutation.type === 'attributes' && 
                            ['aria-label', 'data-icon', 'data-testid', 'title'].includes(mutation.attributeName));
                });
                
                if (relevantMutation) {
                    clearTimeout(timeoutId);
                    timeoutId = setTimeout(checkForNewMessages, 500);
                }
            });
            
            // Start observing when the page is ready
            function startObserving() {
                if (document.body) {
                    observer.observe(document.body, {
                        childList: true,
                        subtree: true,
                        attributes: true,
                        attributeFilter: ['aria-label', 'data-icon', 'data-testid', 'title', 'class']
                    });
                    console.log('Karere: DOM observer started');
                    
                    // Initial check after observer starts
                    setTimeout(checkForNewMessages, 1000);
                } else {
                    setTimeout(startObserving, 1000);
                }
            }
            
            startObserving();
            console.log('Karere: Enhanced message detection initialized');
        })();
        """
        
        self.logger.info("Injecting notification detection script")
        self.webview.evaluate_javascript(js_script, -1, None, None, None, self._on_javascript_result, None)
    
    def _inject_css_fixes(self):
        """Inject CSS fixes for emoji rendering and other WebKit-specific issues."""
        css_fixes = """
        (function() {
            console.log('Karere: Injecting CSS fixes for emoji rendering');
            
            const style = document.createElement('style');
            style.textContent = `
                /* Fix emoji height and rendering issues */
                [data-emoji-picker] img.emoji,
                .emoji-picker img,
                .emoji-mart-emoji img,
                ._2cNQ._3MZy img,
                ._2cNQ img,
                .emoji img,
                span[data-emoji] img,
                span[data-emoji],
                .emoji-picker-emoji img,
                .emoji-panel img.emoji,
                .emoji-category-content img.emoji {
                    height: 24px !important;
                    width: 24px !important;
                    min-height: 24px !important;
                    min-width: 24px !important;
                    line-height: 24px !important;
                    display: inline-block !important;
                    vertical-align: middle !important;
                    object-fit: contain !important;
                }
                
                /* Fix emoji container heights */
                [data-emoji-picker] ._2cNQ._3MZy,
                [data-emoji-picker] ._2cNQ,
                .emoji-picker-emoji,
                .emoji-panel .emoji-category-content > div,
                .emoji-panel .emoji-category-content span {
                    height: 32px !important;
                    min-height: 32px !important;
                    line-height: 32px !important;
                    display: inline-flex !important;
                    align-items: center !important;
                    justify-content: center !important;
                    padding: 4px !important;
                }
                
                /* Fix emoji picker grid layout */
                .emoji-picker-category .emoji-picker-emoji,
                .emoji-category-content {
                    display: grid !important;
                    grid-template-columns: repeat(auto-fill, 32px) !important;
                    gap: 4px !important;
                }
                
                /* Fix emoji panel scrolling */
                .emoji-panel,
                .emoji-picker-scroll {
                    overflow-y: auto !important;
                    max-height: 400px !important;
                }
                
                /* Ensure emoji characters render properly */
                span[data-emoji]:not(:empty),
                .emoji-char {
                    font-size: 20px !important;
                    line-height: 24px !important;
                    height: 24px !important;
                    width: 24px !important;
                    display: inline-block !important;
                    text-align: center !important;
                    vertical-align: middle !important;
                }
                
                /* Fix search and category headers */
                .emoji-picker-search,
                .emoji-picker-category-label {
                    height: auto !important;
                    min-height: 32px !important;
                    line-height: 32px !important;
                }
                
                /* WebKit-specific emoji font rendering */
                @supports (-webkit-appearance: none) {
                    .emoji, [data-emoji], span[data-emoji] {
                        font-family: "Apple Color Emoji", "Segoe UI Emoji", "Noto Color Emoji", "Twemoji Mozilla", "Noto Emoji", "EmojiOne Color", "Android Emoji", sans-serif !important;
                        font-variant-emoji: emoji !important;
                        text-rendering: optimizeLegibility !important;
                        -webkit-font-smoothing: antialiased !important;
                        -moz-osx-font-smoothing: grayscale !important;
                    }
                }
                
                /* Fix specific WhatsApp Web emoji selectors */
                ._2cNQ {
                    min-height: 32px !important;
                    height: 32px !important;
                    display: flex !important;
                    align-items: center !important;
                    justify-content: center !important;
                }
                
                ._2cNQ._3MZy {
                    padding: 4px !important;
                }
                
                /* Fix emoji hover and selection states */
                [data-emoji-picker] ._2cNQ:hover,
                .emoji-picker-emoji:hover {
                    background-color: rgba(0, 0, 0, 0.1) !important;
                    border-radius: 4px !important;
                }
                
                /* Force reflow to apply changes */
                [data-emoji-picker] {
                    transform: translateZ(0) !important;
                }
            `;
            
            document.head.appendChild(style);
            console.log('Karere: CSS fixes applied for emoji rendering');
            
            // Force reflow of emoji elements
            setTimeout(() => {
                const emojiElements = document.querySelectorAll('[data-emoji-picker], .emoji-picker, .emoji-panel, ._2cNQ, [data-emoji]');
                emojiElements.forEach(el => {
                    el.style.transform = 'translateZ(0)';
                    el.offsetHeight; // Force reflow
                    el.style.transform = '';
                });
                console.log('Karere: Forced reflow of emoji elements');
            }, 1000);
            
        })();
        """
        
        self.webview.evaluate_javascript(css_fixes, -1, None, None, None, self._on_css_fixes_result, None)
    
    def _on_css_fixes_result(self, webview, task, user_data):
        """Handle CSS fixes injection result."""
        try:
            webview.evaluate_javascript_finish(task)
            self.logger.debug("CSS fixes injection completed successfully")
        except Exception as e:
            self.logger.error(f"CSS fixes injection failed: {e}")
    
    def _on_javascript_result(self, webview, task, user_data):
        """Handle JavaScript execution result."""
        try:
            webview.evaluate_javascript_finish(task)
            self.logger.debug("JavaScript injection completed successfully")
        except Exception as e:
            self.logger.error(f"JavaScript injection failed: {e}")
    
    def _on_notification_message(self, user_content_manager, message):
        """Handle notification messages from JavaScript."""
        try:
            # Get the message data
            js_value = message.get_js_value()
            if js_value.is_object():
                sender = js_value.object_get_property("sender").to_string() if js_value.object_has_property("sender") else "WhatsApp"
                msg_text = js_value.object_get_property("message").to_string() if js_value.object_has_property("message") else "New message"
                count = js_value.object_get_property("count").to_number() if js_value.object_has_property("count") else 1
                
                
                # Send the notification through the application
                notification_title = f"New message from {sender}" if sender != "WhatsApp" else "WhatsApp"
                notification_body = f"{msg_text} ({int(count)} unread)" if count > 1 else msg_text
                
                self.app.send_notification(notification_title, notification_body)
            else:
                self.logger.debug("Received non-object notification message")
                
        except Exception as e:
            self.logger.error(f"Error handling notification message: {e}")
            # Fallback notification
            self.app.send_notification("WhatsApp", "New message received")

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
            
            # Apply window geometry
            if width > 0 and height > 0:
                self.set_default_size(width, height)
                self.logger.info(f"Window size restored to: {width}x{height}")
            
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
                self.webview.run_javascript("window.stop();", None, None, None)
                
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
