import os
import json

from whakarere.managers.session import SessionManager
from whakarere.managers.whatsapp import WhatsAppSessionManager
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
        self.whatsapp_sessions_pages = {}
        self.config_file_path = os.path.expanduser("~/.config/whakarere/config.json")
        self.load_config()
        atexit.register(self.save_config)

    def is_debug(self):
        return self.debug

    def is_dev(self):
        return self.dev

    def load_config(self):
        if os.path.exists(self.config_file_path):
            with open(self.config_file_path, "r") as f:
                self.config = json.load(f)
                self.session_manager.load_sessions()
                self.whatsapp_manager.initialize()

    def save_config(self):
        with open(self.config_file_path, "w") as f:
            json.dump(self.config, f)
    
    def set_config(self, key, value):
        self.config[key] = value

    def get_config(self, key):
        return self.config.get(key)

    def navigate_to_qr_manager_page(self, session_id):
        qr_code_page = QrManagerPage(self, session_id)
        self.main_window.navigation_view.push(qr_code_page)

    def add_whatsapp_messenger_page(self, session_id):
        if session_id not in self.whatsapp_sessions_pages:
            self.whatsapp_sessions_pages[session_id] = WhatsappMessengerPage(self, session_id)

    def navigate_to_whatsapp_messenger_page(self, session_id):
        # make it so it checks for for already open session on whatsapp_sessions_pages
        # if it has one and if doesn´t it creates a new one and pushes into the whatsapp_sessions_pages
        if session_id in self.whatsapp_sessions_pages:
            self.main_window.navigation_view.push(self.whatsapp_sessions_pages[session_id])
        else:
            self.add_whatsapp_manager_page(session_id)
            self.main_window.navigation_view.push(self.whatsapp_sessions_pages[session_id])