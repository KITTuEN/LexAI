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
    
    lang = user.get('preferred_language', 'English')
    
    # Legal tip
    tip_prompt = f"Generate a short, helpful legal tip of the day for an Indian citizen. RESPOND ONLY IN {lang}."
    try:
        legal_tip = gemini_service.model.generate_content(tip_prompt).text
    except:
        legal_tip = "Always consult a registered advocate before signing important documents." if lang == 'English' else "महत्वपूर्ण दस्तावेजों पर हस्ताक्षर करने से पहले हमेशा एक पंजीकृत अधिवक्ता से परामर्श लें।"

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
        'location': request.form.get('location'),
        'preferred_language': request.form.get('preferred_language', 'English')
    }
    user_model.update_user_profile(user_id, data)
    return redirect(url_for('dashboard.profile_view'))

@dashboard_bp.route('/api/nearby')
@jwt_required()
def nearby_help():
    user_id = get_jwt_identity()
    user = user_model.collection.find_one({"_id": ObjectId(user_id)})
    lang = user.get('preferred_language', 'English')
    
    lat = request.args.get('lat')
    lng = request.args.get('lng')
    query = request.args.get('query')
    
    # Resolve Coordinates
    resolved_lat = float(lat) if lat and lat != 'null' else None
    resolved_lng = float(lng) if lng and lng != 'null' else None
    display_name = query if query else (f"{resolved_lat:.4f}, {resolved_lng:.4f}" if resolved_lat else "Local Zone")

    # If we have a query but no coords, geocode it first
    if query and (resolved_lat is None or resolved_lat == 0.0):
        try:
            geo = gemini_service.geocode_location(query)
            if geo:
                resolved_lat = geo.get('lat')
                resolved_lng = geo.get('lng')
                display_name = geo.get('display_name', query)
        except:
            pass

    # Fetch Real Landmarks
    if resolved_lat:
        try:
            real_data = gemini_service.find_nearby_legal_resources(resolved_lat, resolved_lng, lang)
            return jsonify({
                "results": real_data,
                "lat": resolved_lat,
                "lng": resolved_lng,
                "display_name": display_name
            })
        except Exception as e:
            print(f"Error fetching real landmarks: {e}")

    # Fallback to empty if nothing found or error
    return jsonify({
        "results": [],
        "lat": resolved_lat or 0.0,
        "lng": resolved_lng or 0.0,
        "display_name": display_name
    })
