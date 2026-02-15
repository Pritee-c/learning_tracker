import os

class Config:
    AUTH_SERVICE = os.getenv('AUTH_SERVICE', 'http://localhost:5001')
    COURSE_SERVICE = os.getenv('COURSE_SERVICE', 'http://localhost:5002')
    QUIZ_SERVICE = os.getenv('QUIZ_SERVICE', 'http://localhost:5003')
    PROGRESS_SERVICE = os.getenv('PROGRESS_SERVICE', 'http://localhost:5004')
    REPORT_SERVICE = os.getenv('REPORT_SERVICE', 'http://localhost:5005')
    ENVIRONMENT = os.getenv('ENVIRONMENT', 'development')
