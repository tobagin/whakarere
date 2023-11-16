import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
gi.require_version("GdkPixbuf", "2.0")
gi.require_version("Gdk", "4.0")

from gi.repository import Gdk, GObject

class ChatItem(GObject.Object):
    chat_id = GObject.Property(type=str)
    chat_name = GObject.Property(type=str)
    chat_picture = GObject.Property(type=Gdk.Texture)
    last_message_body = GObject.Property(type=str)
    chat_timestamp = GObject.Property(type=str)
    last_messager_user = GObject.Property(type=str)
    unread_messages = GObject.Property(type=int)
    is_group = GObject.Property(type=bool, default=False)

    def __init__(self, chat_id, chat_name, chat_picture, last_message_body, chat_timestamp, last_messager_user, unread_messages, is_group):
        super().__init__()
        self.chat_id = chat_id
        self.chat_name = chat_name
        self.chat_picture = chat_picture
        self.last_message_body = last_message_body
        self.chat_timestamp = chat_timestamp
        self.last_messager_user = last_messager_user
        self.unread_messages = unread_messages
        self.is_group = is_group