import os
import json

from whakarere.managers.session import SessionManager
from whakarere.managers.whatsapp import WhatsAppSessionManager
from whakarere.pages.qrcode import QrManagerPage
from whakarere.pages.whatsapp import WhatsappMessengerPage
import atexit

class ConfigManager:
    def __init__(self, window):
        self.window = window
        self.config = {}
        self.config_file_path = os.path.expanduser("~/.config/whakarere/config.json")
        atexit.register(self.save_config)

    def load_config(self):
        if os.path.exists(self.config_file_path):
            with open(self.config_file_path, "r") as f:
                self.config = json.load(f)

    def save_config(self):
        with open(self.config_file_path, "w") as f:
            json.dump(self.config, f)
    
    def set_config(self, key, value):
        self.config[key] = value

    def get_config(self, key):
        return self.config.get(key)