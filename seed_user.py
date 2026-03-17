from database import db, user_model
from bson import ObjectId

def seed():
    # Credentials
    name = "Test User"
    email = "test@lexai.com"
    phone = "9876543210"
    password = "Password123!"

    print(f"Creating user: {email}...")
    
    # Check if exists
    existing = user_model.find_by_email(email)
    if existing:
        print("User already exists!")
        return

    user_id = user_model.create_user(name, email, phone, password).inserted_id
    print(f"Successfully created user with ID: {user_id}")
    print("\n--- Sample Credentials ---")
    print(f"Email: {email}")
    print(f"Password: {password}")

if __name__ == "__main__":
    seed()
