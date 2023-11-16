import uuid

class SessionManager:
    def __init__(self, app_manager):
        self.app_manager = app_manager
        self.current_session_id = None
        self.session_ids = []
        self.load_sessions()

    def add_session(self, session_id):
        if session_id not in self.session_ids:
            if self.app_manager.whatsapp_manager.check_session_id(session_id):
                self.session_ids.append(session_id)
                self.save_session_ids()
            else:
                self.app_manager.whatsapp_manager.terminate_session(session_id)
                session_id = self.add_session(self.generate_session_id())
                self.app_manager.whatsapp_manager.check_session_id(session_id)
                self.session_ids.append(session_id)
                self.save_session_ids()

    def remove_session(self, session_id):
        if session_id in self.session_ids:
            self.session_ids.remove(session_id)
            self.app_manager.whatsapp_manager.terminate_session(session_id)

    def get_session_ids_size(self):
        return len(self.session_ids)

    def generate_session_id(self):
        return str(uuid.uuid4())

    def get_session(self, session_id):
        return self.session_ids.get(session_id)
    
    def set_current_session(self, session_id):
        self.current_session_id = session_id
    
    def get_current_session(self):
        return self.current_session_id

    def clear_current_session(self):
        self.current_session_id = None

    def get_session_ids(self):
        return self.session_ids
    
    def load_sessions(self):
        self.session_ids = self.app_manager.get_config("session_ids")
        if self.session_ids is None:
            self.session_ids = []
    
    def save_session_ids(self):
        self.app_manager.set_config("session_ids", self.session_ids)
        self.app_manager.save_config()
    
    def get_current_session_user_id(self):
        return self.app_manager.whatsapp_manager.get_user_id(self.current_session_id)

