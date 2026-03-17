from datetime import datetime
from bson import ObjectId

class SearchModel:
    def __init__(self, db):
        self.collection = db.searches

    def create_search(self, user_id, query, result):
        search_data = {
            "user_id": ObjectId(user_id),
            "query": query,
            "result_summary": result.get('title', 'Legal Search'),
            "timestamp": datetime.utcnow()
        }
        return self.collection.insert_one(search_data)

    def get_user_searches(self, user_id, limit=20):
        return list(self.collection.find({"user_id": ObjectId(user_id)}).sort("timestamp", -1).limit(limit))
