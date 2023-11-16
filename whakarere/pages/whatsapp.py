import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
gi.require_version("GdkPixbuf", "2.0")
from whakarere.types.chat import ChatItem
from whakarere.widgets.titlebar import WindowTitlebarWidget
from whakarere.widgets.main_menu import MainMenuButtonWidget
from gi.repository import Gtk, Adw, GLib, Gio, GdkPixbuf, Pango, Gdk, GObject
from datetime import datetime
import base64, requests, threading

class WhatsappMessengerPage(Adw.NavigationPage):
    def __init__(self, app_manager):
        super().__init__()
        self.set_title("Whakarere")
        self.app_manager = app_manager

        # Create TitleBar Widget
        self.window_titlebar_widget = WindowTitlebarWidget()
        self.window_titlebar_widget.set_title("Whakarere")
        self.window_titlebar_widget.set_subtitle(f"Current Session: {self.app_manager.whatsapp_manager.get_user_name(self.app_manager.session_manager.current_session_id)}")
        self.set_can_pop(True)

        # Create Main Menu Button Widget
        self.button_settings_menu = MainMenuButtonWidget()

        # Create HeaderBar
        self.page_headerbar = Adw.HeaderBar()
        self.page_headerbar.set_title_widget(self.window_titlebar_widget)
        self.page_headerbar.pack_end(self.button_settings_menu)

        # Create Chat List 
        self.chat_list = Gio.ListStore(item_type=ChatItem)

        self.check_session_status_thread = threading.Thread(target=self.load_chats,)
        self.check_session_status_thread.start()

        # Factory function for creating list items
        factory = Gtk.SignalListItemFactory.new()
        factory.connect('bind', self.bind_function)

        # Create SingleSelection
        self.selected_item = None
        self.selected_item_position = None
        self.selection_model = Gtk.SingleSelection.new(self.chat_list)
        self.selection_model.connect("selection-changed", self.on_selection_changed)

        self.chat_list.connect("items-changed", self.on_items_changed)

        # Create ListView
        self.list_view = Gtk.ListView.new(self.selection_model, factory)

        # Create ScrolledWindow
        scrolled_window = Gtk.ScrolledWindow()
        scrolled_window.set_vexpand(True)
        scrolled_window.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        scrolled_window.set_child(self.list_view) # Set ListView as child of ScrolledWindow

        # Create Sidebar for SplitView
        self.sidebar = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.sidebar.set_vexpand(True)
        self.sidebar.append(scrolled_window)

        # Create Main Content
        self.content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)

        # Create SplitView
        self.split_view = Adw.OverlaySplitView()
        self.split_view.set_hexpand(True)
        self.split_view.set_vexpand(True)
        self.split_view.set_valign(Gtk.Align.FILL)
        self.split_view.set_halign(Gtk.Align.FILL)
        self.split_view.set_sidebar(self.sidebar)
        self.split_view.set_content(self.content)

        # Create page content
        self.page_content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.page_content.append(self.page_headerbar)
        self.page_content.append(self.split_view)

        # Set page content
        self.set_child(self.page_content)

    def load_chats(self):
        chats = self.app_manager.whatsapp_manager.get_chats(self.app_manager.session_manager.current_session_id)
        for chat in chats:
            print(chat)
            if chat['id']['server'] == 'broadcast':
                continue
            chat_id = chat["id"]["_serialized"]
            chat_name = chat["name"]
            chat_picture = self.app_manager.whatsapp_manager.get_chat_avatar(chat_id)

            if chat['lastMessage']['_data']['type'] == 'chat':
                last_message_body = chat['lastMessage']['_data']['body']
            elif chat['lastMessage']['_data']['type'] == 'call_log' and chat['lastMessage']['_data']['subtype'] == 'miss_video':
                last_message_body = '📵 Missed Video Call'
            elif chat['lastMessage']['_data']['type'] == 'call_log' and chat['lastMessage']['_data']['subtype'] == 'miss_audio':
                last_message_body = '📵 Missed Audio Call'
            elif chat['lastMessage']['_data']['type'] == 'call_log' and chat['lastMessage']['_data']['subtype'] == 'video':
                last_message_body = '📹 Video Call'
            elif chat['lastMessage']['_data']['type'] == 'call_log' and chat['lastMessage']['_data']['subtype'] == 'audio':
                last_message_body = '📞 Audio Call'
            elif chat['lastMessage']['_data']['type'] == 'image':
                last_message_body = '🖼️ Image'
            elif chat['lastMessage']['_data']['type'] == 'document':
                last_message_body = '📄 Document'
            elif chat['lastMessage']['_data']['type'] == 'sticker':
                last_message_body = '🤪 Sticker'
            elif chat['lastMessage']['_data']['type'] == 'ptt':
                last_message_body = '🎤 Voice Message'
            elif chat['lastMessage']['_data']['type'] == 'location':
                last_message_body = '📍 Location'
            elif chat['lastMessage']['_data']['type'] == 'vcard':
                last_message_body = '👤 Contact'
            else:
                last_message_body = '🤔 Unknown Message'

            is_group = chat["isGroup"]

            chat_timestamp = chat["timestamp"]
            if chat['lastMessage']['_data']['hasReaction']:
                if chat['lastMessage']['_data']['id']['fromMe']:
                    last_messager_user = self.app_manager.whatsapp_manager.get_user_name(self.app_manager.session_manager.current_session_id)
                else:
                    last_messager_user = self.app_manager.whatsapp_manager.get_contact_info(chat['lastMessage']['_data']['id']['participant']['_serialized'], self.app_manager.session_manager.current_session_id)
            else:
                if is_group:
                    last_messager_user = self.app_manager.whatsapp_manager.get_contact_info(chat['lastMessage']['_data']['id']['participant']['_serialized'], self.app_manager.session_manager.current_session_id)
                else:
                    if chat['lastMessage']['_data']['id']['fromMe']:
                        last_messager_user = self.app_manager.whatsapp_manager.get_user_name(self.app_manager.session_manager.current_session_id)
                    else:
                        last_messager_user = self.app_manager.whatsapp_manager.get_contact_info(chat['lastMessage']['_data']['id']['_serialized'], self.app_manager.session_manager.current_session_id)
            unread_messages = chat["unreadCount"]
            chat_item = ChatItem(chat_id, chat_name, chat_picture, last_message_body, chat_timestamp, last_messager_user, unread_messages, is_group)
            self.chat_list.append(chat_item)


    def on_items_changed(self, list_store, position, removed, added):
        # Update Chat window
        # print("items changed redo list_view")
        pass

    def on_selection_changed(self, selection_model, positon, n_items):
        # Updating selection
        self.selected_item_position = selection_model.get_selected()
        self.selected_item = selection_model.get_selected_item()
        
        # Update Chat Window
        # print("new item selected, update chat window")
        pass

    def bind_function(self, factory, list_item):
        model = list_item.get_item()
        hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        avatar = Adw.Avatar()
        avatar.set_size(50)
        avatar.set_margin_start(5)
        avatar.set_halign(Gtk.Align.START)
        avatar.set_custom_image(model.chat_picture)
        hbox.append(avatar)
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        vbox.set_halign(Gtk.Align.START)
        vbox.set_valign(Gtk.Align.CENTER)
        vbox.set_hexpand(True)
        label_name = Gtk.Label()
        label_name.set_use_markup(True)

        # Escape any markup-sensitive characters
        escaped_name = GLib.markup_escape_text(model.chat_name[:20])

        # Set label text with markup for font size
        label_name.set_markup("<span font='9'><b>" + escaped_name + "</b></span>")
        
        label_name.set_halign(Gtk.Align.START)
        label_name.set_valign(Gtk.Align.CENTER)
        label_name.set_hexpand(True)
        label_name.set_vexpand(True)
        label_last_message = Gtk.Label()

        # Escape any markup-sensitive characters
        escaped_last = GLib.markup_escape_text(model.last_message_body[:50])

        # Set label text with markup for font size
        label_last_message.set_markup("<span font='8'>" + escaped_last + "</span>")

        label_last_message.set_use_markup(True)
        label_last_message.set_halign(Gtk.Align.START)
        label_last_message.set_valign(Gtk.Align.CENTER)
        label_last_message.set_hexpand(True)
        label_last_message.set_vexpand(True)

        # Set label properties for wrapping and font size
        label_last_message.set_wrap(True)
        label_last_message.set_wrap_mode(Pango.WrapMode.WORD_CHAR)
        label_last_message.set_lines(2)
        label_last_message.set_max_width_chars(50)  # Adjust the value as needed

        vbox.append(label_name)
        vbox.append(label_last_message)
        hbox.append(vbox)
        vbox_end = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        vbox_end.set_halign(Gtk.Align.END)
        vbox_end.set_valign(Gtk.Align.CENTER)

        now = datetime.now()
        timestamp = datetime.fromtimestamp(int(model.chat_timestamp))
        time_difference = now - timestamp
        days = time_difference.days
        hours = time_difference.seconds // 3600
        minutes = (time_difference.seconds // 60) % 60
        seconds = time_difference.seconds % 60
        label_timestamp = Gtk.Label()
        label_timestamp.set_use_markup(True)

        if days > 0:
            escaped_timestamp = timestamp.strftime('%d')
        else:
            escaped_timestamp = timestamp.strftime('%H:%M')

        # Set label text with markup for font size
        label_timestamp.set_markup("<span font='6'>" + escaped_timestamp + "</span>")

        label_timestamp.set_halign(Gtk.Align.END)
        label_timestamp.set_valign(Gtk.Align.CENTER)
        label_timestamp.set_margin_top(5)
        label_timestamp.set_margin_end(10)
        label_timestamp.set_hexpand(True)
        label_timestamp.set_vexpand(True)
        chat_menu = Gtk.MenuButton()
        chat_menu.set_icon_name("go-down-symbolic")
        chat_menu.set_halign(Gtk.Align.END)
        chat_menu.set_valign(Gtk.Align.CENTER)
        chat_menu.set_has_frame(False)
        chat_menu.set_direction(Gtk.ArrowType.DOWN)
        chat_menu.set_popover(Gtk.Popover())
        chat_menu.get_popover().set_position(Gtk.PositionType.BOTTOM)
        chat_menu.get_popover().set_has_arrow(True)
        chat_menu.get_popover().set_size_request(200, 200)
        chat_menu.get_popover().set_child(Gtk.Label(label="Archive Chat"))
        vbox_end.append(label_timestamp)
        vbox_end.append(chat_menu)
        hbox.append(vbox_end)
        list_item.set_child(hbox)

