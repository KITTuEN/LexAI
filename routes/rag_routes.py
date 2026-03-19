from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from services.pinecone_service import pinecone_service
from services.document_service import document_service
from services.rag_service import rag_service
from services.translations import translate
from models.user import UserModel
from database import user_model
from bson import ObjectId

rag_bp = Blueprint('rag', __name__)

@rag_bp.route('/upload-case', methods=['POST'])
@jwt_required()
def upload_case():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    
    file = request.files['file']
    case_id = request.form.get('case_id')
    
    if file.filename == '' or not case_id:
        return jsonify({"error": "No selected file or case_id"}), 400

    try:
        content = file.read()
        result = document_service.process_and_ingest(content, file.filename, case_id)
        return jsonify({
            "message": "Case document processed and ingested successfully",
            "details": result
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@rag_bp.route('/semantic-search', methods=['POST'])
@jwt_required()
def semantic_search():
    data = request.get_json()
    query = data.get('query')
    case_id = data.get('case_id') # Optional filtering
    
    if not query:
        return jsonify({"error": "Query is required"}), 400

    try:
        matches = pinecone_service.query_case(query, case_id=case_id)
        results = []
        for m in matches:
            results.append({
                "score": m.score,
                "text": m.metadata['text'],
                "source": m.metadata['source'],
                "case_id": m.metadata['case_id']
            })
        return jsonify({"results": results}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@rag_bp.route('/generate-brief', methods=['POST'])
@jwt_required()
def generate_brief():
    data = request.get_json()
    case_id = data.get('case_id')
    
    if not case_id:
        return jsonify({"error": "case_id is required"}), 400

    try:
        identity = get_jwt_identity()
        user = user_model.collection.find_one({"_id": ObjectId(identity)})
        lang = user.get('preferred_language', 'English')
        
        brief = rag_service.generate_case_brief(case_id, lang=lang)
        return jsonify(brief), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@rag_bp.route('/chat-with-case', methods=['POST'])
@jwt_required()
def chat_with_case():
    data = request.get_json()
    case_id = data.get('case_id')
    question = data.get('question')
    
    if not case_id or not question:
        return jsonify({"error": "case_id and question are required"}), 400

    try:
        identity = get_jwt_identity()
        user = user_model.collection.find_one({"_id": ObjectId(identity)})
        lang = user.get('preferred_language', 'English')
        
        answer = rag_service.get_grounded_answer(question, case_id=case_id, lang=lang)
        return jsonify({"answer": answer}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@rag_bp.route('/extract-citations', methods=['POST'])
@jwt_required()
def extract_citations():
    data = request.get_json()
    case_id = data.get('case_id')
    text = data.get('text')
    
    if not case_id and not text:
        return jsonify({"error": "Either case_id or text is required"}), 400

    try:
        citations = rag_service.extract_citations(text=text, case_id=case_id)
        return jsonify({"citations": citations}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@rag_bp.route('/opposing-argument', methods=['POST'])
@jwt_required()
def opposing_argument():
    data = request.get_json()
    user_claim = data.get('claim')
    case_id = data.get('case_id')
    
    if not user_claim:
        return jsonify({"error": "claim is required"}), 400

    try:
        identity = get_jwt_identity()
        user = user_model.collection.find_one({"_id": ObjectId(identity)})
        lang = user.get('preferred_language', 'English')
        
        counter_argument = rag_service.generate_opposing_argument(user_claim, case_id=case_id, lang=lang)
        return jsonify({"counter_argument": counter_argument}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
