# Learning Tracker - Microservices Application

A complete learning management system built with Flask microservices, MySQL, and ready for Docker & Kubernetes deployment.

## Architecture

**6 Microservices:**
1. **auth-service** (Port 5001) — User registration, login, JWT authentication
2. **course-service** (Port 5002) — Courses, modules, lessons management
3. **quiz-service** (Port 5003) — Quizzes, questions, attempt scoring
4. **progress-service** (Port 5004) — Track lesson/course completion
5. **report-service** (Port 5005) — Weekly progress reports
6. **gateway** (Port 5000) — API Gateway & request routing

**Database:** MySQL 8.0 with 14 tables

## Quick Start

### Prerequisites
- Docker & Docker Compose installed
- Python 3.10+ (for local development)

### Option 1: Docker Compose (Recommended for Local Dev)

```bash
cd learning-tracker
docker-compose up -d
```

This starts:
- MySQL database (port 3306)
- All 6 microservices
- API Gateway (port 5000)

Check service health:
```bash
curl http://localhost:5000/health
```

### Option 2: Local Development

1. **Set up MySQL:**
   ```bash
   mysql -u root -p < mysql-schema/schema.sql
   ```

2. **Set up each service:**
   ```bash
   cd auth-service
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   cp .env.example .env
   python app.py
   ```

   Repeat for other services in separate terminals (ports 5001-5005)

3. **Start the gateway:**
   ```bash
   cd gateway
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   cp .env.example .env
   python app.py
   ```

## API Endpoints

### Authentication
- `POST /api/auth/register` — Create user
- `POST /api/auth/login` — Login (returns JWT)
- `POST /api/auth/verify` — Verify token
- `GET /api/auth/me` — Get current user (requires Bearer token)

### Courses
- `GET /api/courses` — List all courses
- `GET /api/courses/<id>` — Get course details
- `POST /api/courses` — Create course (instructor only)
- `GET /api/courses/<id>/modules` — Get course modules
- `GET /api/modules/<id>/lessons` — Get module lessons

### Quizzes
- `GET /api/quizzes/lesson/<id>` — Get quiz with questions
- `POST /api/quizzes/<id>/attempts` — Submit quiz (returns score)
- `GET /api/quizzes/<id>/attempts/user` — Get user's attempts

### Progress
- `GET /api/progress` — Get all lesson progress
- `GET /api/progress/course/<id>` — Get course progress %
- `POST /api/progress/lesson/<id>/start` — Mark lesson started
- `POST /api/progress/lesson/<id>/complete` — Mark lesson completed

### Reports
- `GET /api/reports/week` — Get weekly stats
- `GET /api/reports/history` — Get all reports
- `POST /api/reports/generate` — Trigger report generation

## Example Workflow

```bash
# 1. Register
curl -X POST http://localhost:5000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"name":"John","email":"john@example.com","password":"123456"}'

# 2. Login
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"john@example.com","password":"123456"}'
# Copy the token from response

# 3. Get courses
curl http://localhost:5000/api/courses

# 4. Check progress
curl -H "Authorization: Bearer YOUR_TOKEN" \
  http://localhost:5000/api/progress/course/1
```

## Database Schema

Key tables:
- `users` — User accounts & roles
- `courses` — Learning courses
- `modules` — Course sections
- `lessons` — Individual lessons
- `progress` — Lesson completion tracking
- `quizzes` — Quiz definitions
- `quiz_attempts` — User quiz attempts & scores
- `reports` — Weekly progress summaries

See [mysql-schema/schema.sql](mysql-schema/schema.sql) for full schema.

## Kubernetes Deployment

Services are ready for K8s. To deploy:

1. Build images:
   ```bash
   docker build -t learning-tracker/auth-service:1.0 ./auth-service
   docker build -t learning-tracker/course-service:1.0 ./course-service
   # ...repeat for other services
   ```

2. Push to registry (ECR, Docker Hub, etc.)

3. Deploy with Helm or kubectl manifests (coming soon)

## Configuration

Each service uses environment variables. Copy `.env.example` to `.env`:

```bash
SECRET_KEY=your-secret-key
DB_HOST=mysql
DB_PORT=3306
DB_USER=root
DB_PASSWORD=password
DB_NAME=learning_tracker
ENVIRONMENT=development
```

For production, use strong secrets and proper database credentials.

## Development

### Adding a new endpoint:
1. Edit the service's `app.py`
2. Reload the service
3. Update gateway's `app.py` if needed
4. Call via `http://localhost:5000/api/...`

### Database migrations:
1. Modify `mysql-schema/schema.sql`
2. Restart MySQL container: `docker-compose down && docker-compose up`

## Troubleshooting

**Services can't connect to MySQL:**
- Check MySQL is running: `docker ps | grep mysql`
- Check credentials in `.env`
- Wait for healthcheck: `docker logs learning-tracker-mysql`

**Port conflicts:**
- Change ports in `docker-compose.yml` or in `.env` files

**JWT token issues:**
- Ensure `SECRET_KEY` matches across all services
- Token expires after 24 hours

## Next Steps

1. ✅ Local development complete
2. → Deploy to EC2 using Docker Compose
3. → Set up Kubernetes cluster
4. → Create K8s manifests for all services
5. → Add frontend UI (React/Vue)
6. → Implement CI/CD pipeline

## License

MIT
