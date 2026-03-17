from datetime import datetime
from bson import ObjectId

class DocumentModel:
    def __init__(self, db):
        self.collection = db.documents

    def create_document(self, user_id, doc_type, form_data, generated_text):
        document_data = {
            "user_id": ObjectId(user_id),
            "doc_type": doc_type,
            "form_data": form_data,
            "document_text": generated_text,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        return self.collection.insert_one(document_data)

    def get_user_documents(self, user_id):
        return list(self.collection.find({"user_id": ObjectId(user_id)}).sort("updated_at", -1))

    def get_document(self, doc_id):
        return self.collection.find_one({"_id": ObjectId(doc_id)})

    def update_document_text(self, doc_id, text):
        return self.collection.update_one(
            {"_id": ObjectId(doc_id)},
            {
                "$set": {
                    "document_text": text,
                    "updated_at": datetime.utcnow()
                }
            }
        )
