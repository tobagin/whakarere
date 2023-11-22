import uuid, requests

class SessionManager:
    def __init__(self, window):
        self.window = window
        api_key = "your_global_api_key_here"
        self.api_url = "http://localhost:3000"
        self.headers = { 'x-api-key': api_key }
        self.current_session_id = None
        self.session_ids = []

    def add_session(self, session_id):
        if session_id not in self.session_ids:
            if self.check_session_id(session_id):
                self.session_ids.append(session_id)
                self.save_session_ids()
            else:
                self.terminate_session(session_id)
                session_id = self.add_session(self.generate_session_id())
                self.check_session_id(session_id)
                self.session_ids.append(session_id)
                self.save_session_ids()

    def remove_session(self, session_id):
        if session_id in self.session_ids:
            self.session_ids.remove(session_id)
            self.save_session_ids()
            if not self.check_session_status(session_id):
                self.terminate_session(session_id)

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
        self.session_ids = self.window.config_manager.get_config("session_ids")
        if self.session_ids is None:
            self.session_ids = []
    
    def save_session_ids(self):
        self.window.config_manager.set_config("session_ids", self.session_ids)
        self.window.config_manager.save_config()
    
    def get_current_session_user_id(self):
        return self.window.whatsapp_manager.get_user_id(self.current_session_id)
    
    def check_session_status(self, session_id):
        url = self.api_url + f'/session/status/{session_id}'
        result = requests.get(url, headers=self.headers).json()["success"]

        if(self.window.is_debug()):
            print("check_session_status: " + str(result))
            
        return result 

    def check_session_id(self, session_id):
        url = self.api_url + f'/session/start/{session_id}'
        result = requests.get(url, headers=self.headers).json()["success"]

        if(self.window.is_debug()):
            print("check_session_id: " + str(result))
            
        return result 

    def terminate_session(self, session_id):
        url = self.api_url + f'/session/terminate/{session_id}'
        result = requests.get(url, headers=self.headers).json()["success"]

        if(self.window.is_debug()):
            print("terminate_session: " + str(result))
            
        return result 
    
    def terminate_inactive_sessions(self):
        url = self.api_url + f'/session/terminateInactive'
        result = requests.get(url, headers=self.headers).json()["success"]

        if(self.window.is_debug()):
            print("terminate_inactive_sessions: " + str(result))
            
        return result 

    def terminate_all_sessions(self, test=False):
        url = self.api_url + f'/session/terminateAll'
        result = requests.get(url, headers=self.headers).json()["success"]

        if(self.window.is_debug()):
            print("terminate_inactive_sessions: " + str(result))
            
        return result 

