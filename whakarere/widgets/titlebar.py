import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gtk

class WindowTitlebarWidget(Gtk.Box):
    def __init__(self):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        self.label_title = Gtk.Label(label="Whakarere")
        self.label_title.add_css_class("title")
        self.label_subtitle = Gtk.Label(label="Available Sessions")
        self.label_subtitle.add_css_class("subtitle")
        self.append(self.label_title)
        self.append(self.label_subtitle)

    def set_title(self, title):
        self.label_title.set_label(title)

    def set_subtitle(self, subtitle):
        self.label_subtitle.set_label(subtitle)