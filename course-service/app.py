from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
from config import Config
from database import get_db
import jwt

load_dotenv()
app = Flask(__name__)
CORS(app)
app.config.from_object(Config)

# Health check
@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'healthy', 'service': 'course-service'}), 200

# Get all courses
@app.route('/courses', methods=['GET'])
def get_courses():
    try:
        db = get_db()
        cursor = db.cursor()
        
        cursor.execute(
            'SELECT id, title, description, level, instructor_id, created_at FROM courses'
        )
        courses = cursor.fetchall()
        cursor.close()
        
        result = [
            {
                'id': c[0],
                'title': c[1],
                'description': c[2],
                'level': c[3],
                'instructor_id': c[4],
                'created_at': str(c[5])
            } for c in courses
        ]
        
        return jsonify(result), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Get course by ID
@app.route('/courses/<int:course_id>', methods=['GET'])
def get_course(course_id):
    try:
        db = get_db()
        cursor = db.cursor()
        
        cursor.execute(
            'SELECT id, title, description, level, instructor_id, created_at FROM courses WHERE id = %s',
            (course_id,)
        )
        course = cursor.fetchone()
        cursor.close()
        
        if not course:
            return jsonify({'error': 'Course not found'}), 404
        
        return jsonify({
            'id': course[0],
            'title': course[1],
            'description': course[2],
            'level': course[3],
            'instructor_id': course[4],
            'created_at': str(course[5])
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Create course (requires auth)
@app.route('/courses', methods=['POST'])
def create_course():
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    
    if not token:
        return jsonify({'error': 'No token provided'}), 401
    
    try:
        payload = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
        
        if payload['role'] not in ['admin', 'instructor']:
            return jsonify({'error': 'Unauthorized'}), 403
        
        data = request.get_json()
        
        if not data or not data.get('title'):
            return jsonify({'error': 'Missing required fields'}), 400
        
        db = get_db()
        cursor = db.cursor()
        
        cursor.execute(
            'INSERT INTO courses (title, description, level, instructor_id) VALUES (%s, %s, %s, %s)',
            (data['title'], data.get('description'), data.get('level', 'beginner'), payload['user_id'])
        )
        db.commit()
        course_id = cursor.lastrowid
        cursor.close()
        
        return jsonify({'message': 'Course created', 'course_id': course_id}), 201
    except jwt.InvalidTokenError:
        return jsonify({'error': 'Invalid token'}), 401
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Get modules for course
@app.route('/courses/<int:course_id>/modules', methods=['GET'])
def get_modules(course_id):
    try:
        db = get_db()
        cursor = db.cursor()
        
        cursor.execute(
            'SELECT id, title, order_index FROM modules WHERE course_id = %s ORDER BY order_index',
            (course_id,)
        )
        modules = cursor.fetchall()
        cursor.close()
        
        result = [
            {
                'id': m[0],
                'title': m[1],
                'order_index': m[2]
            } for m in modules
        ]
        
        return jsonify(result), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Get lessons for module
@app.route('/modules/<int:module_id>/lessons', methods=['GET'])
def get_lessons(module_id):
    try:
        db = get_db()
        cursor = db.cursor()
        
        cursor.execute(
            'SELECT id, title, content_url, description, order_index, duration_minutes FROM lessons WHERE module_id = %s ORDER BY order_index',
            (module_id,)
        )
        lessons = cursor.fetchall()
        cursor.close()
        
        result = [
            {
                'id': l[0],
                'title': l[1],
                'content_url': l[2],
                'description': l[3],
                'order_index': l[4],
                'duration_minutes': l[5]
            } for l in lessons
        ]
        
        return jsonify(result), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Create module (requires auth)
@app.route('/modules', methods=['POST'])
def create_module():
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    
    if not token:
        return jsonify({'error': 'No token provided'}), 401
    
    try:
        payload = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
        
        if payload['role'] not in ['admin', 'instructor']:
            return jsonify({'error': 'Unauthorized'}), 403
        
        data = request.get_json()
        
        if not data or not data.get('course_id') or not data.get('title'):
            return jsonify({'error': 'Missing required fields'}), 400
        
        db = get_db()
        cursor = db.cursor()
        
        cursor.execute(
            'INSERT INTO modules (course_id, title, order_index) VALUES (%s, %s, %s)',
            (data['course_id'], data['title'], data.get('order_index', 1))
        )
        db.commit()
        module_id = cursor.lastrowid
        cursor.close()
        
        return jsonify({'message': 'Module created', 'module_id': module_id}), 201
    except jwt.InvalidTokenError:
        return jsonify({'error': 'Invalid token'}), 401
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5002, debug=True)
