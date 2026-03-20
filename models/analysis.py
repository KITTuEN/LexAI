from datetime import datetime
from bson import ObjectId

class AnalysisModel:
    def __init__(self, db):
        self.collection = db.analysis_history

    def save_analysis(self, user_id, doc_id, file_name, analysis_result):
        data = {
            "user_id": ObjectId(user_id),
            "doc_id": doc_id,
            "file_name": file_name,
            "analysis_result": analysis_result,
            "messages": [], # Store chat history here
            "created_at": datetime.utcnow()
        }
        return self.collection.insert_one(data)

    def add_message(self, doc_id, role, text):
        """Appends a message to the chat history of a document."""
        return self.collection.update_one(
            {"doc_id": doc_id},
            {"$push": {"messages": {
                "role": role,
                "content": text,
                "timestamp": datetime.utcnow()
            }}}
        )

    def get_user_history(self, user_id):
        return list(self.collection.find({"user_id": ObjectId(user_id)}).sort("created_at", -1))

    def get_analysis_by_doc_id(self, doc_id):
        return self.collection.find_one({"doc_id": doc_id})
