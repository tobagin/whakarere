import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
gi.require_version("GdkPixbuf", "2.0")
import base64, requests
from whakarere.widgets.titlebar import WindowTitlebarWidget
from whakarere.widgets.main_menu import MainMenuButtonWidget
from whakarere.types.account import AccountItem
from whakarere.images.whatsapp_logo_alt import WhatsappLogoAlt
from gi.repository import Gtk, Gdk, Gio, Adw, GdkPixbuf, GLib

class SessionManagerPage(Adw.NavigationPage):
    def __init__(self, app_manager):
        super().__init__()
        self.set_title("Whakarere")
        self.app_manager = app_manager
        self.set_can_pop(True)

        # Create TitleBar Widget
        self.window_titlebar_widget = WindowTitlebarWidget()

        # Create MainMenu Button Widget
        self.button_settings_menu = MainMenuButtonWidget()

        # Create HeaderBar
        self.page_headerbar = Adw.HeaderBar()
        self.page_headerbar.set_title_widget(self.window_titlebar_widget)
        self.page_headerbar.pack_end(self.button_settings_menu)

        if self.app_manager.is_dev():
            self.terminate_all_sessions = Gtk.Button()
            self.terminate_all_sessions.set_label("T.A.S.") # Terminate All Sessions
            self.terminate_all_sessions.connect("clicked", self.app_manager.whatsapp_manager.terminate_all_sessions)
            self.page_headerbar.pack_end(self.terminate_all_sessions)

        # Create Account List
        self.account_list = Gio.ListStore(item_type=AccountItem)
        for session_id in self.app_manager.session_manager.get_session_ids():
            account = AccountItem(session_id)
            self.account_list.append(account)

        # Factory function for creating list items
        factory = Gtk.SignalListItemFactory.new()
        factory.connect('bind', self.bind_function)

        # Create SingleSelection
        self.selected_item = None
        self.selected_item_position = None
        self.selection_model = Gtk.SingleSelection.new(self.account_list)
        self.selection_model.connect("selection-changed", self.on_selection_changed)

        self.account_list.connect("items-changed", self.on_items_changed)

        # Create ListView
        self.list_view = Gtk.ListView.new(self.selection_model, factory)

        # Create ScrolledWindow
        scrolled_window = Gtk.ScrolledWindow()
        scrolled_window.set_min_content_width(300)
        scrolled_window.set_min_content_height(300)
        scrolled_window.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        scrolled_window.set_child(self.list_view) # Set ListView as child of ScrolledWindow

        # Add session button
        self.button_add_session = Gtk.Button()
        self.button_add_session.icon_name = Gio.ThemedIcon(name="com.mudeprolinux.whakarere-add-session-symbolic.svg")
        button_add_session_content = Adw.ButtonContent()
        button_add_session_content.set_icon_name("com.mudeprolinux.whakarere-add-session-symbolic")
        button_add_session_content.add_css_class("svg-icon")
        button_add_session_content.set_label("Add Session")
        self.button_add_session.set_child(button_add_session_content)
        self.button_add_session.connect("clicked", self.add_new_session)

        # Remove session button
        self.button_remove_session = Gtk.Button()
        button_remove_session_content = Adw.ButtonContent()
        button_remove_session_content.set_icon_name("com.mudeprolinux.whakarere-remove-session-symbolic")
        button_remove_session_content.add_css_class("svg-icon")
        button_remove_session_content.set_label("Remove Session")
        self.button_remove_session.set_child(button_remove_session_content)
        self.button_remove_session.connect("clicked", self.remove_selected_session)

        # Launch session button
        self.button_launch_session = Gtk.Button()
        self.button_launch_session.set_hexpand(True)
        self.button_launch_session.set_halign(Gtk.Align.CENTER)
        button_launch_session_content = Adw.ButtonContent()
        button_launch_session_content.set_icon_name("com.mudeprolinux.whakarere-launch-session-symbolic")
        button_launch_session_content.add_css_class("svg-icon")
        button_launch_session_content.set_label("Launch Session")
        self.button_launch_session.set_child(button_launch_session_content)
        self.button_launch_session.connect("clicked", self.launch_selected_session)

        # Activate session button
        self.button_activate_session = Gtk.Button()
        self.button_activate_session.set_hexpand(True)
        self.button_activate_session.set_halign(Gtk.Align.CENTER)
        button_activate_session_content = Adw.ButtonContent()
        button_activate_session_content.set_icon_name("com.mudeprolinux.whakarere-qr-code-symbolic")
        button_activate_session_content.add_css_class("svg-icon")
        button_activate_session_content.set_label("Scan QR")
        self.button_activate_session.set_child(button_activate_session_content)
        self.button_activate_session.connect("clicked", self.activate_selected_session)

        page_label = Gtk.Label(label="<b>Create a New Session.</b>")
        page_label.set_use_markup(True)
        page_label.set_halign(Gtk.Align.CENTER)
        page_label.set_valign(Gtk.Align.CENTER)

        # Create content box for list view
        content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        content_box.set_valign(Gtk.Align.CENTER)  # Vertical alignment to center
        content_box.set_halign(Gtk.Align.CENTER)  # Horizontal alignment to center
        content_box.set_margin_top(10)
        content_box.set_margin_bottom(10)
        content_box.set_margin_start(10)
        content_box.set_margin_end(10)
        content_box.set_hexpand(True)
        content_box.set_vexpand(True)
        content_box.append(scrolled_window)
        #content_box.append(self.action_bar)

        # a button bar for the bottom of the page
        button_bar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        button_bar.set_halign(Gtk.Align.CENTER)
        button_bar.set_hexpand(True)
        button_bar.append(self.button_add_session)
        button_bar.append(self.button_launch_session)
        button_bar.append(self.button_activate_session)
        button_bar.append(self.button_remove_session)
        if self.app_manager.session_manager.get_session_ids_size() > 0:
            self.on_selection_changed(self.selection_model, None, None)
            if self.app_manager.whatsapp_manager.check_session_status(self.selected_item.session_id):
                self.button_launch_session.set_visible(True)
                self.button_activate_session.set_visible(False)
            else:
                self.button_launch_session.set_visible(False)
                self.button_activate_session.set_visible(True)
        else:
            self.button_launch_session.set_visible(False)
            self.button_activate_session.set_visible(False)

        bottom_bar = Adw.HeaderBar()
        bottom_bar.set_title_widget(button_bar)
        bottom_bar.set_show_back_button(False)
        bottom_bar.set_show_end_title_buttons(False)
        bottom_bar.set_show_start_title_buttons(False)

        # Create page content
        self.page_content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.page_content.append(self.page_headerbar)
        self.page_content.append(content_box)
        self.page_content.append(bottom_bar)

        # Set page content
        self.set_child(self.page_content)
    
    def refresh_listview(self):
        # Update or refresh the data in the list store (modify as needed)
        self.account_list.remove_all()
        for session_id in self.app_manager.session_manager.get_session_ids():
            account = AccountItem(session_id)
            self.account_list.append(account)

        self.selection_model = Gtk.SingleSelection.new(self.account_list)
        # Notify the list view to refresh
        self.list_view.set_model(self.selection_model)

    def on_items_changed(self, list_store, position, removed, added):
        if not removed and self.app_manager.session_manager.get_session_ids_size() > 0:
            self.on_selection_changed(self.selection_model, None, None)
            if self.app_manager.whatsapp_manager.check_session_status(self.selected_item.session_id):
                self.button_launch_session.set_visible(True)
                self.button_activate_session.set_visible(False)
            else:
                self.button_launch_session.set_visible(False)
                self.button_activate_session.set_visible(True)
        else:
            self.button_launch_session.set_visible(False)
            self.button_activate_session.set_visible(False)

    def on_selection_changed(self, selection_model, positon, n_items):
        self.selected_item_position = selection_model.get_selected()
        self.selected_item = selection_model.get_selected_item()
        if self.selected_item is not None:
            if self.app_manager.whatsapp_manager.check_session_status(self.selected_item.session_id):
                self.button_launch_session.set_visible(True)
                self.button_activate_session.set_visible(False)
            else:
                self.button_launch_session.set_visible(False)
                self.button_activate_session.set_visible(True)

    def add_new_session(self, button):
        session_id = self.app_manager.session_manager.generate_session_id()
        self.app_manager.session_manager.add_session(session_id)
        self.account_list.append(AccountItem(session_id))

    def remove_selected_session(self, button):
        # Create a new message dialog
        dialog = Adw.MessageDialog(modal=True, transient_for=self.app_manager.main_window)
        dialog.set_heading("Delete Session")
        dialog.set_body("Are you sure you want to delete the session?")

        dialog.add_response("cancel", "_Cancel")
        dialog.add_response("delete", "_Delete")

        dialog.set_response_appearance("delete", Adw.ResponseAppearance.DESTRUCTIVE)
        
        dialog.set_default_response("cancel")
        dialog.set_close_response("cancel")

        dialog.connect("response", self.on_response)

        #self.add_overlay(dialog)
        dialog.set_visible(True)
    
    def on_response(self, dialog, response):
        if response == "delete":
            self.account_list.remove(self.selected_item_position)
            self.app_manager.session_manager.remove_session(self.selected_item.session_id)
            self.app_manager.whatsapp_manager.terminate_session(self.selected_item.session_id)
            self.on_selection_changed(self.selection_model, None, None)
        elif response == "cancel":
            pass
        dialog.destroy()

    def launch_selected_session(self, button):
        if self.selected_item is not None:
            self.app_manager.session_manager.set_current_session(self.selected_item.session_id)
            self.app_manager.navigate_to_whatsapp_messenger_page(self.selected_item.session_id)
        
    def activate_selected_session(self, button):
        if self.selected_item is not None:
            self.app_manager.session_manager.set_current_session(self.selected_item.session_id)
            self.app_manager.navigate_to_qr_manager_page(self.selected_item.session_id)

    def bind_function(self, factory, list_item):
        model = list_item.get_item()
        result = self.account_list.find(model)
        position = result.position
        if model is not None:
            is_session_active = self.app_manager.whatsapp_manager.check_session_status(model.session_id)
            if is_session_active:
                hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
                hbox.set_halign(Gtk.Align.CENTER)
                avatar = Adw.Avatar()
                avatar.set_size(40)
                avatar.set_margin_top(5)
                avatar.set_margin_bottom(5)
                avatar.set_margin_start(5)
                avatar.set_halign(Gtk.Align.START)
                userid = self.app_manager.whatsapp_manager.get_user_id(model.session_id)
                response = requests.get(self.app_manager.whatsapp_manager.get_user_profile_picture(userid, model.session_id))
                response.raise_for_status()
                loader = GdkPixbuf.PixbufLoader()
                loader.write(response.content)
                loader.close()
                avatar_image = Gdk.Texture.new_for_pixbuf(loader.get_pixbuf())
                avatar.set_custom_image(avatar_image)
                hbox.append(avatar)
                label = Gtk.Label(label=f"<b>{self.app_manager.whatsapp_manager.get_user_name(model.session_id)}</b>")
                label.set_use_markup(True)
                hbox.append(label)
                list_item.set_child(hbox)
            else:
                hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
                hbox.set_halign(Gtk.Align.CENTER)
                avatar = Adw.Avatar()
                avatar.set_size(40)
                avatar.set_margin_top(5)
                avatar.set_margin_bottom(5)
                avatar.set_margin_start(5)
                image_data = base64.b64decode(WhatsappLogoAlt.base64image)
                gbytes = GLib.Bytes.new_take(image_data)
                input_stream = Gio.MemoryInputStream.new_from_bytes(gbytes)
                pixbuf = GdkPixbuf.Pixbuf.new_from_stream(input_stream, None)
                texture = Gdk.Texture.new_for_pixbuf(pixbuf)
                avatar.set_custom_image(texture)
                hbox.append(avatar)
                label = Gtk.Label(label="<b>No account linked.</b>")
                label.set_use_markup(True)
                hbox.append(label)
                list_item.set_child(hbox)