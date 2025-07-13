#!/usr/bin/env python3

import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Gtk, Adw, GLib
import sys

print("DEBUG: Starting minimal GTK test")

class TestApp(Adw.Application):
    def __init__(self):
        print("DEBUG: TestApp.__init__")
        super().__init__(application_id="test.gtk.app")
        
    def do_activate(self):
        print("DEBUG: TestApp.do_activate")
        window = Adw.ApplicationWindow(application=self)
        window.set_default_size(400, 300)
        window.set_title("Test Window")
        
        # Create a simple box with a label
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        box.set_spacing(10)
        box.set_margin_top(20)
        box.set_margin_bottom(20)
        box.set_margin_start(20)
        box.set_margin_end(20)
        
        label = Gtk.Label(label="Hello, GTK4!")
        label.set_markup("<big><b>Hello, GTK4!</b></big>")
        box.append(label)
        
        button = Gtk.Button(label="Click Me")
        button.connect("clicked", self.on_button_clicked)
        box.append(button)
        
        window.set_content(box)
        print("DEBUG: About to present window")
        window.present()
        print("DEBUG: Window presented")
        
    def on_button_clicked(self, button):
        print("DEBUG: Button clicked!")

if __name__ == "__main__":
    print("DEBUG: Creating app")
    app = TestApp()
    print("DEBUG: Running app")
    exit_code = app.run(sys.argv)
    print(f"DEBUG: App exited with code: {exit_code}")
    sys.exit(exit_code)