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


@Gtk.Template(resource_path='/io/github/tobagin/karere/window.ui')
class KarereWindow(Adw.ApplicationWindow):
    """Main application window containing the WebView."""
    
    __gtype_name__ = 'KarereWindow'
    
    webview_container = Gtk.Template.Child()
    
    def __init__(self, app):
        print("DEBUG: Window __init__ started")
        super().__init__(application=app)
        self.app = app
        print("DEBUG: Template initialized")
        
        # Initialize settings
        self.settings = Gio.Settings.new("io.github.tobagin.karere")
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
        data_dir = os.environ.get('XDG_DATA_HOME', os.path.expanduser('~/.local/share')) + '/karere'
        cache_dir = os.environ.get('XDG_CACHE_HOME', os.path.expanduser('~/.cache')) + '/karere'
        
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
        
        # Get the cookie manager from the network session
        self.cookie_manager = self.network_session.get_cookie_manager()
        
        # Configure cookie persistence
        cookie_file = os.path.join(data_dir, 'cookies.sqlite')
        self.cookie_manager.set_persistent_storage(cookie_file, WebKit.CookiePersistentStorage.SQLITE)
        print("DEBUG: Cookie persistence configured")
        
        # Create WebView first
        self.webview = WebKit.WebView.new()
        print("DEBUG: WebView created")
        
        # Configure WebView settings
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
        print(f"DEBUG: User agent set to: {user_agent}")
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
        
        # Set up download handling
        self.setup_download_directory()
        self.webview.connect("decide-policy", self._on_decide_policy)
        
        # Inject user agent override script
        self._inject_user_agent_override()
        
        # Load WhatsApp Web
        self.webview.load_uri("https://web.whatsapp.com")
        print("DEBUG: Loading WhatsApp Web")
    
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
        print(f"DEBUG: User agent override script injected for {app_name}")
    
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
        settings_dialog = KarereSettingsDialog(self)
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

    def setup_download_directory(self):
        """Set up the downloads directory."""
        try:
            # Use the user's Downloads directory
            downloads_dir = os.path.join(os.path.expanduser('~'), 'Downloads')
            self.downloads_dir = downloads_dir
            print(f"DEBUG: Downloads directory: {self.downloads_dir}")
        except Exception as e:
            print(f"DEBUG: Error setting up downloads directory: {e}")
            # Fallback to home directory
            self.downloads_dir = os.path.expanduser('~')

    def _on_decide_policy(self, webview, decision, decision_type):
        """Handle policy decisions including downloads and navigation."""
        from gi.repository import WebKit
        
        print(f"DEBUG: Policy decision type: {decision_type}")
        
        # Print the actual enum values for debugging
        print(f"DEBUG: NAVIGATION_ACTION = {WebKit.PolicyDecisionType.NAVIGATION_ACTION}")
        print(f"DEBUG: NEW_WINDOW_ACTION = {WebKit.PolicyDecisionType.NEW_WINDOW_ACTION}")
        print(f"DEBUG: RESPONSE = {WebKit.PolicyDecisionType.RESPONSE}")
        
        # Check if this is a navigation decision (link click)
        if decision_type == WebKit.PolicyDecisionType.NAVIGATION_ACTION:
            print("DEBUG: Processing NAVIGATION_ACTION")
        elif decision_type == WebKit.PolicyDecisionType.NEW_WINDOW_ACTION:
            print("DEBUG: Processing NEW_WINDOW_ACTION - this might be external links!")
            try:
                navigation_action = decision.get_navigation_action()
                if navigation_action:
                    request = navigation_action.get_request()
                    if request:
                        uri = request.get_uri()
                        print(f"DEBUG: NEW_WINDOW_ACTION URI: {uri}")
                        
                        if self._should_open_externally(uri):
                            print(f"DEBUG: Opening externally from NEW_WINDOW_ACTION: {uri}")
                            self._open_external_link(uri)
                            decision.ignore()
                            return True
                        else:
                            print(f"DEBUG: Allowing NEW_WINDOW_ACTION internally: {uri}")
                            decision.use()
                            return True
            except Exception as e:
                print(f"DEBUG: Error handling NEW_WINDOW_ACTION: {e}")
                return False
        
        # Original navigation action handling
        if decision_type == WebKit.PolicyDecisionType.NAVIGATION_ACTION:
            print("DEBUG: Processing NAVIGATION_ACTION")
            try:
                navigation_action = decision.get_navigation_action()
                if navigation_action:
                    request = navigation_action.get_request()
                    if request:
                        uri = request.get_uri()
                        navigation_type = navigation_action.get_navigation_type()
                        
                        print(f"DEBUG: Navigation type: {navigation_type}, URI: {uri}")
                        
                        # Handle external links (clicked links that leave WhatsApp Web)
                        if navigation_type == WebKit.NavigationType.LINK_CLICKED:
                            print(f"DEBUG: Link clicked: {uri}")
                            if self._should_open_externally(uri):
                                print(f"DEBUG: Opening externally: {uri}")
                                self._open_external_link(uri)
                                decision.ignore()
                                return True
                            else:
                                print(f"DEBUG: Allowing internal navigation: {uri}")
                                decision.use()
                                return True
                        else:
                            print(f"DEBUG: Other navigation type: {navigation_type}")
                    else:
                        print("DEBUG: No request found in navigation action")
                else:
                    print("DEBUG: No navigation action found")
            except Exception as e:
                print(f"DEBUG: Error handling navigation action: {e}")
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
        
        print(f"DEBUG: Checking URI for external opening: {uri}")
        
        # Parse the URI to check domain
        try:
            from urllib.parse import urlparse
            parsed = urlparse(uri)
            domain = parsed.netloc.lower()
            scheme = parsed.scheme.lower()
            
            print(f"DEBUG: Parsed URI - scheme: {scheme}, domain: {domain}")
            
            # Always handle internal schemes internally
            if scheme in ['data', 'blob', 'javascript', 'about']:
                print(f"DEBUG: Internal scheme {scheme} - keeping internal")
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
                print(f"DEBUG: WhatsApp domain {domain} - keeping internal")
                return False
            
            # If there's no domain (relative URLs), keep internal
            if not domain:
                print(f"DEBUG: No domain (relative URL) - keeping internal")
                return False
            
            # Only open external domains in browser
            print(f"DEBUG: External domain {domain} - opening externally")
            return True
            
        except Exception as e:
            print(f"DEBUG: Error parsing URI {uri}: {e}")
            return False
    
    def _open_external_link(self, uri):
        """Open a URI in the system's default browser using Flatpak portal."""
        try:
            print(f"DEBUG: Opening external link via portal: {uri}")
            
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
            
            print(f"DEBUG: External link launch initiated: {uri}")
            
        except Exception as e:
            print(f"DEBUG: Error opening external link {uri}: {e}")
            # Fallback: try the synchronous version
            try:
                from gi.repository import Gio
                Gio.AppInfo.launch_default_for_uri(uri, None)
                print(f"DEBUG: Opened external link with fallback method: {uri}")
            except Exception as e2:
                print(f"DEBUG: Failed to open external link with fallback: {e2}")
    
    def _on_external_link_opened(self, source, result, user_data):
        """Callback for external link opening."""
        try:
            from gi.repository import Gio
            Gio.AppInfo.launch_default_for_uri_finish(result)
            print(f"DEBUG: Successfully opened external link: {user_data}")
        except Exception as e:
            print(f"DEBUG: Failed to open external link {user_data}: {e}")
    
    def _handle_download(self, webview, decision, response):
        """Handle download requests from WhatsApp Web."""
        try:
            print("DEBUG: Download requested")
            
            # Get download info
            uri = response.get_uri()
            suggested_filename = response.get_suggested_filename()
            
            print(f"DEBUG: Download URI: {uri}")
            print(f"DEBUG: Suggested filename: {suggested_filename}")
            
            # Generate filename if none suggested
            if not suggested_filename:
                from urllib.parse import urlparse
                parsed = urlparse(uri)
                suggested_filename = os.path.basename(parsed.path) or "whatsapp_download"
            
            # Ensure unique filename
            counter = 1
            base_name, ext = os.path.splitext(suggested_filename)
            file_path = os.path.join(self.downloads_dir, suggested_filename)
            
            while os.path.exists(file_path):
                new_filename = f"{base_name}_{counter}{ext}"
                file_path = os.path.join(self.downloads_dir, new_filename)
                counter += 1
            
            print(f"DEBUG: Download path: {file_path}")
            
            # Start the download manually
            from gi.repository import WebKit
            download = webview.download_uri(uri)
            if download:
                download.set_destination(file_path)
                
                # Connect to download completion
                download.connect("finished", self._on_download_finished)
                download.connect("failed", self._on_download_failed)
                
                # Send notification about download start
                if hasattr(self.app, 'send_notification'):
                    self.app.send_notification(
                        "Download Started",
                        f"Starting download: {suggested_filename}"
                    )
            
            # Prevent the default action
            decision.ignore()
            return True
            
        except Exception as e:
            print(f"DEBUG: Error handling download request: {e}")
            return False

    def _on_download_finished(self, download):
        """Handle completed downloads."""
        try:
            destination = download.get_destination()
            if destination:
                from urllib.parse import urlparse
                parsed = urlparse(destination)
                filename = os.path.basename(parsed.path)
                
                print(f"DEBUG: Download completed: {filename}")
                
                # Send completion notification
                if hasattr(self.app, 'send_notification'):
                    self.app.send_notification(
                        "Download Complete",
                        f"Downloaded: {filename}"
                    )
                    
        except Exception as e:
            print(f"DEBUG: Error handling download completion: {e}")

    def _on_download_failed(self, download, error):
        """Handle failed downloads."""
        try:
            destination = download.get_destination()
            filename = "file"
            if destination:
                from urllib.parse import urlparse
                parsed = urlparse(destination)
                filename = os.path.basename(parsed.path)
            
            print(f"DEBUG: Download failed: {filename}, Error: {error}")
            
            # Send failure notification
            if hasattr(self.app, 'send_notification'):
                self.app.send_notification(
                    "Download Failed",
                    f"Failed to download: {filename}"
                )
                
        except Exception as e:
            print(f"DEBUG: Error handling download failure: {e}")