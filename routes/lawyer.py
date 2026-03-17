from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from flask_jwt_extended import jwt_required, get_jwt_identity
from bson import ObjectId
from database import user_model, lawyer_chat_model

lawyer_bp = Blueprint('lawyer_panel', __name__)

@lawyer_bp.route('/profile', methods=['GET', 'POST'])
@jwt_required()
def profile():
    user_id = get_jwt_identity()
    user = user_model.collection.find_one({"_id": ObjectId(user_id)})
    
    if user.get('role') != 'lawyer':
        return redirect(url_for('dashboard.member_home'))

    if request.method == 'POST':
        experience_summary = request.form.get('experience_summary')
        user_model.update_lawyer_profile(user_id, experience_summary)
        return redirect(url_for('dashboard.member_home'))

    return render_template('lawyer_profile.html', user=user)

@lawyer_bp.route('/messages')
@jwt_required()
def messages():
    user_id = get_jwt_identity()
    user = user_model.collection.find_one({"_id": ObjectId(user_id)})
    
    if user.get('role') != 'lawyer':
        return redirect(url_for('dashboard.member_home'))

    chats = lawyer_chat_model.get_lawyer_chats(user_id)
    # We need to fetch citizen names for each chat
    for chat in chats:
        citizen = user_model.collection.find_one({"_id": chat['user_id']})
        chat['citizen_name'] = citizen.get('name_encrypted') # Filter handles decryption
    
    return render_template('lawyer_messages.html', chats=chats)
