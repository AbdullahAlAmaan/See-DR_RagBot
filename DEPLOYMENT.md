# Deployment Guide for See-DR RAGBot

## Important Note: Vercel Limitations

**Vercel is NOT suitable for Streamlit applications.** Vercel is designed for:
- Static sites
- Serverless functions (short-lived)
- Edge functions

Streamlit requires:
- A persistent Python server process
- Long-running connections
- WebSocket support

## Recommended Deployment Options

### Option 1: Streamlit Cloud (Recommended - Easiest & Free)

**Best for:** Quick deployment, free hosting, automatic updates

1. Push your code to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Sign in with GitHub
4. Click "New app"
5. Select your repository and branch
6. Set main file: `see_dr_ragbot/ui/app.py`
7. Add secrets:
   - `GEMINI_API_KEY`: Your Gemini API key
8. Click "Deploy"

**Pros:**
- Free tier available
- Automatic deployments on git push
- Easy setup
- Built for Streamlit

**Cons:**
- Limited customization
- Requires public GitHub repo (or paid private)

### Option 2: Railway.app

**Best for:** Full control, easy deployment, good free tier

1. Create account at [railway.app](https://railway.app)
2. New Project → Deploy from GitHub
3. Add environment variables:
   - `GEMINI_API_KEY`
4. Create `Procfile`:
   ```
   web: streamlit run see_dr_ragbot/ui/app.py --server.port $PORT --server.address 0.0.0.0
   ```
5. Railway auto-detects and deploys

**Pros:**
- Free tier ($5 credit/month)
- Easy deployment
- Supports both API and Streamlit
- Private repos OK

### Option 3: Render.com

**Best for:** Free tier, good documentation

1. Create account at [render.com](https://render.com)
2. New → Web Service
3. Connect GitHub repo
4. Build command: `pip install -r requirements.txt`
5. Start command: `streamlit run see_dr_ragbot/ui/app.py --server.port $PORT --server.address 0.0.0.0`
6. Add environment variables:
   - `GEMINI_API_KEY`

**Pros:**
- Free tier available
- Good documentation
- Auto-deploys

**Cons:**
- Free tier spins down after inactivity

### Option 4: Separate Deployment (Recommended for Production)

Deploy the **FastAPI backend** and **Streamlit frontend** separately:

#### Backend (FastAPI) - Can use Vercel
- Vercel supports FastAPI via serverless functions
- Create `api/index.py` wrapper
- Or use Railway/Render for backend

#### Frontend (Streamlit) - Use Streamlit Cloud
- Deploy Streamlit UI on Streamlit Cloud
- Update `API_URL` in `app.py` to point to your backend URL

## Deployment Steps (Streamlit Cloud)

1. **Prepare your repository:**
   ```bash
   git add .
   git commit -m "Prepare for deployment"
   git push
   ```

2. **Create requirements.txt** (already exists, but verify):
   - Ensure all dependencies are listed
   - Pin versions for stability

3. **Set up Streamlit Cloud:**
   - Go to share.streamlit.io
   - Connect GitHub
   - Select repository: `See-DR_RagBot`
   - Main file path: `see_dr_ragbot/ui/app.py`
   - Python version: 3.9+

4. **Add Secrets:**
   - `GEMINI_API_KEY`: Your API key
   - Any other environment variables needed

5. **Deploy:**
   - Click "Deploy"
   - Wait for build to complete
   - Your app will be live at `https://your-app-name.streamlit.app`

## Environment Variables Needed

- `GEMINI_API_KEY`: Required for Gemini API access

## Notes

- The FastAPI backend (`see_dr_ragbot/api/main.py`) needs to be running separately or deployed as a service
- For local development, run both:
  ```bash
  # Terminal 1: FastAPI
  uvicorn see_dr_ragbot.api.main:app --reload --port 8000
  
  # Terminal 2: Streamlit
  streamlit run see_dr_ragbot/ui/app.py --server.port 8501
  ```
- For production, consider deploying API to Railway/Render and Streamlit to Streamlit Cloud

