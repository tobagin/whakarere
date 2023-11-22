import gi
import base64

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
gi.require_version("GdkPixbuf", "2.0")
gi.require_version("Gdk", "4.0")

from gi.repository import Gtk, Adw, GdkPixbuf, Gdk, GLib
from whakarere.widgets.main_menu import MainMenuButtonWidget
from whakarere.widgets.titlebar import WindowTitlebarWidget
from whakarere.images.whatsapp_logo import WhatsappLogo
import threading, time, requests, qrcode, json, datetime
from io import BytesIO

class SessionSync(Adw.NavigationPage):
    def __init__(self, aww, app_manager):
        super().__init__()
        self.set_title("Whakarere")
        self.aww = aww
        self.app_manager = app_manager
        self.set_can_pop(True)

        image_data = base64.b64decode(WhatsappLogo.base64image)
        input_stream = io.BytesIO(image_data)
        pixbuf = GdkPixbuf.Pixbuf.new_from_stream(input_stream, None)
        image = Gtk.Image.new_from_pixbuf(pixbuf)
        image.set_pixel_size(120)
        label = Gtk.Label(label="Syncing with WhatsApp")
        label.set_halign(Gtk.Align.CENTER)
        label2 = Gtk.Label(label="Please wait...")
        label2.set_halign(Gtk.Align.CENTER)
        self.label3 = Gtk.Label(label="Loading chats...")
        self.label3.set_margin_top(-20)
        self.label3.set_halign(Gtk.Align.CENTER)
        self.progress_bar = Gtk.ProgressBar()
        self.progress_bar.set_fraction(0.0)
        self.progress_bar.set_show_text(False)
        self.session_id = self.app_manager.session_manager.generate_session_id()
        self.app_manager.session_manager.add_session(self.session_id)
        thread = threading.Thread(target=self.update_progress_bar)
        thread.start()
        content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=20)
        content.set_margin_top(20)
        content.set_size_request(200, 300)
        content.set_halign(Gtk.Align.CENTER)
        content.set_valign(Gtk.Align.CENTER)
        content.append(image)
        content.append(label)
        content.append(label2)
        content.append(self.progress_bar)
        content.append(self.label3)

        self.set_child(content)

    def update_progress_bar(self):
        self.label3.set_text("Creating session...")
        for i in range(1, 25):
            self.progress_bar.set_fraction(i / 100)
            time.sleep(0.1)
        self.label3.set_text("Launching session...")
        for i in range(26, 50):
            self.progress_bar.set_fraction(i / 100)
            time.sleep(0.1)
        self.label3.set_text("Waiting for session activation...")
        for i in range(51, 75):
            self.progress_bar.set_fraction(i / 100)
            time.sleep(0.1)
        self.label3.set_text("Capturing Qr code...")
        for i in range(76, 101):
            self.progress_bar.set_fraction(i / 100)
            time.sleep(0.1)
        self.label3.set_text("Done! Please go to the next page to scan the QR code with your phone.")
        self.aww.session_id = self.session_id
        self.aww.next_button.set_sensitive(True)