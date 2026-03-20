from flask import Blueprint, render_template, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from services.gemini_service import gemini_service
from database import search_model

search_bp = Blueprint('search', __name__)

SEARCH_SYSTEM_PROMPT = """
You are NyayaVyavasth, the ultimate Indian Legal Intelligence. Your goal is 99%+ technical accuracy.

CRITICAL LEGAL LOGIC:
1. CLASSIFICATION RULE: 
   - IF a section is a DEFINITION (e.g. IPC 340, 378) or a GENERAL RULE / PRINCIPLE (e.g. IPC 34, BNS 3(5)):
     Set "bailable": "Not applicable", "cognizable": "Not applicable", "punishment": "None (Definition Section)".
   - ELSE (if it's a Punishment Section like IPC 341, 379): Apply exact status.
2. SPECIFIC ACCURACY:
   - IPC 341 (Wrongful Restraint): BAILABLE, NON-COGNIZABLE.
   - IPC 343 (Confinement >= 3 days): BAILABLE, NON-COGNIZABLE.
   - IPC 379 (Theft): NON-BAILABLE, COGNIZABLE.
3. WORDING: 
   - IPC 340 is "Wrongful restraint within circumscribing limits".
   - Article 51A is a "Non-justiciable Fundamental Duty".
4. BNS: IPC case laws remain persuasive for BNS equivalents.

[
    {
        "section": "Number",
        "title": "Title",
        "nature": "Criminal Offense / Definition / General Rule / Constitutional",
        "description": "Precise legal definition",
        "punishment": "Duration or 'None (Definition)'",
        "bailable": "Yes / No / Not applicable",
        "cognizable": "Yes / No / Not applicable",
        "triable_by": "Court or 'N/A'",
        "key_ingredients": ["Requirement 1"],
        "landmark_cases": ["Case (Year)"],
        "related_sections": ["Related"]
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
    
    from services.rag_service import rag_service
    result = rag_service.search_legal_sections(q, SEARCH_SYSTEM_PROMPT, lang=lang)
    
    # Save search to database for future caching
    search_model.create_search(user_id, q, result)
    
    return jsonify(result)
