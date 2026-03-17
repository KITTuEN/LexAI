from flask import Blueprint, request, jsonify, render_template, redirect, url_for
from flask_jwt_extended import jwt_required, get_jwt_identity
from bson import ObjectId
from database import db, case_model

cases_bp = Blueprint('cases', __name__)

@cases_bp.route('/create', methods=['POST'])
@jwt_required()
def create():
    user_id = get_jwt_identity()
    title = request.form.get('title')
    summary = request.form.get('situation_summary')
    
    if not title or not summary:
        return jsonify({"error": "Title and summary are required"}), 400
        
    case_id = case_model.create_case(user_id, title, summary).inserted_id
    return redirect(url_for('chat.view', case_id=str(case_id)))

@cases_bp.route('/delete/<case_id>', methods=['POST'])
@jwt_required()
def delete(case_id):
    user_id = get_jwt_identity()
    case_model.collection.delete_one({"_id": ObjectId(case_id), "user_id": ObjectId(user_id)})
    return redirect(url_for('dashboard.home'))
