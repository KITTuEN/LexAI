from flask import Blueprint, render_template, request, jsonify, redirect, url_for
import math
from flask_jwt_extended import jwt_required, get_jwt_identity
from bson import ObjectId
from database import db, case_model, user_model, search_model
from services.gemini_service import gemini_service

dashboard_bp = Blueprint('dashboard', __name__)

def haversine(lat1, lon1, lat2, lon2):
    R = 6371 # Earth radius in km
    dLat = math.radians(lat2 - lat1)
    dLon = math.radians(lon2 - lon1)
    a = math.sin(dLat/2) * math.sin(dLat/2) + \
        math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * \
        math.sin(dLon/2) * math.sin(dLon/2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    return R * c

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

@dashboard_bp.route('/profile')
@jwt_required()
def profile_view():
    user_id = get_jwt_identity()
    user = user_model.collection.find_one({"_id": ObjectId(user_id)})
    return render_template('profile.html', user=user)

@dashboard_bp.route('/profile/update', methods=['POST'])
@jwt_required()
def profile_update():
    user_id = get_jwt_identity()
    data = {
        'name': request.form.get('name'),
        'phone': request.form.get('phone'),
        'location': request.form.get('location')
    }
    user_model.update_user_profile(user_id, data)
    return redirect(url_for('dashboard.profile_view'))

@dashboard_bp.route('/api/nearby')
@jwt_required()
def nearby_help():
    lat = request.args.get('lat')
    lng = request.args.get('lng')
    
    if lat and lng:
        # Use Gemini to find actual real-world legal landmarks based on coordinates
        real_data = gemini_service.find_nearby_legal_resources(lat, lng)
        if real_data:
            # Calculate precise distance for each landmark
            u_lat = float(lat)
            u_lng = float(lng)
            for item in real_data:
                if 'lat' in item and 'lng' in item:
                    dist = haversine(u_lat, u_lng, item['lat'], item['lng'])
                    item['distance'] = f"{dist:.2f} km"
            return jsonify(real_data)

    # Fallback to simulated data if Gemini fails or coordinates are missing
    mock_data = [
        {"name": "City Core Police Station", "type": "Police Station", "distance": "1.2 km", "status": "Open 24/7", "icon": "fa-shield-alt"},
        {"name": "District High Court", "type": "Court", "distance": "2.5 km", "status": "Closes at 5 PM", "icon": "fa-gavel"},
        {"name": "Central Legal Aid Center", "type": "Legal Aid", "distance": "0.8 km", "status": "Free Support", "icon": "fa-hand-holding-heart"},
        {"name": "Adv. Rajesh Kumar (Expert)", "type": "Verified Lawyer", "distance": "1.5 km", "status": "Available Now", "icon": "fa-user-tie"}
    ]
    return jsonify(mock_data)
