import gi

gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from whakarere.managers.app import AppManager
from whakarere.pages.session import SessionManagerPage
from gi.repository import Adw

class WhakarereWindow(Adw.ApplicationWindow):
    def __init__(self, app, debug=False, dev=False):
        super().__init__(application=app)
        self.debug = debug
        self.dev = dev
        self.app = app
        self.app_manager = AppManager(self, debug=self.debug, dev=self.dev)
        self.set_default_size(800, 600)
        self.set_hide_on_close(True)
        # app.send_notification("Whakarere", "Whakarere is running")

        # Create navigation view
        self.navigation_view = Adw.NavigationView()
        self.session_manager_page = SessionManagerPage(self.app_manager)
        self.navigation_view.push(self.session_manager_page)

        # Set the navigation view as the content of the main window
        self.set_content(self.navigation_view)