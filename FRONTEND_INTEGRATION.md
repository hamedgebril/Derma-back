# Frontend Integration Guide

Complete guide for integrating with the Dermavision Backend API.

> **Backend Documentation**: [README.md](README.md) | **Arabic Version**: [README_AR.md](README_AR.md)

## Base URLs

- **Local Development**: `http://localhost:8000`
- **Production**: `https://your-api-domain.com`

## CORS Configuration

The backend accepts requests from:
- `http://localhost:5173` (Vite dev server)
- `https://ai-front-beta-ashy.vercel.app` (Production frontend)

To add additional origins, update `CORS_ORIGINS` in the backend `.env` file and restart the server.

---

## Normalized Diagnosis API Contract

All three diagnosis endpoints now return a unified, consistent response shape. This was a deliberate fix to resolve frontend/backend integration failures caused by inconsistent response structures.

The following fields are guaranteed on every diagnosis-related response:

| Field | Type | Description |
|---|---|---|
| `predicted_label` | string | Top predicted disease type |
| `confidence` | float (0–1) | Confidence score |
| `image_quality_score` | int (0–100) | Image quality score |
| `image_quality_label` | string | Quality label (Excellent, Good, Fair, Poor, Very Poor) |

> Note: `"healty"` may appear as a `predicted_label` value — this is the label as stored in the trained model weights and is returned as-is.

---

## Authentication

### Overview

The backend supports two modes via the `AUTH_REQUIRED` environment variable:

- **Development** (`AUTH_REQUIRED=False`): No authentication required, uses default user_id=1
- **Production** (`AUTH_REQUIRED=True`): JWT required for all protected endpoints

### Signup

**`POST /api/v1/auth/signup`**

Request:
```json
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

Errors: `400` email/username taken, `422` invalid format

### Login

**`POST /api/v1/auth/login`**

Request:
```json
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

Errors: `401` wrong credentials, `403` inactive account

### Using Protected Endpoints

```
Authorization: Bearer <access_token>
```

Token expiry: 60 minutes by default (configurable on backend).

---

## Diagnosis Endpoints

### POST /api/v1/diagnosis

Create a new diagnosis from an uploaded image.

**Request**: `multipart/form-data`

| Parameter | Type | Required | Description |
|---|---|---|---|
| `file` | file | yes | Image file (JPG, PNG, HEIC, max 10MB) |
| `top_k` | query int | no | Number of predictions (default: 3) |

**Response (201)**:
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

Field reference:
- `predicted_label` — top predicted disease type
- `confidence` — confidence score (0–1)
- `top_k` — array of top predictions, each with `label` and `confidence`
- `image_quality_score` — image quality score (0–100)
- `image_quality_label` — quality label string
- `analysis_id` — database ID for this diagnosis; use this to retrieve it later

Errors: `400` invalid file, `401` auth required, `422` bad request, `500` server/model error

---

### GET /api/v1/history

Get the authenticated user's diagnosis history.

**Query Parameters**:
- `limit` (optional, default: 20) — number of records to return

**Response (200)**:
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
    },
    {
      "id": 122,
      "predicted_label": "healty",
      "confidence": 0.88,
      "image_quality_score": 90,
      "image_quality_label": "Excellent",
      "created_at": "2026-02-21T15:20:00Z"
    }
  ],
  "total": 2,
  "limit": 20
}
```

Each item in `analyses` contains: `id`, `predicted_label`, `confidence`, `image_quality_score`, `image_quality_label`, `created_at`.

Errors: `401` auth required, `500` server error

---

### GET /api/v1/diagnosis/{analysis_id}

Retrieve a specific diagnosis by its ID.

**Path Parameters**:
- `analysis_id` — the `analysis_id` returned from `POST /api/v1/diagnosis`

**Response (200)**:
```json
{
  "id": 123,
  "predicted_label": "psoriasis",
  "confidence": 0.92,
  "all_predictions": [
    {
      "disease_type": "psoriasis",
      "probability": 0.92,
      "confidence_percentage": 92.0,
      "rank": 1
    },
    {
      "disease_type": "tinea circinata",
      "probability": 0.05,
      "confidence_percentage": 5.0,
      "rank": 2
    }
  ],
  "image_quality_score": 85,
  "image_quality_label": "Good",
  "created_at": "2026-02-22T10:30:00Z"
}
```

`all_predictions` items contain: `disease_type`, `probability` (0–1), `confidence_percentage` (0–100), `rank`.

Errors: `401` auth required, `404` not found, `500` server error

---

## JavaScript / Axios Examples

### Setup

```javascript
import axios from 'axios';

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000',
  timeout: 30000,
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});
```

### Auth

```javascript
export const signup = async (email, username, password) => {
  const response = await api.post('/api/v1/auth/signup', { email, username, password });
  return response.data;
};

export const login = async (email, password) => {
  const response = await api.post('/api/v1/auth/login', { email, password });
  localStorage.setItem('access_token', response.data.access_token);
  return response.data;
};

export const logout = () => localStorage.removeItem('access_token');
```

### Diagnosis

```javascript
export const analyzeImage = async (file) => {
  const formData = new FormData();
  formData.append('file', file);
  const response = await api.post('/api/v1/diagnosis', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return response.data;
  // response.data.analysis_id — save this for later retrieval
};

export const getDiagnosisById = async (analysisId) => {
  const response = await api.get(`/api/v1/diagnosis/${analysisId}`);
  return response.data;
};

export const getHistory = async (limit = 20) => {
  const response = await api.get(`/api/v1/history?limit=${limit}`);
  return response.data;
  // response.data.analyses — array of history items
};
```

### React Component Example

```jsx
import { useState } from 'react';
import { analyzeImage } from './api';

function DiagnosisUpload() {
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  const handleFileChange = (e) => {
    const selected = e.target.files[0];
    if (!selected) return;

    const validTypes = ['image/jpeg', 'image/jpg', 'image/png', 'image/heic'];
    if (!validTypes.includes(selected.type)) {
      setError('Please select a JPG, PNG, or HEIC image');
      return;
    }
    if (selected.size > 10 * 1024 * 1024) {
      setError('File size must be less than 10MB');
      return;
    }
    setFile(selected);
    setError(null);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!file) return;
    setLoading(true);
    try {
      const data = await analyzeImage(file);
      setResult(data);
    } catch (err) {
      setError(err.response?.data?.detail || 'Analysis failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <form onSubmit={handleSubmit}>
        <input type="file" accept=".jpg,.jpeg,.png,.heic" onChange={handleFileChange} />
        <button type="submit" disabled={!file || loading}>
          {loading ? 'Analyzing...' : 'Analyze Image'}
        </button>
      </form>

      {error && <p className="error">{error}</p>}

      {result && (
        <div>
          <p>Predicted: {result.predicted_label}</p>
          <p>Confidence: {(result.confidence * 100).toFixed(1)}%</p>
          <p>Image Quality: {result.image_quality_label} ({result.image_quality_score}/100)</p>
          <ul>
            {result.top_k.map((pred, i) => (
              <li key={i}>{pred.label}: {(pred.confidence * 100).toFixed(1)}%</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
```

---

## Error Handling

All errors follow this structure:
```json
{
  "detail": "Error message describing what went wrong"
}
```

### HTTP Status Codes

| Code | Meaning |
|---|---|
| 200 | OK |
| 201 | Created |
| 400 | Bad request (invalid file format/size) |
| 401 | Unauthorized (missing/invalid token) |
| 403 | Forbidden (inactive account) |
| 404 | Not found |
| 422 | Validation error |
| 500 | Server error |

```javascript
try {
  const data = await analyzeImage(file);
} catch (error) {
  const status = error.response?.status;
  const message = error.response?.data?.detail || 'An error occurred';

  if (status === 401) {
    // redirect to login
  } else if (status === 400) {
    // show file validation message
  } else {
    // show generic error
  }
}
```

---

## Troubleshooting

### CORS errors
- Add your frontend URL to `CORS_ORIGINS` in the backend `.env` and restart the server
- Don't mix `localhost` and `127.0.0.1` — pick one and be consistent

### File upload returns 400 or 422
- Allowed formats: JPG, PNG, HEIC only
- Max size: 10MB
- Use `FormData` and set `Content-Type: multipart/form-data`
- Field name must be `file`

### 401 Unauthorized
- Check `AUTH_REQUIRED` setting on the backend
- Verify the token is stored and sent in the `Authorization: Bearer <token>` header
- Tokens expire after 60 minutes by default — re-login if expired

### Response fields missing or mismatched
- Ensure you are hitting the updated backend (the normalized contract fix)
- Verify the backend version by checking `GET /api/v1/ready`
- All three endpoints (`POST /diagnosis`, `GET /history`, `GET /diagnosis/{id}`) now consistently return `predicted_label`, `confidence`, `image_quality_score`, `image_quality_label`
- If you see old fields like `top_prediction`, `diagnosis_id`, or nested `image_quality` objects, you are hitting an outdated backend version

### Slow responses
- Increase axios timeout for file uploads (30s recommended)
- Use smaller images where possible (still ≥512px for best quality score)

---

## Health Check

Before integration, verify the backend is ready:

```javascript
const checkHealth = async () => {
  const response = await axios.get('http://localhost:8000/api/v1/ready');
  console.log('Ready:', response.data.ready);
  console.log('ML model:', response.data.checks.ml_model.ready);
  console.log('Database:', response.data.checks.database.ready);
};
```

---

## Integration Checklist

- [ ] Configure `VITE_API_URL` (local: `http://localhost:8000`, production: your domain)
- [ ] Implement signup/login and store JWT token
- [ ] Add `Authorization: Bearer <token>` header to protected requests
- [ ] Use `FormData` for file uploads with field name `file`
- [ ] Validate file format and size before upload
- [ ] Read `analysis_id` from POST response for later retrieval
- [ ] Use `analyses` array from history response
- [ ] Handle loading states and errors for all API calls
- [ ] Test with both development and production auth modes

---

## API Documentation

Interactive Swagger UI is available when the backend is running:
- Local: http://localhost:8000/docs

## Related Documentation

- **README.md** — Backend developer guide
- **README_AR.md** — Arabic version
- **docs_archive/** — Historical documentation (archived)
