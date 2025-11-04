# ⚡ Quick Start: Deploy to Vercel

## 🎯 3-Step Deployment

### Step 1: Prepare (5 minutes)
```bash
# Run preparation script
./scripts/prepare_vercel_deploy.sh

# Commit everything
git add .
git commit -m "Ready for Vercel deployment"
git push
```

### Step 2: Deploy (2 minutes)

**Via Vercel Dashboard:**
1. Go to [vercel.com](https://vercel.com) → New Project
2. Import your GitHub repo
3. Settings:
   - Framework: **Other**
   - Root Directory: `./`
   - Build Command: `echo "No build"`
   - Output Directory: `frontend`
4. Environment Variables:
   - Add `GEMINI_API_KEY` = your key
5. Click **Deploy**

**Or via CLI:**
```bash
npm i -g vercel
vercel login
vercel
vercel env add GEMINI_API_KEY  # Enter your key
vercel --prod
```

### Step 3: Configure (1 minute)

After deployment, you'll get URLs like:
- Frontend: `https://your-project.vercel.app`
- API: `https://your-project.vercel.app/api`

Update `frontend/config.js`:
```javascript
window.API_URL = 'https://your-project.vercel.app/api';
```

Commit and push, or redeploy.

## ✅ That's It!

Your RAG bot is now live at `https://your-project.vercel.app`

## 📋 What's Included

- ✅ Vector store (18MB - well under 50MB limit)
- ✅ FastAPI backend as serverless functions
- ✅ HTML/CSS/JS frontend
- ✅ CORS configured
- ✅ All citations and history features

## 🔍 Verify Deployment

1. **Frontend**: `https://your-project.vercel.app`
2. **API Docs**: `https://your-project.vercel.app/api/docs`
3. **Test Query**: Ask a question in the UI

## 📚 Full Documentation

See `VERCEL_DEPLOYMENT_GUIDE.md` for detailed instructions.

