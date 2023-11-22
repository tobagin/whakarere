import gi, threading, time, datetime, requests, qrcode, json, io

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
gi.require_version("GdkPixbuf", "2.0")
gi.require_version("Gdk", "4.0")

from whakarere.pages.new_account import NewAccountFirstPage
from whakarere.pages.qrcode import QrManagerPage
from gi.repository import Adw, Gtk, GdkPixbuf, Gdk, GLib, Gio
from io import BytesIO

class AccountWizardWindow(Adw.Window):
    def __init__(self, window):
        super().__init__()
        self.window = window
        self.set_transient_for(window)
        self.set_modal(True)
        self.set_default_size(300, 300)
        self.connect("close-request", self.on_modal_close_request)
        self.set_decorated(False)
        self.session_id = None

        api_key = "your_global_api_key_here"
        self.api_url = "http://localhost:3000"
        self.headers = { 'x-api-key': api_key }

        self.header_bar = Adw.HeaderBar()
        self.titlebar_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.title = Gtk.Label(label="Creating a Session")
        self.subtitle = Gtk.Label(label="Please wait...")
        self.titlebar_box.append(self.title)
        self.titlebar_box.append(self.subtitle)
        self.header_bar.set_title_widget(self.titlebar_box)

        self.window_content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=20)
        self.window_content.set_size_request(200, 300)

        image = Gtk.Image.new_from_icon_name("com.mudeprolinux.whakarere")
        image.set_pixel_size(120)
        label_title = Gtk.Label(label="Welcome to Whakarere")
        label_title.set_halign(Gtk.Align.CENTER)
        label_message = Gtk.Label(label="Let me create a new session and I'll help you link it to your WhatsApp account.")
        label_message.set_halign(Gtk.Align.CENTER)

        self.progress_bar_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=20)
        self.progress_bar = Gtk.ProgressBar()
        self.progress_bar.set_fraction(0.0)
        self.progress_bar.set_show_text(False)
        self.progress_bar.set_pulse_step(1)

        self.label_progress = Gtk.Label(label="Creating session...")
        self.label_progress.set_halign(Gtk.Align.CENTER)
        self.label_progress.set_margin_top(0)
        self.progress_bar_box.append(self.progress_bar)
        self.progress_bar_box.append(self.label_progress)
        self.progress_bar_box.set_margin_top(40)
        self.progress_bar_box.set_margin_bottom(40)
        self.progress_bar_box.set_margin_start(20)
        self.progress_bar_box.set_margin_end(20)

        self.session_id = self.window.session_manager.generate_session_id()
        self.window.session_manager.add_session(self.session_id)
        thread = threading.Thread(target=self.update_progress_bar)
        thread.start()

        self.top_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=20)
        self.top_box.set_margin_top(20)
        self.top_box.set_halign(Gtk.Align.CENTER)
        self.top_box.set_valign(Gtk.Align.CENTER)
        self.top_box.append(image)
        self.top_box.append(label_title)
        self.top_box.append(label_message)
        self.top_box.set_margin_start(20)
        self.top_box.set_margin_end(20)
        
        self.window_content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=20)
        self.window_content.set_size_request(200, 300)
        self.window_content.append(self.header_bar)
        self.window_content.append(self.top_box)
        self.window_content.append(self.progress_bar_box)
        self.set_content(self.window_content)
        self.present()

    def on_modal_close_request(self, widget):
        self.window.session_manager.remove_session(self.session_id)
        self.destroy()

    def update_progress_bar(self):
        self.label_progress.set_text("Creating session...")
        for i in range(1, 11):
            self.progress_bar.set_fraction(i / 100)
            time.sleep(0.2)
        self.label_progress.set_text("Launching session...")
        for i in range(11, 21):
            self.progress_bar.set_fraction(i / 100)
            time.sleep(0.2)
        self.label_progress.set_text("Waiting for session activation...")
        for i in range(21, 31):
            self.progress_bar.set_fraction(i / 100)
            time.sleep(0.2)
        self.label_progress.set_text("Capturing QR code...")
        for i in range(31, 41):
            self.progress_bar.set_fraction(i / 100)
            time.sleep(0.2)
        self.label_progress.set_text("Generating QR code...")
        for i in range(41, 51):
            self.progress_bar.set_fraction(i / 100)
            time.sleep(0.2)
        
        self.progress_bar.pulse()
        self.label_progress.set_text("Please scan QR code to continue...")
        self.progress_bar.pulse()
        self.qr_code_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=20)
        self.progress_bar.pulse()
        qr_code_data = self.get_qr_code_image(self.session_id)
        self.progress_bar.pulse()
        glib_bytes = GLib.Bytes.new(qr_code_data)
        self.progress_bar.pulse()
        input_stream = Gio.MemoryInputStream.new_from_bytes(glib_bytes)
        self.progress_bar.pulse()
        pixbuf = GdkPixbuf.Pixbuf.new_from_stream(input_stream, None)
        self.progress_bar.pulse()
        self.qr_code_image = Gtk.Image.new_from_pixbuf(pixbuf)
        self.progress_bar.pulse()
        self.qr_code_image.set_pixel_size(240)
        self.progress_bar.pulse()
        self.qr_code_box.append(self.qr_code_image)
        self.progress_bar.pulse()
        self.window_content.remove(self.top_box)
        self.progress_bar.pulse()
        self.window_content.insert_child_after(self.qr_code_box, self.header_bar)
        self.progress_bar.pulse()

        while not self.check_session_status(self.qr_code_image):
            self.progress_bar.pulse()
            time.sleep(1)

        self.progress_bar.set_fraction(0.50)

        self.label_progress.set_text("Syncing your chats...")
        self.window.whatsapp_manager.initialize_session_by_id(self.session_id)
        for i in range(51, 71):
            self.progress_bar.set_fraction(i / 100)
            time.sleep(0.4)

        self.label_progress.set_text("Done!")

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

    def get_qr_code_image(self, session_id):
        url = self.api_url + f'/session/qr/{session_id}/image'
        result = requests.get(url, headers=self.headers).content

        if(self.window.is_debug()):
            print("get_qr_code_image: " + str(result))
            
        return result

    def get_qr_code_data(self, session_id):
        url = self.api_url + f'/session/qr/{session_id}'
        result = ((requests.get(url, headers=self.headers)).json())["qr"]

        if(self.window.is_debug()):
            print("get_qr_code_data: " + str(result))
            
        return result
    
    def check_session_status(self, session_id):
        url = self.api_url + f'/session/status/{session_id}'
        result = requests.get(url, headers=self.headers).json()["success"]

        if(self.window.is_debug()):
            print("check_session_status: " + str(result))
            
        return result