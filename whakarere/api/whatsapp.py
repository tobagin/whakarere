import requests

class WhatsAppAPI:
    def __init__(self, whatsapp_manager):
        self.whatsapp_manager = whatsapp_manager
        api_key = "your_global_api_key_here"
        self.api_url = "http://localhost:3000"
        self.headers = { 'x-api-key': api_key }

    def get_qr_code_data(self, session_id):
        url = self.api_url + f'/session/qr/{session_id}'
        result = ((requests.get(url, headers=self.headers)).json())["qr"]

        if(self.whatsapp_manager.app_manager.is_debug()):
            print("get_qr_code_data: " + str(result))
            
        return result 
    
    def check_session_status(self, session_id):
        url = self.api_url + f'/session/status/{session_id}'
        result = requests.get(url, headers=self.headers).json()["success"]

        if(self.whatsapp_manager.app_manager.is_debug()):
            print("check_session_status: " + str(result))
            
        return result 

    def check_session_id(self, session_id):
        url = self.api_url + f'/session/start/{session_id}'
        result = requests.get(url, headers=self.headers).json()["success"]

        if(self.whatsapp_manager.app_manager.is_debug()):
            print("check_session_id: " + str(result))
            
        return result 
    
    def get_user_profile_picture(self, userid, session_id):
        url = self.api_url + f'/client/getProfilePicUrl/{session_id}'
        try:
            result = requests.post(url, headers=self.headers, json={'contactId': userid}).json()["result"]
        except:
            result = None

        if(self.whatsapp_manager.app_manager.is_debug()):
            print("get_user_profile_picture: " + str(result))
            
        return result 

    def get_user_id(self, session_id):
        url = self.api_url + f'/client/getClassInfo/{session_id}'
        result = requests.get(url, headers=self.headers).json()["sessionInfo"]["wid"]["_serialized"]  # Extract userid

        if(self.whatsapp_manager.app_manager.is_debug()):
            print("get_user_id: " + str(result))
            
        return result 

    def get_user_name(self, session_id):
        url = self.api_url + f'/client/getClassInfo/{session_id}'
        result = requests.get(url, headers=self.headers).json()["sessionInfo"]["pushname"]  # Return pushname

        if(self.whatsapp_manager.app_manager.is_debug()):
            print("get_user_name: " + str(result))
            
        return result 

    def get_chats(self, session_id):
        url = self.api_url + f'/client/getChats/{session_id}'
        result = requests.get(url, headers=self.headers).json()["chats"]

        if(self.whatsapp_manager.app_manager.is_debug()):
            print("get_chats: " + str(result))
            
        return result 
    
    def get_chat_messages(self, chat_id, session_id):
        url = self.api_url + f'/client/getChatMessages/{session_id}'
        result = requests.post(url, headers=self.headers, json={'chatId': chat_id}).json()["messages"]

        if(self.whatsapp_manager.app_manager.is_debug()):
            print("get_chat_messages: " + str(result))
            
        return result 

    def terminate_session(self, session_id):
        url = self.api_url + f'/session/terminate/{session_id}'
        result = requests.get(url, headers=self.headers).json()["success"]

        if(self.whatsapp_manager.app_manager.is_debug()):
            print("terminate_session: " + str(result))
            
        return result 
    
    def terminate_inactive_sessions(self):
        url = self.api_url + f'/session/terminateInactive'
        result = requests.get(url, headers=self.headers).json()["success"]

        if(self.whatsapp_manager.app_manager.is_debug()):
            print("terminate_inactive_sessions: " + str(result))
            
        return result 

    ############################
    # Contact methods
    ############################

    def get_contact_info(self, contact_id, session_id):
        url = self.api_url + f'/contact/getClassInfo/{session_id}'
        result = requests.post(url, headers=self.headers, json={'contactId': contact_id}).json()
        print(result)
        if(self.whatsapp_manager.app_manager.is_debug()):
            print("get_contact_info: " + str(result))
            
        return result