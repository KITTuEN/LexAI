from flask import Blueprint, render_template, request, jsonify
from flask_jwt_extended import jwt_required

rights_bp = Blueprint('rights', __name__)

@rights_bp.route('/')
@jwt_required()
def index():
    return render_template('rights.html')

@rights_bp.route('/guide/<topic>')
@jwt_required()
def get_guide(topic):
    guides = {
        'arrest': {
            'title': 'Rights During Arrest',
            'points': [
                'Right to know the grounds of arrest (Art 22(1) & Sec 50 CrPC/Sec 47 BNSS).',
                'Right to be produced before a Magistrate within 24 hours (Art 22(2) & Sec 57 CrPC/Sec 58 BNSS).',
                'Right to consult and be defended by a legal practitioner of choice.',
                'Right to remain silent (Art 20(3)).',
                'Women can only be arrested by a female officer, and generally not between sunset and sunrise (Sec 46(4) CrPC/Sec 43(5) BNSS).'
            ],
            'tips': 'Always ask for the arrest memo and ensure it is signed by a witness.'
        },
        'bail': {
            'title': 'Understanding Bail',
            'points': [
                'In bailable offenses, bail is a matter of right.',
                'In non-bailable offenses, bail is a matter of court discretion.',
                'Anticipatory bail can be sought before arrest for non-bailable offenses (Sec 438 CrPC/Sec 482 BNSS).',
                'Default bail is available if the investigation is not completed within 60/90 days (Sec 167(2) CrPC/Sec 187(2) BNSS).'
            ],
            'tips': 'Contact a lawyer immediately to prepare a bail application.'
        },
        'fir': {
            'title': 'Filing an FIR',
            'points': [
                'Information of a cognizable offense must be recorded by the police (Sec 154 CrPC/Sec 173 BNSS).',
                'Zero FIR: You can file an FIR at any police station regardless of jurisdiction.',
                'Right to a free copy of the FIR.',
                'If police refuse to file FIR, you can approach the SP/SSP or the Magistrate.'
            ],
            'tips': 'Ensure all details are accurate before signing the FIR.'
        }
    }
    return jsonify(guides.get(topic, {'error': 'Guide not found'}))
