import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
gi.require_version("GdkPixbuf", "2.0")
gi.require_version("Gdk", "4.0")

from gi.repository import Gtk, Adw, GdkPixbuf, Gdk, GLib
from whakarere.widgets.main_menu import MainMenuButtonWidget
from whakarere.widgets.titlebar import WindowTitlebarWidget
import threading, time, requests, qrcode
from io import BytesIO

class NewAccountFirstPage(Adw.NavigationPage):
    def __init__(self, app_manager):
        super().__init__()
        self.set_title("Whakarere")
        self.app_manager = app_manager
        self.set_can_pop(True)
        display = Gdk.Display.get_default()
        
        # Get the icon theme for this display
        icon_theme = Gtk.IconTheme.get_for_display(display)
        # Load an icon by name, specify the size
        pixbuf = icon_theme.load_icon("com.mudeprolinux.whakarere", 64, 0) 

        image = Gtk.Image.new_from_pixbuf(pixbuf)
        label = Gtk.Label(label="Welcome to Whakarere")
        label.set_halign(Gtk.Align.CENTER)
        label2 = Gtk.Label(label="This wizard will help you to connect your WhatsApp account a new session on Whakarere.")
        label2.set_halign(Gtk.Align.CENTER)
        label3 = Gtk.Label(label="Please go to the next page to scan the QR code with your phone.")
        label3.set_halign(Gtk.Align.CENTER)
        content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        content.set_size_request(200, 300)
        content.set_halign(Gtk.Align.CENTER)
        content.set_valign(Gtk.Align.CENTER)
        content.append(image)
        content.append(label)
        content.append(label2)
        content.append(label3)
        self.set_child(content)
