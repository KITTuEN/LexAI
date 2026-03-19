from datetime import datetime
from bson import ObjectId

class CaseModel:
    def __init__(self, db):
        self.collection = db.cases

    def create_case(self, user_id, title, situation_summary):
        case_data = {
            "user_id": ObjectId(user_id),
            "title": title,
            "situation_summary": situation_summary,
            "status": "New", # [New | In Progress | Analyzed | Closed]
            "chat_history": [
                {
                    "role": "ai",
                    "content": "Hello! I am NyayaVyavasth. I've received your situation summary. Let's discuss this further so I can provide a detailed analysis. What exactly happens when...",
                    "timestamp": datetime.utcnow()
                }
            ],
            "analysis_result": {},
            "tags": [],
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        return self.collection.insert_one(case_data)

    def get_user_cases(self, user_id):
        return list(self.collection.find({"user_id": ObjectId(user_id)}).sort("updated_at", -1))

    def get_case(self, case_id):
        return self.collection.find_one({"_id": ObjectId(case_id)})

    def add_message(self, case_id, role, content):
        message = {
            "role": role, # 'user' or 'ai'
            "content": content,
            "timestamp": datetime.utcnow()
        }
        return self.collection.update_one(
            {"_id": ObjectId(case_id)},
            {
                "$push": {"chat_history": message},
                "$set": {"updated_at": datetime.utcnow()}
            }
        )

    def update_status(self, case_id, status):
        return self.collection.update_one(
            {"_id": ObjectId(case_id)},
            {"$set": {"status": status, "updated_at": datetime.utcnow()}}
        )

    def save_analysis(self, case_id, analysis):
        return self.collection.update_one(
            {"_id": ObjectId(case_id)},
            {
                "$set": {
                    "analysis_result": analysis,
                    "status": "Analyzed",
                    "updated_at": datetime.utcnow()
                }
            }
        )

    def save_complaint(self, case_id, complaint_data):
        return self.collection.update_one(
            {"_id": ObjectId(case_id)},
            {
                "$set": {
                    "complaint_data": complaint_data,
                    "updated_at": datetime.utcnow()
                }
            }
        )

    def save_complaint_text(self, case_id, text):
        return self.collection.update_one(
            {"_id": ObjectId(case_id)},
            {
                "$set": {
                    "final_complaint_text": text,
                    "updated_at": datetime.utcnow()
                }
            }
        )
