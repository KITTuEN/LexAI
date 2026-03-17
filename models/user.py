from datetime import datetime
import bcrypt
from services.encryption import encryption_service

class UserModel:
    def __init__(self, db):
        self.collection = db.users

    def create_user(self, name, email, phone, password):
        password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt(12))
        
        user_data = {
            "name_encrypted": encryption_service.encrypt(name),
            "email_encrypted": encryption_service.encrypt(email),
            "email_hash": bcrypt.hashpw(email.lower().encode('utf-8'), bcrypt.gensalt()).decode(), # For indexing/lookup
            "phone_encrypted": encryption_service.encrypt(phone),
            "password_hash": password_hash.decode('utf-8'),
            "created_at": datetime.utcnow(),
            "last_login": datetime.utcnow(),
            "cases": []
        }
        return self.collection.insert_one(user_data)

    def find_by_email(self, email):
        # Since email is encrypted, we need a way to look it up.
        # We can use a deterministic hash of the email for lookups.
        # For simplicity in this demo, we'll fetch all and check, 
        # but in production, use a hash.
        users = self.collection.find()
        for user in users:
            decrypted_email = encryption_service.decrypt(user['email_encrypted'])
            if decrypted_email and decrypted_email.lower() == email.lower():
                return user
        return None

    def verify_password(self, password, password_hash):
        return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))
