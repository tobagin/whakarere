import os
import json

from whakarere.api.whatsapp import WhatsAppAPI
from whakarere.managers.session import SessionManager
from whakarere.managers.whatsapp import WhatsAppSessionManager
from whakarere.managers.qrcode import QRCodeManager
from whakarere.pages.qrcode import QrManagerPage
from whakarere.pages.whatsapp import WhatsappMessengerPage
import atexit

class AppManager:
    def __init__(self, main_window, debug=False, dev=False):
        self.debug = debug
        self.dev = dev
        self.config = {}
        self.main_window = main_window
        self.whatsapp_manager = WhatsAppSessionManager(self)
        self.session_manager = SessionManager(self)
        self.qrcode_manager = QRCodeManager(self)
        self.config_file_path = os.path.expanduser("~/.config/whakarere/config.json")
        self.load_config()
        atexit.register(self.save_config)

    def is_debug(self):
        return self.debug

    def is_dev(self):
        return self.dev

    def create_config_file(self):
        if not os.path.exists(self.config_file_path):
            os.makedirs(os.path.dirname(self.config_file_path), exist_ok=True)
            with open(self.config_file_path, "w") as f:
                json.dump({}, f)
            self.config = self.load_config()

    def load_config(self):
        if os.path.exists(self.config_file_path):
            with open(self.config_file_path, "r") as f:
                self.config = json.load(f)
                self.session_manager.load_sessions()
                self.whatsapp_manager.initialize()
        else:
            self.create_config_file()

    def save_config(self):
        with open(self.config_file_path, "w") as f:
            json.dump(self.config, f)
    
    def set_config(self, key, value):
        self.config[key] = value

    def get_config(self, key):
        return self.config.get(key)

    def navigate_to_qr_manager_page(self):
        self.qrcode_page = QrManagerPage(self)
        self.main_window.navigation_view.push(self.qrcode_page)

    def navigate_to_whatsapp_messenger_page(self):
        self.whatsapp_page = WhatsappMessengerPage(self)
        self.main_window.navigation_view.push(self.whatsapp_page)