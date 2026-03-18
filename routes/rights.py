from flask import Blueprint, render_template, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

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
    lang = user.get('preferred_language', 'English') if user else 'English'
    
    # Hardcoded legal guides based on BNS 2023 / BNSS / Constitution of India
    guides = {
        'arrest': {
            "title": "Your Rights During Arrest",
            "points": [
                "Right to know the grounds of arrest under BNSS Section 47.",
                "Right to inform a relative or friend immediately upon arrest (BNSS Section 48).",
                "Right to be produced before a Magistrate within 24 hours of arrest (Article 22 of Constitution).",
                "Right to consult a legal practitioner of your choice during interrogation.",
                "Right to be examined by a medical officer (BNSS Section 53)."
            ],
            "tips": "Always remain calm. Do not resist arrest physically, but clearly state that you wish to speak to your lawyer."
        },
        'bail': {
            "title": "Bail & Bond Rights",
            "points": [
                "Bailable Offences: Bail is your absolute right. The police/court must grant bail if you provide the bond (BNSS Section 478).",
                "Non-Bailable Offences: Bail is at the discretion of the court. You can apply before a Magistrate or Sessions Court.",
                "Anticipatory Bail: You can apply to the Sessions Court or High Court if you apprehend arrest (BNSS Section 482).",
                "Default Bail: Absolute right to release if the investigation is not completed within 60 or 90 days depending on the offence (BNSS Section 187).",
                "Bail bond amount must be reasonable and not excessive."
            ],
            "tips": "Ensure you have a local surety ready (someone who can stand guarantee for you) to process your bail faster."
        },
        'fir': {
            "title": "First Information Report (FIR) Rights",
            "points": [
                "Right to register a 'Zero FIR' at any police station, regardless of jurisdiction.",
                "Right to get a free copy of the FIR immediately after it is registered (BNSS Section 173).",
                "Right to read the FIR and verify the details before signing it.",
                "Right to file an e-FIR section for certain cognizable offences under the new BNSS provisions.",
                "If the police refuse to register an FIR, you can send a written complaint to the Superintendent of Police (SP) by post."
            ],
            "tips": "Always keep a stamped and signed copy of your given complaint as proof of submission before the formal FIR is generated."
        }
    }
    
    # Fallback to arrest if topic not found
    guide = guides.get(topic, guides['arrest'])
    return jsonify(guide)
