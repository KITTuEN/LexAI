from flask import Blueprint, render_template, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from bson import ObjectId
from datetime import datetime
from database import user_model, analysis_model
from services.gemini_service import gemini_service
import uuid
import base64
from services.document_service import document_service
from services.rag_service import rag_service

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
        file_content = file.read()
        file_name = file.filename
        doc_id = str(uuid.uuid4())
        
        # Get language
        user_id = get_jwt_identity()
        user = user_model.collection.find_one({"_id": ObjectId(user_id)})
        lang = user.get('preferred_language', 'English')
        
        if file.mimetype.startswith('image/'):
            # OCR with Gemini
            extracted_text = gemini_service.extract_text_from_media(file_content, file.mimetype)
            document_service.process_and_ingest(extracted_text.encode('utf-8'), file_name, doc_id)
        else:
            document_service.process_and_ingest(file_content, file_name, doc_id)
        
        # 2. Analyze using RAG
        analysis = rag_service.analyze_document_with_rag(doc_id, lang=lang)
        
        # 3. Save to History (MongoDB)
        analysis_model.save_analysis(user_id, doc_id, file_name, analysis)
        
        return jsonify({"analysis": analysis, "doc_id": doc_id})
    except Exception as e:
        print(f"OCR RAG Error: {e}")
        return jsonify({"error": str(e)}), 500

@ocr_bp.route('/chat', methods=['POST'])
@jwt_required()
def ocr_chat():
    data = request.get_json()
    doc_id = data.get('doc_id')
    question = data.get('question')
    
    if not doc_id or not question:
        return jsonify({"error": "doc_id and question are required"}), 400
    
    try:
        print(f"DEBUG: OCR Chat Request for doc_id={doc_id}, question={question[:30]}...")
        # Get language
        user_id = get_jwt_identity()
        user = user_model.collection.find_one({"_id": ObjectId(user_id)})
        lang = user.get('preferred_language', 'English')
        
        print(f"DEBUG: Using language={lang}")
        answer = rag_service.get_grounded_answer(question, doc_id=doc_id, lang=lang)
        print(f"DEBUG: AI Answer generated ({len(answer)} chars)")
        
        # Save to Chat History
        analysis_model.add_message(doc_id, "user", question)
        analysis_model.add_message(doc_id, "ai", answer)
        
        return jsonify({"answer": answer})
    except Exception as e:
        print(f"OCR Chat Error: {e}")
        return jsonify({"error": str(e)}), 500

@ocr_bp.route('/history', methods=['GET'])
@jwt_required()
def get_ocr_history():
    try:
        user_id = get_jwt_identity()
        history = analysis_model.get_user_history(user_id)
        # Convert ObjectId and datetime for JSON
        for h in history:
            h['_id'] = str(h['_id'])
            h['user_id'] = str(h['user_id'])
            h['created_at'] = h['created_at'].isoformat()
            
            # Handle stringified analysis_result (fallback for old data)
            if isinstance(h.get('analysis_result'), str):
                try:
                    # Replace single quotes with double quotes for valid JSON if needed
                    res_str = h['analysis_result'].replace("'", '"')
                    h['analysis_result'] = json.loads(res_str)
                except:
                    pass
            
            # Handle stringified messages (fallback for old data)
            if isinstance(h.get('messages'), str):
                try:
                    msg_str = h['messages'].replace("'", '"').replace("datetime.datetime", "")
                    # This is very rough, but it's a fallback
                    h['messages'] = json.loads(msg_str)
                except:
                    h['messages'] = []

            if 'messages' in h and isinstance(h['messages'], list):
                for m in h['messages']:
                    if isinstance(m.get('timestamp'), datetime):
                        m['timestamp'] = m['timestamp'].isoformat()
        return jsonify(history)
    except Exception as e:
        print(f"History Error: {e}")
        return jsonify({"error": str(e)}), 500

@ocr_bp.route('/history/<doc_id>', methods=['GET'])
@jwt_required()
def get_ocr_detail(doc_id):
    try:
        item = analysis_model.get_analysis_by_doc_id(doc_id)
        if not item:
            return jsonify({"error": "Analysis not found"}), 404
        
        item['_id'] = str(item['_id'])
        item['user_id'] = str(item['user_id'])
        item['created_at'] = item['created_at'].isoformat()
        
        # Handle stringified analysis_result (fallback for old data)
        if isinstance(item.get('analysis_result'), str):
            try:
                res_str = item['analysis_result'].replace("'", '"')
                item['analysis_result'] = json.loads(res_str)
            except:
                pass

        if 'messages' in item:
            for m in item['messages']:
                if isinstance(m.get('timestamp'), datetime):
                    m['timestamp'] = m['timestamp'].isoformat()
        return jsonify(item)
    except Exception as e:
        print(f"Detail Error: {e}")
        return jsonify({"error": str(e)}), 500
