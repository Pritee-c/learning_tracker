from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
from config import Config
from database import get_db
import jwt
import os
from datetime import datetime, timedelta
import hashlib

load_dotenv()
app = Flask(__name__)
CORS(app)
app.config.from_object(Config)

# Health check
@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'healthy', 'service': 'auth-service'}), 200

# Register user
@app.route('/auth/register', methods=['POST'])
def register():
    data = request.get_json()
    
    if not data or not data.get('email') or not data.get('password') or not data.get('name'):
        return jsonify({'error': 'Missing required fields'}), 400
    
    try:
        db = get_db()
        cursor = db.cursor()
        
        # Check if user exists
        cursor.execute('SELECT id FROM users WHERE email = %s', (data['email'],))
        if cursor.fetchone():
            return jsonify({'error': 'User already exists'}), 409
        
        # Hash password
        password_hash = hashlib.sha256(data['password'].encode()).hexdigest()
        
        # Create user
        cursor.execute(
            'INSERT INTO users (name, email, password_hash, role) VALUES (%s, %s, %s, %s)',
            (data['name'], data['email'], password_hash, 'student')
        )
        db.commit()
        user_id = cursor.lastrowid
        
        return jsonify({'message': 'User created', 'user_id': user_id}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Login user
@app.route('/auth/login', methods=['POST'])
def login():
    data = request.get_json()
    
    if not data or not data.get('email') or not data.get('password'):
        return jsonify({'error': 'Missing email or password'}), 400
    
    try:
        db = get_db()
        cursor = db.cursor()
        
        password_hash = hashlib.sha256(data['password'].encode()).hexdigest()
        
        cursor.execute(
            'SELECT id, name, email, role FROM users WHERE email = %s AND password_hash = %s',
            (data['email'], password_hash)
        )
        user = cursor.fetchone()
        
        if not user:
            return jsonify({'error': 'Invalid credentials'}), 401
        
        # Generate JWT token
        payload = {
            'user_id': user[0],
            'email': user[2],
            'role': user[3],
            'exp': datetime.utcnow() + timedelta(hours=24)
        }
        token = jwt.encode(payload, app.config['SECRET_KEY'], algorithm='HS256')
        
        return jsonify({
            'token': token,
            'user_id': user[0],
            'name': user[1],
            'email': user[2],
            'role': user[3]
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Verify token
@app.route('/auth/verify', methods=['POST'])
def verify_token():
    data = request.get_json()
    token = data.get('token') if data else None
    
    if not token:
        return jsonify({'error': 'No token provided'}), 400
    
    try:
        payload = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
        return jsonify({'valid': True, 'user_id': payload['user_id'], 'role': payload['role']}), 200
    except jwt.ExpiredSignatureError:
        return jsonify({'error': 'Token expired'}), 401
    except jwt.InvalidTokenError:
        return jsonify({'error': 'Invalid token'}), 401

# Get current user
@app.route('/auth/me', methods=['GET'])
def get_current_user():
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    
    if not token:
        return jsonify({'error': 'No token provided'}), 401
    
    try:
        payload = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
        db = get_db()
        cursor = db.cursor()
        
        cursor.execute('SELECT id, name, email, role FROM users WHERE id = %s', (payload['user_id'],))
        user = cursor.fetchone()
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        return jsonify({
            'user_id': user[0],
            'name': user[1],
            'email': user[2],
            'role': user[3]
        }), 200
    except jwt.InvalidTokenError:
        return jsonify({'error': 'Invalid token'}), 401
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)
