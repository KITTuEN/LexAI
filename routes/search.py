from flask import Blueprint, render_template, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from services.gemini_service import gemini_service
from database import search_model

search_bp = Blueprint('search', __name__)

SEARCH_SYSTEM_PROMPT = """
You are a legal database expert. Provide detailed analysis of the requested IPC/BNS section in JSON format.
Include: section, title, chapter, description, punishment, bailable, cognizable, triable_by, key_ingredients, landmark_cases, related_sections, and common_defenses.
"""

@search_bp.route('/')
@jwt_required()
def index():
    return render_template('search.html')

@search_bp.route('/query', methods=['POST'])
@jwt_required()
def query():
    q = request.json.get('query')
    if not q:
        return jsonify({"error": "Query is required"}), 400
        
    result = gemini_service.search_section(q, SEARCH_SYSTEM_PROMPT)
    
    # Save search to database
    user_id = get_jwt_identity()
    search_model.create_search(user_id, q, result)
    
    return jsonify(result)
