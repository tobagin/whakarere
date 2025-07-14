"""
About dialog for Karere application.
"""

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Gtk, Adw


def create_about_dialog(parent_window):
    """Create and return a configured AboutDialog."""
    about_dialog = Adw.AboutDialog()
    
    # Set application information
    about_dialog.set_application_name("Karere")
    about_dialog.set_application_icon("io.github.tobagin.karere")
    about_dialog.set_developer_name("Thiago Fernandes")
    about_dialog.set_version("0.1.7")
    about_dialog.set_website("https://github.com/tobagin/karere")
    about_dialog.set_issue_url("https://github.com/tobagin/karere/issues")
    about_dialog.set_support_url("https://github.com/tobagin/karere/discussions")
    about_dialog.set_copyright("© 2023 Thiago Fernandes")
    about_dialog.set_license_type(Gtk.License.GPL_3_0)
    
    about_dialog.set_comments(
        "A modern GTK4 WhatsApp client built with Python, GTK4, and Libadwaita. "
        "Provides a native desktop experience for WhatsApp Web with seamless Linux desktop integration."
    )
    
    # Set credits
    about_dialog.set_developers([
        "Thiago Fernandes https://github.com/tobagin"
    ])
    
    about_dialog.set_designers([
        "Thiago Fernandes"
    ])
    
    about_dialog.set_artists([
        "Thiago Fernandes"
    ])
    
    # Add translator credits if available
    about_dialog.set_translator_credits("translator-credits")
    
    return about_dialog