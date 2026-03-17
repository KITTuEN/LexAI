from flask import Blueprint, render_template, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from services.gemini_service import gemini_service
from database import search_model

search_bp = Blueprint('search', __name__)

SEARCH_SYSTEM_PROMPT = """
You are a legal database expert. Provide detailed analysis of the requested IPC/BNS section or legal topic.
You MUST return a JSON array containing ALL relevant sections matching the query.
[
    {
        "section": "Section number (e.g. BNS 303 or IPC 420)",
        "title": "Title of the section",
        "chapter": "Chapter name/number",
        "description": "Detailed description",
        "punishment": "Details of punishment",
        "bailable": "Yes/No",
        "cognizable": "Yes/No",
        "triable_by": "Court type",
        "key_ingredients": ["ingredient 1", "ingredient 2"],
        "landmark_cases": ["case 1", "case 2"],
        "related_sections": ["section 1", "section 2"],
        "common_defenses": ["defense 1", "defense 2"]
    }
]
"""

@search_bp.route('/')
@jwt_required()
def index():
    return render_template('search.html')

@search_bp.route('/query', methods=['POST'])
@jwt_required()
def query():
    q = request.json.get('query', '').lower().strip()
    if not q:
        return jsonify({"error": "Query is required"}), 400
    
    # Check cache first
    cached = search_model.find_cached_result(q)
    if cached and 'result' in cached:
        return jsonify(cached['result'])
        
    # If not cached, fetch from Gemini
    user_id = get_jwt_identity()
    from database import user_model
    from bson import ObjectId
    user = user_model.collection.find_one({"_id": ObjectId(user_id)})
    lang = user.get('preferred_language', 'English')
    
    result = gemini_service.search_section(q, SEARCH_SYSTEM_PROMPT, lang=lang)
    
    # Save search to database for future caching
    search_model.create_search(user_id, q, result)
    
    return jsonify(result)
