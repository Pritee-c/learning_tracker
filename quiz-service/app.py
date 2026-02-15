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
    return jsonify({'status': 'healthy', 'service': 'quiz-service'}), 200

# Get quiz by lesson ID
@app.route('/quizzes/lesson/<int:lesson_id>', methods=['GET'])
def get_quiz_by_lesson(lesson_id):
    try:
        db = get_db()
        cursor = db.cursor()
        
        cursor.execute(
            'SELECT id, title, passing_score, max_attempts FROM quizzes WHERE lesson_id = %s',
            (lesson_id,)
        )
        quiz = cursor.fetchone()
        
        if not quiz:
            return jsonify({'error': 'Quiz not found'}), 404
        
        # Get questions
        cursor.execute(
            'SELECT id, prompt, type, order_index FROM questions WHERE quiz_id = %s ORDER BY order_index',
            (quiz[0],)
        )
        questions = cursor.fetchall()
        
        questions_data = []
        for q in questions:
            cursor.execute(
                'SELECT id, text, order_index FROM choices WHERE question_id = %s ORDER BY order_index',
                (q[0],)
            )
            choices = cursor.fetchall()
            
            questions_data.append({
                'id': q[0],
                'prompt': q[1],
                'type': q[2],
                'order_index': q[3],
                'choices': [{'id': c[0], 'text': c[1], 'order_index': c[2]} for c in choices]
            })
        
        cursor.close()
        
        return jsonify({
            'id': quiz[0],
            'title': quiz[1],
            'passing_score': quiz[2],
            'max_attempts': quiz[3],
            'questions': questions_data
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Submit quiz attempt
@app.route('/quizzes/<int:quiz_id>/attempts', methods=['POST'])
def submit_attempt(quiz_id):
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    
    if not token:
        return jsonify({'error': 'No token provided'}), 401
    
    try:
        payload = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
        data = request.get_json()
        
        if not data or 'answers' not in data:
            return jsonify({'error': 'Missing answers'}), 400
        
        db = get_db()
        cursor = db.cursor()
        
        # Create attempt record
        cursor.execute(
            'INSERT INTO quiz_attempts (quiz_id, user_id, started_at, finished_at) VALUES (%s, %s, NOW(), NOW())',
            (quiz_id, payload['user_id'])
        )
        db.commit()
        attempt_id = cursor.lastrowid
        
        # Process answers
        correct_count = 0
        total_count = 0
        
        for answer in data['answers']:
            question_id = answer.get('question_id')
            choice_id = answer.get('choice_id')
            
            # Check if correct
            cursor.execute(
                'SELECT is_correct FROM choices WHERE id = %s AND question_id = %s',
                (choice_id, question_id)
            )
            choice = cursor.fetchone()
            is_correct = choice[0] if choice else False
            
            # Record answer
            cursor.execute(
                'INSERT INTO attempt_answers (attempt_id, question_id, choice_id, is_correct) VALUES (%s, %s, %s, %s)',
                (attempt_id, question_id, choice_id, is_correct)
            )
            
            if is_correct:
                correct_count += 1
            total_count += 1
        
        db.commit()
        
        # Calculate score
        score = (correct_count / total_count * 100) if total_count > 0 else 0
        
        # Update attempt with results
        cursor.execute(
            'UPDATE quiz_attempts SET score = %s, total_questions = %s, correct_answers = %s WHERE id = %s',
            (score, total_count, correct_count, attempt_id)
        )
        db.commit()
        cursor.close()
        
        return jsonify({
            'attempt_id': attempt_id,
            'score': score,
            'correct_answers': correct_count,
            'total_questions': total_count
        }), 201
    except jwt.InvalidTokenError:
        return jsonify({'error': 'Invalid token'}), 401
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Get user's quiz attempts
@app.route('/quizzes/<int:quiz_id>/attempts/user', methods=['GET'])
def get_user_attempts(quiz_id):
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    
    if not token:
        return jsonify({'error': 'No token provided'}), 401
    
    try:
        payload = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
        db = get_db()
        cursor = db.cursor()
        
        cursor.execute(
            'SELECT id, score, correct_answers, total_questions, started_at, finished_at FROM quiz_attempts WHERE quiz_id = %s AND user_id = %s ORDER BY finished_at DESC',
            (quiz_id, payload['user_id'])
        )
        attempts = cursor.fetchall()
        cursor.close()
        
        result = [
            {
                'id': a[0],
                'score': float(a[1]) if a[1] else None,
                'correct_answers': a[2],
                'total_questions': a[3],
                'started_at': str(a[4]),
                'finished_at': str(a[5])
            } for a in attempts
        ]
        
        return jsonify(result), 200
    except jwt.InvalidTokenError:
        return jsonify({'error': 'Invalid token'}), 401
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5003, debug=True)
