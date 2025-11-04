# Vercel Deployment Guide

This guide explains how to deploy both the frontend and backend to Vercel.

## Architecture

- **Frontend**: Static HTML/CSS/JS in `frontend/` directory
- **Backend**: FastAPI as serverless functions (if deploying to Vercel) OR use Railway/Render separately

## Option 1: Deploy Frontend Only to Vercel (Recommended)

Deploy the frontend to Vercel and host the backend separately (Railway, Render, etc.)

### Frontend Deployment

1. **Create a new Vercel project:**
   ```bash
   cd frontend
   vercel
   ```

2. **Set environment variables in Vercel dashboard:**
   - Go to your project settings → Environment Variables
   - Add: `VITE_API_URL` = `https://your-backend-url.railway.app` (or wherever your API is)

3. **Update `app.js` to use the environment variable:**
   The frontend code already supports this. You may need to rebuild if using Vite.

### Backend Deployment (Separate)

Deploy the FastAPI backend to:
- **Railway.app** (recommended)
- **Render.com**
- **Fly.io**

See `DEPLOYMENT.md` for backend deployment instructions.

---

## Option 2: Deploy Both to Vercel (More Complex)

Vercel supports Python serverless functions, but it's more complex for FastAPI apps with large dependencies.

### Backend Setup

1. Create `api/index.py`:
```python
from vercel.app import app
import sys
import os

# Add parent to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from see_dr_ragbot.api.main import app as fastapi_app

# Export for Vercel
app = fastapi_app
```

2. Create `vercel.json` in root:
```json
{
  "version": 2,
  "builds": [
    {
      "src": "api/index.py",
      "use": "@vercel/python"
    }
  ],
  "routes": [
    {
      "src": "/api/(.*)",
      "dest": "api/index.py"
    },
    {
      "src": "/(.*)",
      "dest": "frontend/$1"
    }
  ]
}
```

3. **Note**: You'll need to upload your `vector_store/` directory or use a cloud storage solution (S3, etc.) since Vercel serverless functions have limited storage.

---

## Quick Start (Frontend Only)

1. **Deploy frontend:**
   ```bash
   cd frontend
   vercel
   ```

2. **Set environment variable:**
   - In Vercel dashboard → Settings → Environment Variables
   - Add: `VITE_API_URL` = `https://your-backend-url.com`

3. **Deploy backend separately:**
   - Use Railway.app or Render.com
   - Set `GEMINI_API_KEY` environment variable
   - Note the backend URL

4. **Update frontend environment variable** with your backend URL

---

## Environment Variables

### Frontend (Vercel)
- `VITE_API_URL`: Backend API URL (e.g., `https://your-api.railway.app`)

### Backend (Railway/Render)
- `GEMINI_API_KEY`: Your Gemini API key

---

## Troubleshooting

### CORS Issues
If you get CORS errors, add CORS middleware to your FastAPI backend:
```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### API URL Not Working
- Check that your backend is running and accessible
- Verify the environment variable is set correctly in Vercel
- Check browser console for errors

---

## Recommended Approach

**For production, I recommend:**
1. **Frontend**: Deploy to Vercel (free, fast CDN)
2. **Backend**: Deploy to Railway.app or Render.com (better for Python/FastAPI)
3. **Vector Store**: Upload to cloud storage (S3, etc.) or include in deployment

This gives you the best of both worlds: fast static frontend hosting + reliable backend hosting.

