import base64
from flask import Blueprint, render_template, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from bson import ObjectId
from database import user_model
from services.gemini_service import gemini_service

ocr_bp = Blueprint('ocr', __name__)

SYSTEM_OCR_PROMPT = """
You are a World-Class Legal Document Analyst. 
Your goal is to help common people understand complex legal documents like Contracts, Policies, and Notices.
Identify risks, benefits, and hidden traps in Indian legal contexts.
Be objective, authoritative, and prioritize the user's protection.
ALWAYS warn that this is AI-generated and not a substitute for a registered Advocate.
"""

@ocr_bp.route('/')
@jwt_required()
def index():
    return render_template('ocr.html')

@ocr_bp.route('/analyze', methods=['POST'])
@jwt_required()
def analyze():
    if 'file' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No file selected"}), 400
    
    try:
        image_data = file.read()
        image_b64 = base64.b64encode(image_data).decode('utf-8')
        mime_type = file.mimetype
        
        # Get language
        user_id = get_jwt_identity()
        user = user_model.collection.find_one({"_id": ObjectId(user_id)})
        lang = user.get('preferred_language', 'English')
        
        analysis = gemini_service.analyze_document(image_b64, mime_type, SYSTEM_OCR_PROMPT, lang=lang)
        return jsonify({"analysis": analysis})
    except Exception as e:
        print(f"OCR Error: {e}")
        return jsonify({"error": str(e)}), 500
