from flask import Blueprint, render_template, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from bson import ObjectId
from database import case_model, user_model
from services.gemini_service import gemini_service

complaint_bp = Blueprint('complaint', __name__)

COMPLAINT_SYSTEM_PROMPT = """
Generate a formal police complaint in the standard Indian format for submission to a police station. 
Use formal legal language. Include: To (SP/SHO), Subject line, complainant details, accused details, 
chronological incident description, applicable IPC/BNS sections with brief justification, evidence list, 
prayer/relief sought, date and place.

IMPORTANT: For details that are not provided (like Complainant's Name, S/o, Address, etc.), do NOT use placeholders 
like "[Your Full Name]" or "[Your Address]". Instead, leave a clear blank line (e.g., "__________") so I can fill it in manually.
"""

@complaint_bp.route('/')
@jwt_required()
def index():
    user_id = get_jwt_identity()
    cases = case_model.get_user_cases(user_id)
    case_id = request.args.get('case_id')
    return render_template('complaint_form.html', cases=cases, initial_case_id=case_id)

@complaint_bp.route('/generate', methods=['POST'])
@jwt_required()
def generate():
    data = request.json
    case_id = data.get('case_id')
    
    # Save complaint details if a case is selected
    if case_id:
        complaint_details = {
            "accused_name": data.get('accused_name'),
            "incident_date": data.get('incident_date'),
            "location": data.get('location'),
            "description": data.get('description')
        }
        case_model.save_complaint(case_id, complaint_details)
        
    # Get language
    user_id = get_jwt_identity()
    user = user_model.collection.find_one({"_id": ObjectId(user_id)})
    lang = user.get('preferred_language', 'English')
    
    text = gemini_service.generate_complaint(data, COMPLAINT_SYSTEM_PROMPT, lang=lang)
    
    # Also save the generated text as the initial 'final' text
    if case_id:
        case_model.save_complaint_text(case_id, text)
        
    return jsonify({"complaint_text": text})

@complaint_bp.route('/save_text', methods=['POST'])
@jwt_required()
def save_text():
    data = request.json
    case_id = data.get('case_id')
    text = data.get('complaint_text')
    
    if not case_id or not text:
        return jsonify({"error": "Missing data"}), 400
        
    case_model.save_complaint_text(case_id, text)
    return jsonify({"status": "Success"})

@complaint_bp.route('/data/<case_id>')
@jwt_required()
def get_complaint_data(case_id):
    user_id = get_jwt_identity()
    case = case_model.get_case(case_id)
    if not case or str(case['user_id']) != user_id:
        return jsonify({"error": "Access Denied"}), 403
    
    return jsonify({
        "details": case.get('complaint_data', {}),
        "final_text": case.get('final_complaint_text', "")
    })
