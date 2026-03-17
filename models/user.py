from datetime import datetime
import bcrypt
from bson import ObjectId
from services.encryption import encryption_service

class UserModel:
    def __init__(self, db):
        self.collection = db.users

    def create_user(self, name, email, phone, password, role='user', lawyer_data=None):
        password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt(12))
        
        user_data = {
            "name_encrypted": encryption_service.encrypt(name),
            "email_encrypted": encryption_service.encrypt(email),
            "email_hash": bcrypt.hashpw(email.lower().encode('utf-8'), bcrypt.gensalt()).decode(),
            "phone_encrypted": encryption_service.encrypt(phone),
            "password_hash": password_hash.decode('utf-8'),
            "role": role,
            "created_at": datetime.utcnow(),
            "last_login": datetime.utcnow(),
            "location_encrypted": None,
            "cases": []
        }

        if role == 'lawyer' and lawyer_data:
            user_data.update({
                "aadhar_encrypted": encryption_service.encrypt(lawyer_data.get('aadhar')),
                "father_name_encrypted": encryption_service.encrypt(lawyer_data.get('father_name')),
                "mother_name_encrypted": encryption_service.encrypt(lawyer_data.get('mother_name')),
                "lawyer_id_encrypted": encryption_service.encrypt(lawyer_data.get('lawyer_id')),
                "experience_summary": lawyer_data.get('experience_summary', '')
            })

        return self.collection.insert_one(user_data)

    def get_lawyers(self):
        return list(self.collection.find({"role": "lawyer"}))

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

    def update_lawyer_profile(self, user_id, experience_summary):
        return self.collection.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": {"experience_summary": experience_summary}}
        )

    def update_user_profile(self, user_id, data):
        """Update encrypted profile data for a user."""
        update_fields = {}
        
        if 'name' in data:
            update_fields["name_encrypted"] = encryption_service.encrypt(data['name'])
        if 'phone' in data:
            update_fields["phone_encrypted"] = encryption_service.encrypt(data['phone'])
        if 'location' in data:
            update_fields["location_encrypted"] = encryption_service.encrypt(data['location'])
            
        if update_fields:
            return self.collection.update_one(
                {"_id": ObjectId(user_id)},
                {"$set": update_fields}
            )
        return None
