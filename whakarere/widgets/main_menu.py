import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gtk, Adw

class MainMenuButtonWidget(Gtk.MenuButton):
    def __init__(self):
        super().__init__()
        # Create MainMenu Button Widget
        self.set_icon_name("open-menu-symbolic")
        self.set_tooltip_text("Main Menu")
        self.set_has_frame(False)
        self.set_direction(Gtk.ArrowType.DOWN)
        self.set_popover(Gtk.Popover())
        self.get_popover().set_position(Gtk.PositionType.BOTTOM)
        self.get_popover().set_has_arrow(True)
        self.get_popover().set_size_request(200, 200)
        self.get_popover().set_child(Gtk.Label(label="Main Menu"))
        
        # About Button
        about_button = Gtk.Button()
        about_button.set_label("About Whakarere")
        about_button.set_has_frame(False)
        about_button.connect("clicked", self.on_about_clicked)
        
        # Keyboard Shortcuts Button
        shortcut_button = Gtk.Button()
        shortcut_button.set_label("Keyboard Shortcuts")
        shortcut_button.set_has_frame(False)
        shortcut_button.connect("clicked", self.on_shortcuts_clicked)
        
        # Preferences Button
        preferences_button = Gtk.Button()
        preferences_button.set_label("Preferences")
        preferences_button.set_has_frame(False)
        preferences_button.connect("clicked", self.on_preferences_clicked)

        settings_menu = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        separetor = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        settings_menu.append(separetor)
        settings_menu.append(preferences_button)
        settings_menu.append(shortcut_button)
        settings_menu.append(about_button)

        self.get_popover().set_child(settings_menu)

    def on_about_clicked(self, button):
        about_window = Adw.AboutWindow(modal=True, transient_for=self)
        about_window.set_application_icon("com.mudeprolinux.whakarere")
        about_window.set_application_name("Whakarere")
        about_window.set_version("0.1.0")
        #about_window.set_comments("A Gtk4 Whatsapp Client.")
        about_window.set_website("https://mudeprolinux.com")
        about_window.set_developer_name("Mude Pro Linux")
        about_window.set_developers(["Thiago Fernandes <tobagin@mudeprolinux.com>"])
        about_window.set_designers(["Thiago Fernandes <tobagin@mudeprolinux.com>"])
        about_window.set_license_type(Gtk.License.MIT_X11)
        about_window.set_copyright("2023 © Mude Pro Linux")
        about_window.set_issue_url("https://github.com/tobagin/whakarere/issues")

        # Show the About window
        about_window.present()
    
    def on_shortcuts_clicked(self, button):
        shortcuts_window = Gtk.ShortcutsWindow(modal=True, transient_for=self)
        shortcuts_section = Gtk.ShortcutsSection()
        shortcuts_group = Gtk.ShortcutsGroup()
        shortcuts_section.add_group(shortcuts_group)
        shortcuts_window.add_session(shortcuts_section)
        copy_shortcut = Gtk.Shortcut.new_from_string("<Ctrl>C", Gtk.Label.new("Copy Selected Text"))
        shortcuts_group.add(copy_shortcut)
        shortcuts_window.show()

    def on_preferences_clicked(self, button):
        pass