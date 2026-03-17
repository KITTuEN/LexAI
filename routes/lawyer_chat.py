from flask import Blueprint, render_template, request, jsonify, redirect, url_for
from flask_jwt_extended import jwt_required, get_jwt_identity
from bson import ObjectId
from database import lawyer_chat_model, user_model

lawyer_chat_bp = Blueprint('lawyer_chat', __name__)

@lawyer_chat_bp.route('/initiate/<lawyer_id>')
@jwt_required()
def initiate(lawyer_id):
    user_id = get_jwt_identity()
    chat_id = lawyer_chat_model.create_chat(user_id, lawyer_id)
    return redirect(url_for('lawyer_chat.view_chat', chat_id=chat_id))

@lawyer_chat_bp.route('/chat/<chat_id>')
@jwt_required()
def view_chat(chat_id):
    user_id = get_jwt_identity()
    chat = lawyer_chat_model.get_chat(chat_id)
    if not chat:
        return "Chat not found", 404
    
    if str(chat['user_id']) != user_id and str(chat['lawyer_id']) != user_id:
        return "Access Denied", 403
    
    # Get other party name
    other_party_id = chat['lawyer_id'] if str(chat['user_id']) == user_id else chat['user_id']
    other_party = user_model.collection.find_one({"_id": other_party_id})
    
    return render_template('lawyer_chat.html', chat=chat, other_party=other_party)

@lawyer_chat_bp.route('/chat/<chat_id>/message', methods=['POST'])
@jwt_required()
def send_message(chat_id):
    user_id = get_jwt_identity()
    content = request.json.get('message')
    if not content:
        return jsonify({"error": "Message content required"}), 400
    
    chat = lawyer_chat_model.get_chat(chat_id)
    if not chat:
        return jsonify({"error": "Chat not found"}), 404
    
    if str(chat['user_id']) != user_id and str(chat['lawyer_id']) != user_id:
        return jsonify({"error": "Access Denied"}), 403
    
    lawyer_chat_model.add_message(chat_id, user_id, content)
    return jsonify({"success": True})

@lawyer_chat_bp.route('/chat/<chat_id>/messages')
@jwt_required()
def get_messages(chat_id):
    user_id = get_jwt_identity()
    chat = lawyer_chat_model.get_chat(chat_id)
    if not chat:
        return jsonify({"error": "Chat not found"}), 404
    
    if str(chat['user_id']) != user_id and str(chat['lawyer_id']) != user_id:
        return jsonify({"error": "Access Denied"}), 403
    
    # Format messages for JSON (converting ObjectId and Datetime)
    formatted_messages = []
    for msg in chat.get('messages', []):
        formatted_messages.append({
            "sender_id": str(msg['sender_id']),
            "content": msg['content'],
            "timestamp": msg['timestamp'].strftime('%H:%M')
        })
    
    return jsonify({"messages": formatted_messages})
