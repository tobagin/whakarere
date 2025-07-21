#!/usr/bin/env python3
"""
Test script to verify WebKit notification signals.
This script creates a minimal WebView and tests if notification signals are triggered.
"""

import gi
import sys
import logging

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
gi.require_version("WebKit", "6.0")

from gi.repository import Gtk, Adw, WebKit, GLib

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("webkit_test")

class TestApp(Adw.Application):
    def __init__(self):
        super().__init__(application_id="org.test.WebKitNotifications")
        self.webview = None
        
    def do_activate(self):
        window = Adw.ApplicationWindow(application=self)
        window.set_title("WebKit Notifications Test")
        window.set_default_size(800, 600)
        
        # Create WebView
        self.webview = WebKit.WebView()
        
        # Set up settings to ensure notifications work
        settings = self.webview.get_settings()
        settings.set_enable_javascript(True)
        settings.set_enable_media(True)
        settings.set_enable_mediasource(True)
        
        # Connect signals
        self.webview.connect("permission-request", self._on_permission_request)
        self.webview.connect("show-notification", self._on_show_notification)
        self.webview.connect("load-changed", self._on_load_changed)
        
        # Create a scrolled window and add webview
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_child(self.webview)
        window.set_content(scrolled)
        
        window.present()
        
        # Load a test page that will request notification permission and show notifications
        test_html = '''
        <!DOCTYPE html>
        <html>
        <head>
            <title>Notification Test</title>
        </head>
        <body>
            <h1>WebKit Notification Test</h1>
            <button onclick="requestNotificationPermission()">Request Permission</button>
            <button onclick="showNotification()">Show Notification</button>
            <div id="status"></div>
            
            <script>
                function log(message) {
                    console.log(message);
                    document.getElementById('status').innerHTML += message + '<br>';
                }
                
                function requestNotificationPermission() {
                    log('Requesting notification permission...');
                    
                    if (!('Notification' in window)) {
                        log('This browser does not support notifications');
                        return;
                    }
                    
                    Notification.requestPermission().then(function(permission) {
                        log('Permission result: ' + permission);
                    });
                }
                
                function showNotification() {
                    log('Attempting to show notification...');
                    
                    if (!('Notification' in window)) {
                        log('This browser does not support notifications');
                        return;
                    }
                    
                    if (Notification.permission === 'granted') {
                        var notification = new Notification('Test Notification', {
                            body: 'This is a test notification from WebKit',
                            tag: 'test',
                            icon: ''
                        });
                        
                        notification.onclick = function() {
                            log('Notification clicked!');
                        };
                        
                        notification.onclose = function() {
                            log('Notification closed!');
                        };
                        
                        log('Notification created');
                    } else {
                        log('Notification permission is: ' + Notification.permission);
                        if (Notification.permission !== 'denied') {
                            requestNotificationPermission();
                        }
                    }
                }
                
                // Auto-request permission on load
                window.onload = function() {
                    log('Page loaded, Notification available: ' + ('Notification' in window));
                    requestNotificationPermission();
                };
            </script>
        </body>
        </html>
        '''
        
        self.webview.load_html(test_html, "file:///")
        
    def _on_load_changed(self, webview, load_event):
        logger.info(f"Load changed: {load_event}")
        
    def _on_permission_request(self, webview, request):
        logger.info(f"Permission request received: {type(request)}")
        
        if isinstance(request, WebKit.NotificationPermissionRequest):
            logger.info("Notification permission requested - ALLOWING")
            request.allow()
            return True
        else:
            logger.info(f"Other permission request: {type(request)}")
            return False
    
    def _on_show_notification(self, webview, notification):
        logger.info("SHOW NOTIFICATION SIGNAL TRIGGERED!")
        
        try:
            title = notification.get_title()
            body = notification.get_body() 
            tag = notification.get_tag()
            
            logger.info(f"Notification details - Title: {title}, Body: {body}, Tag: {tag}")
            
            # Connect to notification signals
            notification.connect("clicked", lambda n: logger.info("Notification clicked!"))
            notification.connect("closed", lambda n: logger.info("Notification closed!"))
            
            return True
        except Exception as e:
            logger.error(f"Error handling notification: {e}")
            return False

if __name__ == "__main__":
    app = TestApp()
    app.run(sys.argv)