from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
from config import Config
from database import get_db
import jwt
from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler

load_dotenv()
app = Flask(__name__)
CORS(app)
app.config.from_object(Config)

# Health check
@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'healthy', 'service': 'report-service'}), 200

# Get weekly report for user
@app.route('/reports/week', methods=['GET'])
def get_weekly_report():
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    
    if not token:
        return jsonify({'error': 'No token provided'}), 401
    
    try:
        payload = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
        db = get_db()
        cursor = db.cursor()
        
        # Get this week's report (last 7 days)
        week_ago = datetime.now() - timedelta(days=7)
        
        # Lessons completed this week
        cursor.execute(
            '''SELECT COUNT(*) FROM progress 
               WHERE user_id = %s AND status = 'completed' AND completed_at >= %s''',
            (payload['user_id'], week_ago)
        )
        lessons_completed = cursor.fetchone()[0]
        
        # Quizzes taken this week
        cursor.execute(
            '''SELECT COUNT(*) FROM quiz_attempts 
               WHERE user_id = %s AND finished_at >= %s''',
            (payload['user_id'], week_ago)
        )
        quizzes_taken = cursor.fetchone()[0]
        
        # Average quiz score this week
        cursor.execute(
            '''SELECT AVG(score) FROM quiz_attempts 
               WHERE user_id = %s AND finished_at >= %s AND score IS NOT NULL''',
            (payload['user_id'], week_ago)
        )
        avg_score = cursor.fetchone()[0]
        
        cursor.close()
        
        return jsonify({
            'user_id': payload['user_id'],
            'period': 'last 7 days',
            'lessons_completed': lessons_completed,
            'quizzes_taken': quizzes_taken,
            'average_quiz_score': float(avg_score) if avg_score else 0
        }), 200
    except jwt.InvalidTokenError:
        return jsonify({'error': 'Invalid token'}), 401
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Trigger report generation (for testing)
@app.route('/reports/generate', methods=['POST'])
def generate_reports():
    """Generate weekly reports for all users - callable manually"""
    try:
        db = get_db()
        cursor = db.cursor()
        
        today = datetime.now().date()
        
        # Get all users
        cursor.execute('SELECT id FROM users WHERE active = TRUE')
        users = cursor.fetchall()
        
        for user in users:
            user_id = user[0]
            
            # Get this week's stats
            week_ago = datetime.now() - timedelta(days=7)
            
            cursor.execute(
                '''SELECT COUNT(*) FROM progress 
                   WHERE user_id = %s AND status = 'completed' AND completed_at >= %s''',
                (user_id, week_ago)
            )
            lessons_completed = cursor.fetchone()[0]
            
            cursor.execute(
                '''SELECT COUNT(*) FROM quiz_attempts 
                   WHERE user_id = %s AND finished_at >= %s''',
                (user_id, week_ago)
            )
            quizzes_taken = cursor.fetchone()[0]
            
            cursor.execute(
                '''SELECT AVG(score) FROM quiz_attempts 
                   WHERE user_id = %s AND finished_at >= %s AND score IS NOT NULL''',
                (user_id, week_ago)
            )
            avg_score = cursor.fetchone()[0]
            
            # Store report
            cursor.execute(
                '''INSERT INTO reports (user_id, report_date, lessons_completed, quizzes_taken, average_quiz_score, sent_at)
                   VALUES (%s, %s, %s, %s, %s, NOW())
                   ON DUPLICATE KEY UPDATE 
                   lessons_completed = VALUES(lessons_completed),
                   quizzes_taken = VALUES(quizzes_taken),
                   average_quiz_score = VALUES(average_quiz_score),
                   sent_at = NOW()''',
                (user_id, today, lessons_completed, quizzes_taken, avg_score)
            )
        
        db.commit()
        cursor.close()
        
        return jsonify({'message': f'Generated reports for {len(users)} users'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Get report history
@app.route('/reports/history', methods=['GET'])
def get_report_history():
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    
    if not token:
        return jsonify({'error': 'No token provided'}), 401
    
    try:
        payload = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
        db = get_db()
        cursor = db.cursor()
        
        cursor.execute(
            '''SELECT id, report_date, lessons_completed, quizzes_taken, average_quiz_score, sent_at
               FROM reports WHERE user_id = %s ORDER BY report_date DESC LIMIT 12''',
            (payload['user_id'],)
        )
        reports = cursor.fetchall()
        cursor.close()
        
        result = [
            {
                'id': r[0],
                'report_date': str(r[1]),
                'lessons_completed': r[2],
                'quizzes_taken': r[3],
                'average_quiz_score': float(r[4]) if r[4] else 0,
                'sent_at': str(r[5]) if r[5] else None
            } for r in reports
        ]
        
        return jsonify(result), 200
    except jwt.InvalidTokenError:
        return jsonify({'error': 'Invalid token'}), 401
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Background scheduler (runs weekly)
def schedule_reports():
    """This would run weekly to generate reports automatically"""
    db = get_db()
    cursor = db.cursor()
    
    today = datetime.now().date()
    week_ago = datetime.now() - timedelta(days=7)
    
    # Get all active users
    cursor.execute('SELECT id FROM users WHERE active = TRUE')
    users = cursor.fetchall()
    
    for user in users:
        user_id = user[0]
        
        cursor.execute(
            '''SELECT COUNT(*) FROM progress 
               WHERE user_id = %s AND status = 'completed' AND completed_at >= %s''',
            (user_id, week_ago)
        )
        lessons_completed = cursor.fetchone()[0]
        
        cursor.execute(
            '''SELECT COUNT(*) FROM quiz_attempts 
               WHERE user_id = %s AND finished_at >= %s''',
            (user_id, week_ago)
        )
        quizzes_taken = cursor.fetchone()[0]
        
        cursor.execute(
            '''SELECT AVG(score) FROM quiz_attempts 
               WHERE user_id = %s AND finished_at >= %s AND score IS NOT NULL''',
            (user_id, week_ago)
        )
        avg_score = cursor.fetchone()[0]
        
        cursor.execute(
            '''INSERT INTO reports (user_id, report_date, lessons_completed, quizzes_taken, average_quiz_score, sent_at)
               VALUES (%s, %s, %s, %s, %s, NOW())
               ON DUPLICATE KEY UPDATE 
               lessons_completed = VALUES(lessons_completed),
               quizzes_taken = VALUES(quizzes_taken),
               average_quiz_score = VALUES(average_quiz_score),
               sent_at = NOW()''',
            (user_id, today, lessons_completed, quizzes_taken, avg_score)
        )
    
    db.commit()
    cursor.close()

if __name__ == '__main__':
    # Optional: Start background scheduler
    # scheduler = BackgroundScheduler()
    # scheduler.add_job(schedule_reports, 'cron', day_of_week='0', hour=0)  # Weekly on Sunday
    # scheduler.start()
    
    app.run(host='0.0.0.0', port=5005, debug=True)
