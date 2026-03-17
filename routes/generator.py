from flask import Blueprint, render_template, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from bson import ObjectId
from database import user_model, document_model
from services.gemini_service import gemini_service

generator_bp = Blueprint('generator', __name__)

@generator_bp.route('/')
@jwt_required()
def index():
    user_id = get_jwt_identity()
    saved_docs = document_model.get_user_documents(user_id)
    return render_template('generator.html', saved_docs=saved_docs)

@generator_bp.route('/generate', methods=['POST'])
@jwt_required()
def generate():
    data = request.json
    doc_type = data.get('doc_type')
    form_data = data.get('form_data')
    
    if not doc_type or not form_data:
        return jsonify({"error": "Missing document type or data"}), 400
        
    user_id = get_jwt_identity()
    user = user_model.collection.find_one({"_id": ObjectId(user_id)})
    lang = user.get('preferred_language', 'English')
    
    try:
        text = gemini_service.generate_legal_document(doc_type, form_data, lang=lang)
        # Save to database
        result = document_model.create_document(user_id, doc_type, form_data, text)
        doc_id = str(result.inserted_id)
        return jsonify({"document_text": text, "document_id": doc_id})
    except Exception as e:
        print(f"Error generating document: {e}")
        return jsonify({"error": "Failed to generate document"}), 500

@generator_bp.route('/data/<doc_id>')
@jwt_required()
def get_document_data(doc_id):
    user_id = get_jwt_identity()
    doc = document_model.get_document(doc_id)
    
    if not doc or str(doc['user_id']) != user_id:
        return jsonify({"error": "Access Denied"}), 403
        
    return jsonify({
        "doc_type": doc.get('doc_type'),
        "form_data": doc.get('form_data', {}),
        "document_text": doc.get('document_text', "")
    })

@generator_bp.route('/save_text', methods=['POST'])
@jwt_required()
def save_text():
    data = request.json
    doc_id = data.get('document_id')
    text = data.get('document_text')
    
    if not doc_id or not text:
        return jsonify({"error": "Missing data"}), 400
        
    # Verify ownership before saving
    user_id = get_jwt_identity()
    doc = document_model.get_document(doc_id)
    if not doc or str(doc['user_id']) != user_id:
        return jsonify({"error": "Access Denied"}), 403

    document_model.update_document_text(doc_id, text)
    return jsonify({"status": "Success"})
