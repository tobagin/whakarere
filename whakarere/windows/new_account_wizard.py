import gi

gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from whakarere.managers.app import AppManager
from whakarere.pages.new_account import NewAccountFirstPage
from whakarere.pages.qrcode import QrManagerPage
from gi.repository import Adw, Gtk

class AccountWizardWindow(Adw.Window):
    def __init__(self, app_manager):
        super().__init__()
        self.app_manager = app_manager
        #self.set_transient_for(app_manager.main_window)
        self.set_decorated(False)
        self.session_id = None

        self.header_bar = Adw.HeaderBar()
        self.titlebar_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.title = Gtk.Label(label="Creating a Session")
        self.subtitle = Gtk.Label(label="Please wait...")
        self.titlebar_box.append(self.title)
        self.titlebar_box.append(self.subtitle)
        self.header_bar.set_title_widget(self.titlebar_box)

        self.previous_button_content = Adw.ButtonContent()
        self.previous_button_content.set_icon_name("go-previous-symbolic")
        self.previous_button = Gtk.Button()
        self.previous_button.set_child(self.previous_button_content)
        self.previous_button.hide()

        self.next_button_content = Adw.ButtonContent()
        self.next_button_content.set_icon_name("go-next-symbolic")
        self.next_button = Gtk.Button()
        self.next_button.set_child(self.next_button_content)
        self.next_button.set_sensitive(False)
        self.next_button.connect("clicked", self.move_to_qrcode_page)

        self.bottom_bar = Adw.HeaderBar()
        self.bottom_bar.set_show_end_title_buttons(False)
        self.bottom_bar.set_show_title(False)
        self.bottom_bar.pack_start(self.previous_button)
        self.bottom_bar.pack_end(self.next_button)

        self.navigationview = Adw.NavigationView()
        page = NewAccountFirstPage(self, self.app_manager)
        self.navigationview.push(page)

        self.content = Adw.ToolbarView()
        self.content.add_top_bar(self.header_bar)
        self.content.add_bottom_bar(self.bottom_bar)
        self.content.set_size_request(200, 300)
        self.content.set_content(self.navigationview)

        self.set_content(self.content)
        self.present()
    
    def move_to_qrcode_page(self, button):
        qrcode_page = QrManagerPage(self, self.app_manager, self.session_id)
        self.navigationview.push(qrcode_page)
        self.subtitle.set_text("Scan the QR Code with your phone")
        self.next_button.set_sensitive(False)