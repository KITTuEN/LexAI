import os
from cryptography.fernet import Fernet
from dotenv import load_dotenv

load_dotenv()

class EncryptionService:
    def __init__(self):
        key = os.getenv('FERNET_KEY')
        if not key:
            key = Fernet.generate_key().decode()
            print(f"WARNING: FERNET_KEY not found. Generated new key: {key}")
        self.fernet = Fernet(key.encode())

    def encrypt(self, data):
        if not data:
            return None
        return self.fernet.encrypt(data.encode()).decode()

    def decrypt(self, token):
        if not token:
            return None
        return self.fernet.decrypt(token.encode()).decode()

encryption_service = EncryptionService()
