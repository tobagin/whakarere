import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import GObject

class AccountItem(GObject.Object):
    session_id = GObject.Property(type=str)

    def __init__(self, session_id):
        super().__init__()
        self.session_id = session_id