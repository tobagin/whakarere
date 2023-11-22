import gi

gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
gi.require_version("Gdk", "4.0")

from whakarere.managers.config import ConfigManager
from whakarere.managers.session import SessionManager
from whakarere.managers.whatsapp import WhatsAppSessionManager
from whakarere.widgets.titlebar import WindowTitlebarWidget
from whakarere.widgets.main_menu import MainMenuButtonWidget
from whakarere.pages.session import SessionManagerPage
from whakarere.pages.session2 import SessionManagerPage2
from whakarere.windows.account_wizard import AccountWizardWindow
from gi.repository import Adw, Gtk, Gdk

class WhakarereMainWindow(Adw.ApplicationWindow):
    def __init__(self, app, debug=False, dev=False):
        super().__init__(application=app)
        self.app = app
        self.debug = debug
        self.dev = dev

        self.settings = Gtk.Settings.get_default()
        self.settings.connect("notify::gtk-theme-name", self.on_theme_changed)

        # Initial CSS application
        self.update_css_for_theme()

        # Set the window size and default close behavior
        self.set_default_size(800, 600)
        self.set_hide_on_close(True)

        # Create the config manager and load the config file
        self.config_manager = ConfigManager(self)
        self.config_manager.load_config()

        # Create the session manager and load the sessions
        self.session_manager = SessionManager(self)
        self.session_manager.load_sessions()

        # Create the whatsapp manager and initialize the active sessions
        self.whatsapp_manager = WhatsAppSessionManager(self)
        self.whatsapp_manager.initialize()

        # Create TitleBar Widget
        self.window_titlebar_widget = Adw.WindowTitle()
        self.window_titlebar_widget.set_title("Whakarere")
        self.window_titlebar_widget.set_subtitle("Your Gtk4 Whatsapp Client.")

        # Create MainMenu Button Widget
        self.button_settings_menu = MainMenuButtonWidget()

        # Create HeaderBar
        self.headerbar = Adw.HeaderBar()
        self.headerbar.set_title_widget(self.window_titlebar_widget)
        self.headerbar.pack_end(self.button_settings_menu)
        self.add_session_button = Gtk.Button()
        self.add_session_button.set_icon_name("window-new-symbolic")
        self.add_session_button.set_tooltip_text("Create a New Session")
        self.add_session_button.connect("clicked", self.add_new_session)
        self.headerbar.pack_end(self.add_session_button)

        if self.is_dev():
            self.terminate_all_sessions = Gtk.Button()
            self.terminate_all_sessions.set_label("T.A.S.") # Terminate All Sessions
            self.terminate_all_sessions.set_tooltip_text("Terminate All Sessions")
            self.terminate_all_sessions.connect("clicked", self.session_manager.terminate_all_sessions)
            self.headerbar.pack_start(self.terminate_all_sessions)

        #
        self.overlay_spliview = Adw.OverlaySplitView()
        self.overlay_spliview.set_show_sidebar(False)
        self.main_box_content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=20)
        self.main_box_content.set_hexpand(True)
        self.main_box_content.set_vexpand(True)
        image = Gtk.Image.new_from_icon_name("com.mudeprolinux.whakarere")
        image.set_pixel_size(120)
        label_title = Gtk.Label(label="Welcome to Whakarere")
        label_title.set_halign(Gtk.Align.CENTER)
        label_message = Gtk.Label(label="Your Gtk4 WhatsApp client.")
        label_message.set_halign(Gtk.Align.CENTER)
        self.main_box_content.append(image)
        self.main_box_content.append(label_title)
        self.main_box_content.append(label_message)

        self.main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=20)
        self.main_box.set_name("main_box")
        self.main_box.append(self.headerbar)
        self.main_box.append(self.main_box_content)

        self.overlay_spliview.set_content(self.main_box)
        self.set_content(self.overlay_spliview)
             
        # if self.dev:
        #     self.navigation_splitview = Adw.NavigationSplitView()
        #     self.navigation_splitview.set_collapsed(True)
        #     self.navigation_splitview.set_show_content(False)
        #     self.session_manager_page = SessionManagerPage2(self)
        #     self.navigation_splitview.set_content(self.session_manager_page)
        #     self.set_content(self.navigation_splitview)
        # else:
        #     # Create navigation view
        #     self.navigation_view = Adw.NavigationView()
        #     self.session_manager_page = SessionManagerPage(self)
        #     self.navigation_view.push(self.session_manager_page)

        #     # Set the navigation view as the content of the main window
        #     self.set_content(self.navigation_view)
        
    def is_debug(self):
        return self.debug

    def is_dev(self):
        return self.dev

    def add_new_session(self, button):
        #self.window.main_window.set_sensitive(False) # Disable main window 
        new_account_wizard = AccountWizardWindow(self)
        new_account_wizard.present()
        #new_account_wizard.set_visible(True)

    def update_css_for_theme(self):
        print("update_css_for_theme")
        self.settings = Gtk.Settings.get_default()
        theme_name = self.settings.get_property("gtk-theme-name")
        print(theme_name)

        if "dark" in theme_name.lower():
            print("dark")
            css_data = """
                #main_box {
                    background-image: url('/home/tobagin/.config/whakarere/bgs/bg-dark.png');
                    background-repeat: repeat;
                }
            """
        else:
            print("light")
            css_data = """
                #main_box {
                    background-image: url('/home/tobagin/.config/whakarere/bgs/bg-light.png');
                    background-repeat: repeat;
                }
            """

        css_provider = Gtk.CssProvider()
        css_provider.load_from_data(css_data.encode())
        Gtk.StyleContext.add_provider_for_display(
            Gdk.Display.get_default(),
            css_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

    def on_theme_changed(self, settings, pspec):
        print("on_theme_changed")
        self.update_css_for_theme(self)