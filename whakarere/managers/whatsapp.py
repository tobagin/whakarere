import gi, sqlite3, os, threading, requests, base64
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
gi.require_version("GdkPixbuf", "2.0")
gi.require_version("Gdk", "4.0")
from gi.repository import Gdk, GdkPixbuf, Gio, GLib
from whakarere.images.unknown_contact import UnknownContact
from whakarere.pages.whatsapp import WhatsappMessengerPage

class WhatsAppSessionManager:
    def __init__(self, window):
        self.window = window
        api_key = "your_global_api_key_here"
        self.api_url = "http://localhost:3000"
        self.headers = { 'x-api-key': api_key }
        self.whatsapp_messenger_pages = {}
        self.chats = {}  # Changed to a dictionary to map session IDs to chats
        self.chats_avatar = {}  # Presumably for future functionality
        self.databases = {}  # Changed to a dictionary to map session IDs to databases
        self.chat_messages = {}  # Presumably for future functionality
        self.number = 0

    def load_or_create_databases(self):
        db_directory = os.path.expanduser("~/.config/whakarere/dbs")

        # Ensure the database directory exists
        if not os.path.exists(db_directory):
            os.makedirs(db_directory)

        for session_id in self.window.session_manager.session_ids:
            db_file = f"{session_id}.db"
            db_path = os.path.join(db_directory, db_file)

            # Connect to the SQLite database
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            # Store the connection in the dictionary
            self.databases[session_id] = conn

            # Close the cursor
            cursor.close()

    def initialize(self):
        sessions_thread = threading.Thread(target=self.initialize_sessions)
        sessions_thread.start()

    def initialize_sessions(self):
        for session in self.window.session_manager.session_ids:
            if self.window.session_manager.check_session_status(session):
                result = self.get_chats(session)  # Fixed assignment
                self.chats[session] = result  # Store chats indexed by session ID
                for chat in result:
                    chat_id = chat["id"]["_serialized"]
                    if chat["isGroup"]:
                        print(chat_id)
                        try:
                            self.chat_messages[chat_id] = self.chat_fetch_messages(chat_id, session)
                        except:        
                            trimmed_chat_id = chat_id[-15:]
                            print(trimmed_chat_id)
                            self.chats[trimmed_chat_id] = self.chat_fetch_messages(trimmed_chat_id, session)
                    else:
                        self.chat_messages[chat_id] = self.chat_fetch_messages(chat_id, session)
                    self.chats_avatar[chat_id] = self.get_user_profile_picture(chat_id, session)
                self.window.whatsapp_manager.add_whatsapp_messenger_page(session)

    def initialize_session_by_id(self, session_id):
        if self.window.session_manager.check_session_status(session_id):
            result = self.get_chats(session_id)  # Fixed assignment
            self.chats[session_id] = result  # Store chats indexed by session ID
            for chat in result:
                chat_id = chat["id"]["_serialized"]
                if chat["isGroup"]:
                    print(chat_id)
                    try:
                        self.chat_messages[chat_id] = self.chat_fetch_messages(chat_id, session_id)
                    except:        
                        trimmed_chat_id = chat_id[-15:]
                        print(trimmed_chat_id)
                        self.chats[trimmed_chat_id] = self.chat_fetch_messages(trimmed_chat_id, session_id)
                else:
                    self.chat_messages[chat_id] = self.chat_fetch_messages(chat_id, session_id)
                self.chats_avatar[chat_id] = self.get_user_profile_picture(chat_id, session_id)
            if session_id not in self.whatsapp_sessions_pages:
                self.whatsapp_sessions_pages[session_id] = WhatsappMessengerPage(self, session_id)

    def navigate_to_whatsapp_messenger_page(self, session_id):
        # make it so it checks for for already open session on whatsapp_sessions_pages
        # if it has one and if doesn´t it creates a new one and pushes into the whatsapp_sessions_pages
        if session_id in self.whatsapp_sessions_pages:
            self.main_window.navigation_view.push(self.whatsapp_sessions_pages[session_id])
        else:
            self.add_whatsapp_messenger_page(session_id)
            self.main_window.navigation_view.push(self.whatsapp_sessions_pages[session_id])

    ############################
    # Chat methods
    ############################

    def get_chats(self, session_id):
        url = self.api_url + f'/client/getChats/{session_id}'
        result = requests.get(url, headers=self.headers).json()["chats"]

        if(self.window.is_debug()):
            print("get_chats: " + str(result))
            
        return result 
    
    def chat_fetch_messages(self, chat_id, session_id):
        url = self.api_url + f'/chat/fetchMessages/{session_id}'
        result = requests.post(url, headers=self.headers, json={'chatId': chat_id})
        if(self.number == 3):
            print(result)

        json = result.json()

        if(self.window.is_debug()):
            print("get_chat_messages: " + str(result))

        if(self.number == 3):
            print(json)    
            self.number += 1
        
        return result 

    def get_chats_by_id(self, session_id):
        return self.chats.get(session_id, [])

    def get_chat_avatar(self, chat_id):
        url = self.chats_avatar.get(chat_id, None)
        if url is not None:
            response = requests.get(url)
            loader = GdkPixbuf.PixbufLoader()
            loader.write(response.content)
            loader.close()
            return Gdk.Texture.new_for_pixbuf(loader.get_pixbuf())
        else:
            binary_data = base64.b64decode(UnknownContact.base64image)
            gbytes = GLib.Bytes.new(binary_data)
            input_stream = Gio.MemoryInputStream.new_from_bytes(gbytes)
            pixbuf = GdkPixbuf.Pixbuf.new_from_stream(input_stream, None)
            return Gdk.Texture.new_for_pixbuf(pixbuf)
   
    def get_user_profile_picture(self, userid, session_id):
        url = self.api_url + f'/client/getProfilePicUrl/{session_id}'
        try:
            result = requests.post(url, headers=self.headers, json={'contactId': userid}).json()["result"]
        except:
            result = None

        if(self.window.is_debug()):
            print("get_user_profile_picture: " + str(result))
            
        return result 

    def get_user_id(self, session_id):
        url = self.api_url + f'/client/getClassInfo/{session_id}'
        result = requests.get(url, headers=self.headers).json()["sessionInfo"]["wid"]["_serialized"]  # Extract userid

        if(self.window.is_debug()):
            print("get_user_id: " + str(result))
            
        return result 

    def get_user_name(self, session_id):
        url = self.api_url + f'/client/getClassInfo/{session_id}'
        result = requests.get(url, headers=self.headers).json()["sessionInfo"]["pushname"]  # Return pushname

        if(self.window.is_debug()):
            print("get_user_name: " + str(result))
            
        return result 

    ############################
    # Contact methods
    ############################

    def get_contact_info(self, contact_id, session_id):
        url = self.api_url + f'/contact/getClassInfo/{session_id}'
        result = requests.post(url, headers=self.headers, json={'contactId': contact_id}).json()
        print(result)
        if(self.window.is_debug()):
            print("get_contact_info: " + str(result))
            
        return result