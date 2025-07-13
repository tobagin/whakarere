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
        
        # Connect close event to background running
        self.connect("close-request", self._on_close_request)
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
        
        # Set up script message handler for notifications
        user_content_manager = self.webview.get_user_content_manager()
        user_content_manager.connect("script-message-received::notification", self._on_notification_message)
        user_content_manager.register_script_message_handler("notification")
        print("DEBUG: Script message handler registered")
        
        # Add WebView to container with expand properties
        self.webview.set_vexpand(True)
        self.webview.set_hexpand(True)
        self.webview_container.append(self.webview)
        print("DEBUG: WebView added to container")
        
        # Connect to page load events to inject JavaScript
        self.webview.connect("load-changed", self._on_load_changed)
        
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
    
    def _on_close_request(self, window):
        """Handle window close request - hide instead of quit."""
        print("DEBUG: Window close request received")
        return self.app.on_window_delete_event()
    
    def _on_load_changed(self, webview, load_event):
        """Handle WebView load events to inject JavaScript for notifications."""
        if load_event == WebKit.LoadEvent.FINISHED:
            print("DEBUG: Page load finished, injecting JavaScript for message detection")
            self._inject_notification_script()
    
    def _inject_notification_script(self):
        """Inject JavaScript to detect new WhatsApp messages."""
        js_script = """
        (function() {
            console.log('Whakarere: Notification script injected');
            
            let lastMessageCount = 0;
            let isWindowFocused = true;
            let lastNotificationTime = 0;
            let lastMessageText = '';
            
            // Check if window is focused
            window.addEventListener('focus', () => { 
                isWindowFocused = true; 
                console.log('Whakarere: Window focused');
            });
            window.addEventListener('blur', () => { 
                isWindowFocused = false; 
                console.log('Whakarere: Window blurred');
            });
            
            
            // Simple DOM check for debugging
            function inspectDOM() {
                const unreadElements = document.querySelectorAll('[data-icon="unread-count"], [data-testid="unread-count"]');
                if (unreadElements.length > 0) {
                    console.log('Whakarere: Found', unreadElements.length, 'unread indicators');
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
                        console.log('Whakarere: Unread count changed:', totalUnread);
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
                            console.log('Whakarere: Notification sent for:', senderName);
                        }
                    }
                    
                    lastMessageCount = totalUnread;
                    lastMessageText = latestMessageText;
                    
                } catch (error) {
                    console.error('Whakarere: Error checking messages:', error);
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
                    console.log('Whakarere: DOM observer started');
                    
                    // Initial check after observer starts
                    setTimeout(checkForNewMessages, 1000);
                } else {
                    setTimeout(startObserving, 1000);
                }
            }
            
            startObserving();
            console.log('Whakarere: Enhanced message detection initialized');
        })();
        """
        
        print("DEBUG: Executing JavaScript for message detection")
        self.webview.evaluate_javascript(js_script, -1, None, None, None, self._on_javascript_result, None)
    
    def _on_javascript_result(self, webview, task, user_data):
        """Handle JavaScript execution result."""
        try:
            webview.evaluate_javascript_finish(task)
            print("DEBUG: JavaScript injection completed successfully")
        except Exception as e:
            print(f"DEBUG: JavaScript injection failed: {e}")
    
    def _on_notification_message(self, user_content_manager, message):
        """Handle notification messages from JavaScript."""
        try:
            # Get the message data
            js_value = message.get_js_value()
            if js_value.is_object():
                sender = js_value.object_get_property("sender").to_string() if js_value.object_has_property("sender") else "WhatsApp"
                msg_text = js_value.object_get_property("message").to_string() if js_value.object_has_property("message") else "New message"
                count = js_value.object_get_property("count").to_number() if js_value.object_has_property("count") else 1
                
                print(f"DEBUG: Received notification request - Sender: {sender}, Message: {msg_text}, Count: {count}")
                
                # Send the notification through the application
                notification_title = f"New message from {sender}" if sender != "WhatsApp" else "WhatsApp"
                notification_body = f"{msg_text} ({int(count)} unread)" if count > 1 else msg_text
                
                self.app.send_notification(notification_title, notification_body)
            else:
                print("DEBUG: Received non-object notification message")
                
        except Exception as e:
            print(f"DEBUG: Error handling notification message: {e}")
            # Fallback notification
            self.app.send_notification("WhatsApp", "New message received")