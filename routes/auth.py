from flask import Blueprint, request, jsonify, render_template, redirect, url_for, make_response
from flask_jwt_extended import create_access_token, set_access_cookies, unset_jwt_cookies
from models.user import UserModel
from models.user import UserModel
from database import user_model

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        data = request.form
        name = data.get('name')
        email = data.get('email')
        phone = data.get('phone')
        password = data.get('password')
        confirm_password = data.get('confirm_password')

        if password != confirm_password:
            return render_template('signup.html', error="Passwords do not match")

        if user_model.find_by_email(email):
            return render_template('signup.html', error="Email already registered")

        role = data.get('role', 'user')
        lawyer_data = None
        if role == 'lawyer':
            lawyer_data = {
                'aadhar': data.get('aadhar'),
                'father_name': data.get('father_name'),
                'mother_name': data.get('mother_name'),
                'lawyer_id': data.get('lawyer_id'),
                'experience_summary': data.get('experience_summary')
            }

        user_model.create_user(name, email, phone, password, role=role, lawyer_data=lawyer_data)
        return redirect(url_for('auth.login'))

    return render_template('signup.html')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        remember = request.form.get('remember') == 'on'

        user = user_model.find_by_email(email)
        if user and user_model.verify_password(password, user['password_hash']):
            expires = 30 if remember else 1
            access_token = create_access_token(identity=str(user['_id']))
            resp = make_response(redirect(url_for('dashboard.member_home')))
            set_access_cookies(resp, access_token)
            return resp
        
        return render_template('login.html', error="Invalid email or password")

    return render_template('login.html')

@auth_bp.route('/logout')
def logout():
    resp = make_response(redirect(url_for('index')))
    unset_jwt_cookies(resp)
    return resp
