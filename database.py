import os
from pymongo import MongoClient
from dotenv import load_dotenv
from models.user import UserModel
from models.case import CaseModel
from models.search import SearchModel
from models.lawyer_chat import LawyerChatModel
from models.document import DocumentModel
from models.analysis import AnalysisModel

load_dotenv()

MONGO_URI = os.getenv('MONGO_URI', 'mongodb://localhost:27017/lexai')
client = MongoClient(MONGO_URI)
db = client.get_default_database()

# Model instances
user_model = UserModel(db)
case_model = CaseModel(db)
search_model = SearchModel(db)
lawyer_chat_model = LawyerChatModel(db)
document_model = DocumentModel(db)
analysis_model = AnalysisModel(db)
