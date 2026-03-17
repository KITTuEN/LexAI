from flask import Blueprint, render_template, request, jsonify, redirect, url_for
from flask_jwt_extended import jwt_required, get_jwt_identity
from bson import ObjectId
from database import db, case_model, user_model, search_model
from services.gemini_service import gemini_service

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/home')
@jwt_required()
def member_home():
    user_id = get_jwt_identity()
    user = user_model.collection.find_one({"_id": ObjectId(user_id)})
    return render_template('member_home.html', user=user)

@dashboard_bp.route('/')
@jwt_required()
def dashboard_view():
    user_id = get_jwt_identity()
    user = user_model.collection.find_one({"_id": ObjectId(user_id)})
    
    if user.get('role') == 'lawyer':
        from database import lawyer_chat_model
        chats = lawyer_chat_model.get_lawyer_chats(user_id)
        
        # Stats for lawyer
        total_consultations = len(chats)
        
        return render_template('lawyer_dashboard.html', 
                                user=user,
                                chats=chats,
                                total_consultations=total_consultations)

    cases = case_model.get_user_cases(user_id) # Fetches all, sorted by date
    searches = search_model.get_user_searches(user_id)
    
    # Stats for citizen
    total_cases = len(cases)
    cases_in_progress = len([c for c in cases if c['status'] == 'In Progress'])
    cases_analyzed = len([c for c in cases if c['status'] == 'Analyzed'])
    total_searches = len(searches)
    
    # Legal tip
    tip_prompt = "Generate a short, helpful legal tip of the day for an Indian citizen."
    try:
        legal_tip = gemini_service.model.generate_content(tip_prompt).text
    except:
        legal_tip = "Always consult a registered advocate before signing important documents."

    return render_template('dashboard.html', 
                            cases=cases, 
                            searches=searches,
                            total_cases=total_cases,
                            cases_in_progress=cases_in_progress,
                            cases_analyzed=cases_analyzed,
                            total_searches=total_searches,
                            legal_tip=legal_tip)
