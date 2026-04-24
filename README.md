# Dermavision Backend - Skin Disease Analysis API

Production-ready FastAPI backend for AI-powered skin disease detection and analysis.

> **النسخة العربية**: [README_AR.md](README_AR.md) | **Frontend Integration**: [FRONTEND_INTEGRATION.md](FRONTEND_INTEGRATION.md)

## Overview

Dermavision Backend is a REST API that provides:
- AI-powered skin disease diagnosis using EfficientNet-B4
- User authentication with JWT tokens
- Diagnosis history tracking
- Image quality assessment
- Secure file upload and storage

## Recent Updates

**Normalized Diagnosis API Contract (Latest Fix)**

The diagnosis API response shapes were inconsistent across endpoints, causing frontend/backend integration failures. This has been resolved. All three diagnosis endpoints now return a unified, normalized response using a dedicated mapper layer (`diagnosis_mapper.py`) and response models (`diagnosis_response.py`).

The following fields are now guaranteed across all diagnosis endpoints:
- `predicted_label` — top predicted disease type
- `confidence` — confidence score (0–1)
- `image_quality_score` — image quality score (0–100)
- `image_quality_label` — quality label string

Files added/updated as part of this fix:
- `app/api/v1/schemas/diagnosis_response.py` — unified response schemas
- `app/api/v1/mappers/diagnosis_mapper.py` — mapper layer normalizing service output
- `app/api/v1/endpoints/diagnosis.py` — all endpoints updated to use new models

## Architecture

```
API Layer (FastAPI) → Domain Layer (Business Logic) → Infrastructure Layer (DB, ML)
```

- `app/api/` — HTTP endpoints, request/response handling, middleware
- `app/domain/` — Business logic services (diagnosis, file management)
- `app/infrastructure/` — External integrations (database, ML model)
- `app/core/` — Configuration, security, logging, exceptions

## Requirements

- Python 3.11+
- 2GB+ free disk space (for ML model weights)
- SQLite (default) or PostgreSQL (production)

## Quick Setup

### 1. Install Dependencies

```bash
python -m venv venv

# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate

pip install -r requirements.txt
```

### 2. Setup Model Weights

Place the trained model file at:
```
app/infrastructure/ml/weights/skin_efficientnet_b4_9.pth
```

### 3. Configure Environment

```bash
cp .env.example .env
```

Key environment variables:
```bash
SECRET_KEY=your-secret-key-minimum-32-characters-change-in-production
AUTH_REQUIRED=False        # Set to True in production
DATABASE_URL=sqlite:///./skin_analysis.db
MODEL_PATH=./app/infrastructure/ml/weights/skin_efficientnet_b4_9.pth
MODEL_DEVICE=cpu           # or cuda
CORS_ORIGINS=["http://localhost:5173","https://your-frontend.vercel.app"]
```

### 4. Initialize Database

```bash
alembic upgrade head
```

Creates two tables:
- `users` — id, email, username, hashed_password, timestamps
- `diagnoses` — id, user_id, image_path, predictions, quality, timestamps

### 5. Start Server

```bash
# Development
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Production
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

## Environment Variables

```bash
# Application
ENVIRONMENT=development
DEBUG=False
APP_VERSION=1.0.0

# Security
SECRET_KEY=<generate-strong-key>
AUTH_REQUIRED=False        # True in production
ACCESS_TOKEN_EXPIRE_MINUTES=60

# Database
DATABASE_URL=sqlite:///./skin_analysis.db

# CORS
CORS_ORIGINS=["http://localhost:5173","https://your-frontend.vercel.app"]

# Storage
UPLOAD_DIR=./uploads
MAX_UPLOAD_SIZE=10485760   # 10MB
ALLOWED_EXTENSIONS=[".jpg",".jpeg",".png",".heic"]

# ML Model
MODEL_PATH=./app/infrastructure/ml/weights/skin_efficientnet_b4_9.pth
MODEL_DEVICE=cpu
TOP_K_PREDICTIONS=3
```

`AUTH_REQUIRED` controls authentication behavior:
- `False` (dev): Allows requests without tokens, uses default user_id=1
- `True` (prod): Requires valid JWT token for all protected endpoints

Generate a strong secret key:
```bash
python -c "import secrets; print(secrets.token_urlsafe(64))"
```

## Authentication

### Signup
```bash
POST /api/v1/auth/signup
Content-Type: application/json

{
  "email": "user@example.com",
  "username": "johndoe",
  "password": "securepassword123"
}
```

Response (201):
```json
{
  "id": 1,
  "email": "user@example.com",
  "username": "johndoe",
  "is_active": true,
  "created_at": "2026-02-22T10:30:00Z"
}
```

### Login
```bash
POST /api/v1/auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "securepassword123"
}
```

Response (200):
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

Use the token on protected endpoints:
```
Authorization: Bearer <access_token>
```

## API Endpoints

### Health & Status
- `GET /api/v1/health` — Basic health check
- `GET /api/v1/ready` — Readiness check (ML model + DB status)

### Authentication
- `POST /api/v1/auth/signup` — Register new user
- `POST /api/v1/auth/login` — Login and get JWT token

### Diagnosis (Protected*)
- `POST /api/v1/diagnosis` — Analyze skin disease from image
- `GET /api/v1/history?limit=20` — Get user's diagnosis history
- `GET /api/v1/diagnosis/{analysis_id}` — Get specific diagnosis by ID

*Protected endpoints require authentication only when `AUTH_REQUIRED=True`

## Diagnosis API Contract

All three diagnosis endpoints return a normalized, consistent response. The following fields are guaranteed on every diagnosis response:

| Field | Type | Description |
|---|---|---|
| `predicted_label` | string | Top predicted disease type |
| `confidence` | float (0–1) | Confidence score |
| `image_quality_score` | int (0–100) | Image quality score |
| `image_quality_label` | string | Quality label |

### POST /api/v1/diagnosis

Request: `multipart/form-data`, field `file` (JPG, PNG, HEIC, max 10MB)

Response (201):
```json
{
  "predicted_label": "psoriasis",
  "confidence": 0.92,
  "top_k": [
    { "label": "psoriasis", "confidence": 0.92 },
    { "label": "tinea circinata", "confidence": 0.05 },
    { "label": "healty", "confidence": 0.02 }
  ],
  "image_quality_score": 85,
  "image_quality_label": "Good",
  "analysis_id": 123
}
```

> Note: `"healty"` is the label as stored in the trained model weights. It is returned as-is.

### GET /api/v1/diagnosis/{analysis_id}

Response (200):
```json
{
  "id": 123,
  "predicted_label": "psoriasis",
  "confidence": 0.92,
  "all_predictions": [
    { "disease_type": "psoriasis", "probability": 0.92, "confidence_percentage": 92.0, "rank": 1 },
    { "disease_type": "tinea circinata", "probability": 0.05, "confidence_percentage": 5.0, "rank": 2 }
  ],
  "image_quality_score": 85,
  "image_quality_label": "Good",
  "created_at": "2026-02-22T10:30:00Z"
}
```

### GET /api/v1/history

Response (200):
```json
{
  "analyses": [
    {
      "id": 123,
      "predicted_label": "psoriasis",
      "confidence": 0.92,
      "image_quality_score": 85,
      "image_quality_label": "Good",
      "created_at": "2026-02-22T10:30:00Z"
    }
  ],
  "total": 1,
  "limit": 20
}
```

## ML Model

- **Architecture**: EfficientNet-B4 (via timm)
- **Input**: 380×380 pixels, ImageNet normalization
- **Classes**: MF, annular lichen, healty, psoriasis, tinea circinata, urticaria

### Image Quality Scoring
| Resolution | Score | Label |
|---|---|---|
| ≥1024px | 95 | Excellent |
| ≥512px | 85 | Good |
| ≥256px | 70 | Fair |
| ≥128px | 50 | Poor |
| <128px | 30 | Very Poor |

## Database Management

```bash
alembic upgrade head       # Apply all migrations
alembic downgrade -1       # Rollback one migration
alembic current            # Check current version
alembic revision --autogenerate -m "description"  # New migration
```

## Troubleshooting

**Model not loading**
```bash
# Verify file exists
ls -lh app/infrastructure/ml/weights/skin_efficientnet_b4_9.pth
```

**Authentication errors**
- Verify `SECRET_KEY` is set in `.env`
- Check `AUTH_REQUIRED` matches your environment
- Default token expiry is 60 minutes

**CORS errors**
- Add your frontend URL to `CORS_ORIGINS` in `.env` and restart

**Database errors**
```bash
alembic upgrade head
```

**File upload issues**
- Allowed formats: JPG, PNG, HEIC
- Max size: 10MB
- Content-Type must be `multipart/form-data`

## Testing

```bash
# Health check
curl http://localhost:8000/api/v1/ready

# Signup
curl -X POST "http://localhost:8000/api/v1/auth/signup" \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","username":"testuser","password":"test123"}'

# Login
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"test123"}'

# Diagnosis
TOKEN="your-jwt-token"
curl -X POST "http://localhost:8000/api/v1/diagnosis" \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@test_image.jpg"

# History
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/api/v1/history?limit=10"
```

## Production Deployment

### Pre-deployment Checklist

- [ ] `AUTH_REQUIRED=True`
- [ ] `ENVIRONMENT=production`, `DEBUG=False`
- [ ] Strong `SECRET_KEY` (64+ characters)
- [ ] Production `DATABASE_URL` (PostgreSQL recommended)
- [ ] `CORS_ORIGINS` updated with production frontend URL
- [ ] `alembic upgrade head` run
- [ ] HTTPS enabled

### Docker

```bash
docker build -t dermavision-api .

docker run -d \
  -p 8000:8000 \
  -e AUTH_REQUIRED=True \
  -e SECRET_KEY=your-secret-key \
  --name dermavision-api \
  dermavision-api
```

## Security Features

- bcrypt password hashing
- JWT token authentication
- Configurable token expiration
- File size and type validation
- CORS protection
- SQLAlchemy ORM (SQL injection protection)
- Pydantic input validation

## API Documentation

Interactive docs available when running:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Documentation

- **README.md** — Backend developer guide (this file)
- **FRONTEND_INTEGRATION.md** — Frontend integration guide
- **README_AR.md** — Arabic version
- **docs_archive/** — Historical documentation (archived)

## License

[Your License Here]
