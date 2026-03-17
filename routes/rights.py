from flask import Blueprint, render_template, request, jsonify
from flask_jwt_extended import jwt_required

rights_bp = Blueprint('rights', __name__)

@rights_bp.route('/')
@jwt_required()
def index():
    return render_template('rights.html')

@rights_bp.route('/guide/<topic>')
@jwt_required()
def get_guide(topic):
    user_id = get_jwt_identity()
    from database import user_model
    from bson import ObjectId
    user = user_model.collection.find_one({"_id": ObjectId(user_id)})
    lang = user.get('preferred_language', 'English')
    
    from services.gemini_service import gemini_service
    guide = gemini_service.generate_rights_guide(topic, lang=lang)
    return jsonify(guide)
