import os
from flask import Flask, jsonify, request, render_template, redirect, url_for
from flask_jwt_extended import JWTManager, set_access_cookies, jwt_required, get_jwt_identity, unset_jwt_cookies
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from pymongo import MongoClient
from dotenv import load_dotenv
from config import Config

# Models
from models.user import UserModel
from models.case import CaseModel
from services.translations import translate

load_dotenv()

app = Flask(__name__)
app.config.from_object(Config)

# Extensions
CORS(app)
jwt = JWTManager(app)
from flask_wtf.csrf import CSRFProtect
csrf = CSRFProtect(app)
limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://"
)

# Database and Models
from database import db, user_model, case_model

# Context processor for footer disclaimer
# Blueprints
from routes.auth import auth_bp
from routes.dashboard import dashboard_bp
from routes.cases import cases_bp
from routes.chat import chat_bp
from routes.search import search_bp
from routes.complaint import complaint_bp
from routes.ocr import ocr_bp
from routes.rights import rights_bp
from routes.lawyer_chat import lawyer_chat_bp
from routes.lawyer import lawyer_bp
from routes.generator import generator_bp

app.register_blueprint(auth_bp, url_prefix='/auth')
app.register_blueprint(dashboard_bp, url_prefix='/dashboard')
app.register_blueprint(cases_bp, url_prefix='/cases')
app.register_blueprint(chat_bp, url_prefix='/case')
app.register_blueprint(search_bp, url_prefix='/search')
app.register_blueprint(complaint_bp, url_prefix='/complaint')
app.register_blueprint(ocr_bp, url_prefix='/ocr')
app.register_blueprint(rights_bp, url_prefix='/rights')
app.register_blueprint(lawyer_chat_bp, url_prefix='/lawyer-chat')
app.register_blueprint(lawyer_bp, url_prefix='/lawyer')
app.register_blueprint(generator_bp, url_prefix='/generator')

# Custom Filters
@app.template_filter('decrypt_name')
def decrypt_name_filter(s):
    from services.encryption import encryption_service
    return encryption_service.decrypt(s)

# Context processor for footer disclaimer
@app.context_processor
def inject_globals():
    from flask_jwt_extended import get_jwt_identity, verify_jwt_in_request
    from bson import ObjectId
    
    current_user = None
    try:
        # optional=True allows the request to proceed even if JWT is missing
        verify_jwt_in_request(optional=True)
        identity = get_jwt_identity()
        if identity:
            current_user = user_model.collection.find_one({"_id": ObjectId(identity)})
    except Exception:
        pass

    return {
        "legal_disclaimer": translate('legal_disclaimer_text', current_user.get('preferred_language', 'English') if current_user else 'English'),
        "current_user": current_user,
        "_t": lambda key: translate(key, current_user.get('preferred_language', 'English') if current_user else 'English')
    }

@app.route('/lawyers')
@jwt_required()
def list_lawyers():
    lawyers = user_model.get_lawyers()
    return render_template('lawyers.html', lawyers=lawyers)

@app.route('/')
def index():
    from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity
    try:
        verify_jwt_in_request(optional=True)
        if get_jwt_identity():
            return redirect(url_for('dashboard.member_home'))
    except:
        pass
    return render_template('index.html')

@app.route('/robots.txt', strict_slashes=False)
def robots_txt():
    # Clean host_url and ensure it ends without a slash before appending sitemap.xml
    host_url = request.host_url.rstrip('/')
    content = f"User-agent: *\nAllow: /\nDisallow: /auth/\nDisallow: /dashboard/\nDisallow: /case/\nDisallow: /ocr/\nSitemap: {host_url}/sitemap.xml"
    return content, 200, {'Content-Type': 'text/plain'}

@app.route('/sitemap.xml', strict_slashes=False)
def sitemap_xml():
    # Use url_for with _external=True for more reliable absolute URLs
    urls = [
        url_for('index', _external=True),
        url_for('auth.login', _external=True),
        url_for('auth.signup', _external=True)
    ]
    
    # Pre-clean the URLs to avoid any double slashes from url_for in some environments
    cleaned_urls = [u.rstrip('/') for u in urls]
    
    content = f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url>
    <loc>{cleaned_urls[0]}/</loc>
    <priority>1.0</priority>
  </url>
  <url>
    <loc>{cleaned_urls[1]}</loc>
    <priority>0.8</priority>
  </url>
  <url>
    <loc>{cleaned_urls[2]}</loc>
    <priority>0.8</priority>
  </url>
</urlset>""".strip()
    return content, 200, {'Content-Type': 'application/xml'}

@app.route('/google10c68f1d7dfe2f5f.html')
def google_verify():
    return render_template('google10c68f1d7dfe2f5f.html')

if __name__ == '__main__':
    app.run(debug=True, use_reloader=False)
