from datetime import datetime
from bson import ObjectId

class LawyerChatModel:
    def __init__(self, db):
        self.collection = db.lawyer_chats

    def create_chat(self, user_id, lawyer_id):
        chat = self.collection.find_one({
            "user_id": ObjectId(user_id),
            "lawyer_id": ObjectId(lawyer_id)
        })
        if not chat:
            chat_data = {
                "user_id": ObjectId(user_id),
                "lawyer_id": ObjectId(lawyer_id),
                "messages": [],
                "created_at": datetime.utcnow(),
                "last_message_at": datetime.utcnow()
            }
            res = self.collection.insert_one(chat_data)
            return str(res.inserted_id)
        return str(chat['_id'])

    def add_message(self, chat_id, sender_id, content):
        message = {
            "sender_id": ObjectId(sender_id),
            "content": content,
            "timestamp": datetime.utcnow()
        }
        self.collection.update_one(
            {"_id": ObjectId(chat_id)},
            {
                "$push": {"messages": message},
                "$set": {"last_message_at": datetime.utcnow()}
            }
        )

    def get_chat(self, chat_id):
        return self.collection.find_one({"_id": ObjectId(chat_id)})

    def get_user_chats(self, user_id):
        return list(self.collection.find({"user_id": ObjectId(user_id)}).sort("last_message_at", -1))

    def get_lawyer_chats(self, lawyer_id):
        return list(self.collection.find({"lawyer_id": ObjectId(lawyer_id)}).sort("last_message_at", -1))
