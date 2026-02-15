from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from dotenv import load_dotenv
import requests
import os

load_dotenv()
app = Flask(__name__)
CORS(app)

# Service endpoints
AUTH_SERVICE = os.getenv('AUTH_SERVICE', 'http://localhost:5001')
COURSE_SERVICE = os.getenv('COURSE_SERVICE', 'http://localhost:5002')
QUIZ_SERVICE = os.getenv('QUIZ_SERVICE', 'http://localhost:5003')
PROGRESS_SERVICE = os.getenv('PROGRESS_SERVICE', 'http://localhost:5004')
REPORT_SERVICE = os.getenv('REPORT_SERVICE', 'http://localhost:5005')

# Health check
@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'healthy', 'service': 'gateway'}), 200

# ============ AUTH ROUTES ============
@app.route('/api/auth/register', methods=['POST'])
def register():
    data = request.get_json()
    try:
        response = requests.post(f'{AUTH_SERVICE}/auth/register', json=data)
        return jsonify(response.json()), response.status_code
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/auth/login', methods=['POST'])
def login():
    data = request.get_json()
    try:
        response = requests.post(f'{AUTH_SERVICE}/auth/login', json=data)
        return jsonify(response.json()), response.status_code
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/auth/verify', methods=['POST'])
def verify_token():
    data = request.get_json()
    try:
        response = requests.post(f'{AUTH_SERVICE}/auth/verify', json=data)
        return jsonify(response.json()), response.status_code
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/auth/me', methods=['GET'])
def get_me():
    headers = {'Authorization': request.headers.get('Authorization', '')}
    try:
        response = requests.get(f'{AUTH_SERVICE}/auth/me', headers=headers)
        return jsonify(response.json()), response.status_code
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ============ COURSE ROUTES ============
@app.route('/api/courses', methods=['GET'])
def get_courses():
    try:
        response = requests.get(f'{COURSE_SERVICE}/courses')
        return jsonify(response.json()), response.status_code
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/courses/<int:course_id>', methods=['GET'])
def get_course(course_id):
    try:
        response = requests.get(f'{COURSE_SERVICE}/courses/{course_id}')
        return jsonify(response.json()), response.status_code
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/courses', methods=['POST'])
def create_course():
    data = request.get_json()
    headers = {'Authorization': request.headers.get('Authorization', '')}
    try:
        response = requests.post(f'{COURSE_SERVICE}/courses', json=data, headers=headers)
        return jsonify(response.json()), response.status_code
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/courses/<int:course_id>/modules', methods=['GET'])
def get_modules(course_id):
    try:
        response = requests.get(f'{COURSE_SERVICE}/courses/{course_id}/modules')
        return jsonify(response.json()), response.status_code
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/modules/<int:module_id>/lessons', methods=['GET'])
def get_lessons(module_id):
    try:
        response = requests.get(f'{COURSE_SERVICE}/modules/{module_id}/lessons')
        return jsonify(response.json()), response.status_code
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ============ QUIZ ROUTES ============
@app.route('/api/quizzes/lesson/<int:lesson_id>', methods=['GET'])
def get_quiz(lesson_id):
    try:
        response = requests.get(f'{QUIZ_SERVICE}/quizzes/lesson/{lesson_id}')
        return jsonify(response.json()), response.status_code
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/quizzes/<int:quiz_id>/attempts', methods=['POST'])
def submit_quiz_attempt(quiz_id):
    data = request.get_json()
    headers = {'Authorization': request.headers.get('Authorization', '')}
    try:
        response = requests.post(f'{QUIZ_SERVICE}/quizzes/{quiz_id}/attempts', json=data, headers=headers)
        return jsonify(response.json()), response.status_code
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/quizzes/<int:quiz_id>/attempts/user', methods=['GET'])
def get_user_quiz_attempts(quiz_id):
    headers = {'Authorization': request.headers.get('Authorization', '')}
    try:
        response = requests.get(f'{QUIZ_SERVICE}/quizzes/{quiz_id}/attempts/user', headers=headers)
        return jsonify(response.json()), response.status_code
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ============ PROGRESS ROUTES ============
@app.route('/api/progress', methods=['GET'])
def get_progress():
    headers = {'Authorization': request.headers.get('Authorization', '')}
    try:
        response = requests.get(f'{PROGRESS_SERVICE}/progress', headers=headers)
        return jsonify(response.json()), response.status_code
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/progress/course/<int:course_id>', methods=['GET'])
def get_course_progress(course_id):
    headers = {'Authorization': request.headers.get('Authorization', '')}
    try:
        response = requests.get(f'{PROGRESS_SERVICE}/progress/course/{course_id}', headers=headers)
        return jsonify(response.json()), response.status_code
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/progress/lesson/<int:lesson_id>/start', methods=['POST'])
def start_lesson(lesson_id):
    headers = {'Authorization': request.headers.get('Authorization', '')}
    try:
        response = requests.post(f'{PROGRESS_SERVICE}/progress/lesson/{lesson_id}/start', headers=headers)
        return jsonify(response.json()), response.status_code
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/progress/lesson/<int:lesson_id>/complete', methods=['POST'])
def complete_lesson(lesson_id):
    headers = {'Authorization': request.headers.get('Authorization', '')}
    try:
        response = requests.post(f'{PROGRESS_SERVICE}/progress/lesson/{lesson_id}/complete', headers=headers)
        return jsonify(response.json()), response.status_code
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ============ REPORT ROUTES ============
@app.route('/api/reports/week', methods=['GET'])
def get_weekly_report():
    headers = {'Authorization': request.headers.get('Authorization', '')}
    try:
        response = requests.get(f'{REPORT_SERVICE}/reports/week', headers=headers)
        return jsonify(response.json()), response.status_code
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/reports/history', methods=['GET'])
def get_report_history():
    headers = {'Authorization': request.headers.get('Authorization', '')}
    try:
        response = requests.get(f'{REPORT_SERVICE}/reports/history', headers=headers)
        return jsonify(response.json()), response.status_code
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/reports/generate', methods=['POST'])
def generate_reports():
    headers = {'Authorization': request.headers.get('Authorization', '')}
    try:
        response = requests.post(f'{REPORT_SERVICE}/reports/generate', headers=headers)
        return jsonify(response.json()), response.status_code
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ============ STATIC CONTENT (if serving frontend) ============
@app.route('/', methods=['GET'])
def index():
    return jsonify({
        'message': 'Learning Tracker API Gateway',
        'version': '1.0',
        'services': {
            'auth': f'{AUTH_SERVICE}/health',
            'course': f'{COURSE_SERVICE}/health',
            'quiz': f'{QUIZ_SERVICE}/health',
            'progress': f'{PROGRESS_SERVICE}/health',
            'report': f'{REPORT_SERVICE}/health'
        }
    }), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
