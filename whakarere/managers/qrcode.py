import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
gi.require_version("GdkPixbuf", "2.0")
gi.require_version("Gdk", "4.0")

import qrcode
from gi.repository import Gdk, GdkPixbuf, GLib
from io import BytesIO

class QRCodeManager:
    def __init__(self, app_manager):
        self.app_manager = app_manager
    
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
        pil_image.save(buffer, format="PNG")
        glib_bytes = GLib.Bytes.new(buffer.getvalue())
        loader = GdkPixbuf.PixbufLoader.new_with_type("png")
        loader.write_bytes(glib_bytes)
        pixbuf = loader.get_pixbuf()
        loader.close()
        return pixbuf
        
