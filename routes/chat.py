from flask import Blueprint, render_template, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from bson import ObjectId
from database import db, case_model
from services.gemini_service import gemini_service

chat_bp = Blueprint('chat', __name__)

SYSTEM_CHAT_PROMPT = """
You are LexAI, an expert Indian legal advisor. 
The user has provided this initial situation summary: "{situation_summary}"

Your role is to:
1. Acknowledge the situation and ask SMART, FOCUSED follow-up questions.
2. Ask ONLY ONE question at a time to keep the conversation manageable.
3. Your goal is to gather: who is involved, chronology of events, evidence available, and legal roles.
4. After 4-6 questions, if you have enough info, tell the user they can now click "Analyze My Case" for a full report.
5. Base all advice on current Indian law (BNS 2023 / IPC).
"""

@chat_bp.route('/<case_id>/chat')
@jwt_required()
def view(case_id):
    user_id = get_jwt_identity()
    case = case_model.get_case(case_id)
    if not case or str(case['user_id']) != user_id:
        return "Access Denied", 403
    return render_template('chat.html', case=case)

@chat_bp.route('/<case_id>/message', methods=['POST'])
@jwt_required()
def send_message(case_id):
    user_id = get_jwt_identity()
    case = case_model.get_case(case_id)
    if not case or str(case['user_id']) != user_id:
        return jsonify({"error": "Access Denied"}), 403

    message = request.json.get('message')
    case_model.add_message(case_id, 'user', message)
    
    # Get response from Gemini
    updated_case = case_model.get_case(case_id)
    chat_history = updated_case['chat_history']
    
    # Inject situation summary into prompt
    custom_prompt = SYSTEM_CHAT_PROMPT.format(situation_summary=case['situation_summary'])
    
    try:
        ai_response = gemini_service.get_chat_response(chat_history, custom_prompt)
        case_model.add_message(case_id, 'ai', ai_response)
        case_model.update_status(case_id, 'In Progress')
        return jsonify({"response": ai_response})
    except Exception as e:
        print(f"Chat Error: {e}")
        return jsonify({"response": "I'm sorry, I'm having trouble connecting to my legal brain right now. Please try again in a moment."}), 500

@chat_bp.route('/<case_id>/analyze', methods=['POST'])
@jwt_required()
def analyze(case_id):
    user_id = get_jwt_identity()
    case = case_model.get_case(case_id)
    if not case or str(case['user_id']) != user_id:
        return jsonify({"error": "Access Denied"}), 403

    analysis_prompt = """
    Analyze the case fully based on Indian Law. 
    Use BNS 2023 as primary with IPC references.
    Provide result in the requested JSON format.
    """
    
    analysis = gemini_service.analyze_case(case['situation_summary'], case['chat_history'], analysis_prompt)
    case_model.save_analysis(case_id, analysis)
    
    return jsonify(analysis)
