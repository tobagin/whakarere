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

class QrManagerPage(Adw.NavigationPage):
    def __init__(self, aww, app_manager, session_id):
        super().__init__()
        self.set_title("Whakarere")
        api_key = "your_global_api_key_here"
        self.api_url = "http://localhost:3000"
        self.headers = { 'x-api-key': api_key }
        self.aww = aww
        self.app_manager = app_manager
        self.session_id = session_id
        print(f"QrManagerPage Session ID: {self.session_id}")

        # Create QR Code Image
        self.qr_code_texture = self.get_qr_code_texture(self.get_qr_code_data(session_id))
        self.qr_code = Gtk.Picture()
        self.qr_code.set_paintable(self.qr_code_texture)
        
        # Create ScrolledWindow
        scrolled_window = Gtk.ScrolledWindow()
        scrolled_window.set_min_content_width(300)
        scrolled_window.set_min_content_height(300)
        scrolled_window.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        scrolled_window.set_child(self.qr_code) 
        
        self.qr_code_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.qr_code_box.set_halign(Gtk.Align.CENTER)
        self.qr_code_box.set_valign(Gtk.Align.CENTER)
        self.qr_code_box.set_margin_top(10)
        self.qr_code_box.set_margin_bottom(10)
        self.qr_code_box.set_margin_start(10)
        self.qr_code_box.set_margin_end(10)
        self.qr_code_box.set_hexpand(True)
        self.qr_code_box.set_vexpand(True)  
        self.qr_code_box.append(scrolled_window)

        self.set_child(self.qr_code_box)

        self.check_session_status_thread = threading.Thread(target=self.check_session_status_thread, args=(self.session_id,))
        self.check_session_status_thread.start()

    def generate_qr_code(self, qr_code_data):
        qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=10, border=4)
        qr.add_data(qr_code_data)
        qr.make(fit=True)
        return qr.make_image(fill_color="black", back_color="white")

    def get_qr_code_texture(self, qr_code_data):
        qr_image = self.generate_qr_code(qr_code_data)
        pixbuf = self.pil_image_to_pixbuf(qr_image)
        return Gdk.Texture.new_for_pixbuf(pixbuf)

    def pil_image_to_pixbuf(self, pil_image):
        """Convert a PIL image to a GdkPixbuf."""
        buffer = BytesIO()
        pil_image.save(buffer)
        glib_bytes = GLib.Bytes.new(buffer.getvalue())
        loader = GdkPixbuf.PixbufLoader.new_with_type("png")
        loader.write_bytes(glib_bytes)
        pixbuf = loader.get_pixbuf()
        loader.close()
        return pixbuf

    def get_qr_code_data(self, session_id):
        url = self.api_url + f'/session/qr/{session_id}'
        result = ((requests.get(url, headers=self.headers)).json())["qr"]

        if(self.app_manager.is_debug()):
            print("get_qr_code_data: " + str(result))
            
        return result
    
    def check_session_status(self, session_id):
        url = self.api_url + f'/session/status/{session_id}'
        result = requests.get(url, headers=self.headers).json()["success"]

        if(self.app_manager.is_debug()):
            print("check_session_status: " + str(result))
            
        return result
    
    def check_session_status_thread(self, session_id):
        while not self.check_session_status(session_id):
            time.sleep(2)
        self.aww.next_button.show()