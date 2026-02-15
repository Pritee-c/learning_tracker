from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
from config import Config
from database import get_db
import jwt
from datetime import datetime

load_dotenv()
app = Flask(__name__)
CORS(app)
app.config.from_object(Config)

# Health check
@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'healthy', 'service': 'progress-service'}), 200

# Get user's overall progress
@app.route('/progress', methods=['GET'])
def get_user_progress():
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    
    if not token:
        return jsonify({'error': 'No token provided'}), 401
    
    try:
        payload = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
        db = get_db()
        cursor = db.cursor()
        
        # Get all lessons user is enrolled in
        cursor.execute(
            '''SELECT p.id, p.lesson_id, p.status, l.title, m.id, c.id, c.title, p.completed_at
               FROM progress p
               JOIN lessons l ON p.lesson_id = l.id
               JOIN modules m ON l.module_id = m.id
               JOIN courses c ON m.course_id = c.id
               WHERE p.user_id = %s
               ORDER BY c.id, m.order_index, l.order_index''',
            (payload['user_id'],)
        )
        progress_records = cursor.fetchall()
        cursor.close()
        
        result = [
            {
                'id': p[0],
                'lesson_id': p[1],
                'status': p[2],
                'lesson_title': p[3],
                'module_id': p[4],
                'course_id': p[5],
                'course_title': p[6],
                'completed_at': str(p[7]) if p[7] else None
            } for p in progress_records
        ]
        
        return jsonify(result), 200
    except jwt.InvalidTokenError:
        return jsonify({'error': 'Invalid token'}), 401
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Get progress for specific course
@app.route('/progress/course/<int:course_id>', methods=['GET'])
def get_course_progress(course_id):
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    
    if not token:
        return jsonify({'error': 'No token provided'}), 401
    
    try:
        payload = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
        db = get_db()
        cursor = db.cursor()
        
        # Get course progress
        cursor.execute(
            '''SELECT COUNT(*) as total_lessons, 
                      SUM(CASE WHEN p.status = 'completed' THEN 1 ELSE 0 END) as completed_lessons
               FROM lessons l
               JOIN modules m ON l.module_id = m.id
               LEFT JOIN progress p ON l.id = p.lesson_id AND p.user_id = %s
               WHERE m.course_id = %s''',
            (payload['user_id'], course_id)
        )
        stats = cursor.fetchone()
        
        # Get detailed progress
        cursor.execute(
            '''SELECT l.id, l.title, COALESCE(p.status, 'not_started'), m.order_index, l.order_index
               FROM lessons l
               JOIN modules m ON l.module_id = m.id
               LEFT JOIN progress p ON l.id = p.lesson_id AND p.user_id = %s
               WHERE m.course_id = %s
               ORDER BY m.order_index, l.order_index''',
            (payload['user_id'], course_id)
        )
        lessons = cursor.fetchall()
        cursor.close()
        
        completion_percent = 0
        if stats[0] > 0:
            completion_percent = (stats[1] or 0) / stats[0] * 100
        
        return jsonify({
            'course_id': course_id,
            'total_lessons': stats[0],
            'completed_lessons': stats[1] or 0,
            'completion_percent': round(completion_percent, 2),
            'lessons': [
                {
                    'lesson_id': l[0],
                    'title': l[1],
                    'status': l[2],
                    'module_order': l[3],
                    'lesson_order': l[4]
                } for l in lessons
            ]
        }), 200
    except jwt.InvalidTokenError:
        return jsonify({'error': 'Invalid token'}), 401
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Mark lesson as started/in progress
@app.route('/progress/lesson/<int:lesson_id>/start', methods=['POST'])
def start_lesson(lesson_id):
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    
    if not token:
        return jsonify({'error': 'No token provided'}), 401
    
    try:
        payload = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
        db = get_db()
        cursor = db.cursor()
        
        # Create or update progress
        cursor.execute(
            'SELECT id FROM progress WHERE user_id = %s AND lesson_id = %s',
            (payload['user_id'], lesson_id)
        )
        progress = cursor.fetchone()
        
        if progress:
            cursor.execute(
                'UPDATE progress SET status = %s, started_at = NOW() WHERE id = %s',
                ('in_progress', progress[0])
            )
        else:
            cursor.execute(
                'INSERT INTO progress (user_id, lesson_id, status, started_at) VALUES (%s, %s, %s, NOW())',
                (payload['user_id'], lesson_id, 'in_progress')
            )
        
        db.commit()
        cursor.close()
        
        return jsonify({'message': 'Lesson started'}), 200
    except jwt.InvalidTokenError:
        return jsonify({'error': 'Invalid token'}), 401
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Mark lesson as completed
@app.route('/progress/lesson/<int:lesson_id>/complete', methods=['POST'])
def complete_lesson(lesson_id):
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    
    if not token:
        return jsonify({'error': 'No token provided'}), 401
    
    try:
        payload = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
        db = get_db()
        cursor = db.cursor()
        
        cursor.execute(
            'UPDATE progress SET status = %s, completed_at = NOW() WHERE user_id = %s AND lesson_id = %s',
            ('completed', payload['user_id'], lesson_id)
        )
        db.commit()
        cursor.close()
        
        return jsonify({'message': 'Lesson completed'}), 200
    except jwt.InvalidTokenError:
        return jsonify({'error': 'Invalid token'}), 401
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5004, debug=True)
