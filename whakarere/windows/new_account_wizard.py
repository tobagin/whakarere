import gi

gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from whakarere.managers.app import AppManager
from whakarere.pages.new_account import NewAccountFirstPage
from gi.repository import Adw, Gtk

class AccountWizardWindow(Adw.Window):
    def __init__(self, app_manager):
        super().__init__()
        self.app_manager = app_manager
        #self.set_transient_for(app_manager.main_window)
        #self.set_default_size(400, 300)
        self.set_decorated(False)  # Optional: for an undecorated window
        #self.set_keep_above(True)

        header_bar = Adw.HeaderBar()
        headerbar_title = Gtk.Label(label="Add New Account")
        header_bar.set_title_widget(headerbar_title)
        previous_button_content = Adw.ButtonContent()
        previous_button_content.set_icon_name("go-previous-symbolic")
        #previous_button_content.set_label("Previous")
        previous_button = Gtk.Button()
        previous_button.set_child(previous_button_content)
        next_button_content = Adw.ButtonContent()
        next_button_content.set_icon_name("go-next-symbolic")
        #next_button_content.set_label("Next")

        next_button = Gtk.Button()
        next_button.set_child(next_button_content)
        bottom_bar = Adw.HeaderBar()
        bottom_bar.set_show_end_title_buttons(False)
        bottom_bar.set_show_title(False)
        bottom_bar.pack_start(previous_button)
        bottom_bar.pack_end(next_button)

        self.navigationview = Adw.NavigationView()
        page = NewAccountFirstPage(self.app_manager)
        self.navigationview.push(page)

        content = Adw.ToolbarView()
        content.add_top_bar(header_bar)
        content.add_bottom_bar(bottom_bar)
        content.set_size_request(200, 300)
        content.set_content(self.navigationview)

        self.set_content(content)
        self.connect("close-request", self.on_wizard_close)
        self.present()

    def on_wizard_close(self, window):
        self.app_manager.main_window.set_sensitive(True)