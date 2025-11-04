# Vercel Deployment Guide for See-DR RAGBot

## 🎯 Deployment Strategy

This guide deploys your Gemini RAG Bot to Vercel with:
- **Frontend**: Static HTML/CSS/JS (in `frontend/`)
- **Backend**: FastAPI as serverless functions (in `api/`)
- **Vector Store**: FAISS index files (included in deployment, <25MB recommended)

## 📋 Prerequisites

1. ✅ Vector store built and ready (`vector_store/index.faiss` and `vector_store/metadata.jsonl`)
2. ✅ Gemini API key
3. ✅ Vercel account (free tier works)
4. ✅ GitHub repository

## 🗂️ Project Structure for Vercel

```
See-DR_RagBot/
├── api/
│   ├── index.py              # Vercel serverless function entry point
│   └── requirements.txt      # Python dependencies for Vercel
├── frontend/
│   ├── index.html
│   ├── app.js
│   ├── styles.css
│   ├── config.js
│   └── vercel.json
├── see_dr_ragbot/            # Your Python package
├── vector_store/             # ✅ Keep this (FAISS index)
│   ├── index.faiss
│   └── metadata.jsonl
├── config.yaml
├── vercel.json               # Root Vercel config
└── .gitignore                # Excludes PDFs, keeps vector_store
```

## 🚀 Step-by-Step Deployment

### Step 1: Prepare Your Repository

1. **Ensure vector store is committed:**
   ```bash
   # Check if vector store files exist
   ls -lh vector_store/
   
   # If they're gitignored, temporarily un-ignore them
   # The .gitignore has been updated to keep vector_store/
   ```

2. **Update frontend config:**
   Edit `frontend/config.js` and set your API URL (or leave as localhost for now, we'll set it after deployment):
   ```javascript
   // Will be set via environment variable in Vercel
   window.API_URL = window.API_URL || 'http://localhost:8000';
   ```

3. **Commit everything:**
   ```bash
   git add .
   git commit -m "Prepare for Vercel deployment"
   git push origin main
   ```

### Step 2: Deploy to Vercel

#### Option A: Via Vercel Dashboard (Recommended)

1. Go to [vercel.com](https://vercel.com) and sign in
2. Click **"Add New Project"**
3. Import your GitHub repository
4. Configure:
   - **Framework Preset**: Other
   - **Root Directory**: `./` (root)
   - **Build Command**: `echo "No build needed"`
   - **Output Directory**: `frontend`

5. **Set Environment Variables:**
   - `GEMINI_API_KEY`: Your Gemini API key
   - `VECTOR_STORE_DIR`: `vector_store` (optional, defaults from config.yaml)

6. Click **"Deploy"**

#### Option B: Via Vercel CLI

1. **Install Vercel CLI:**
   ```bash
   npm i -g vercel
   ```

2. **Login:**
   ```bash
   vercel login
   ```

3. **Deploy:**
   ```bash
   vercel
   ```

4. **Set environment variables:**
   ```bash
   vercel env add GEMINI_API_KEY
   # Paste your API key when prompted
   ```

5. **Deploy to production:**
   ```bash
   vercel --prod
   ```

### Step 3: Configure API URL

After deployment, Vercel will give you URLs like:
- Frontend: `https://your-project.vercel.app`
- API: `https://your-project.vercel.app/api`

1. **Update frontend config:**
   - Option 1: Edit `frontend/config.js` and set:
     ```javascript
     window.API_URL = 'https://your-project.vercel.app/api';
     ```
   - Option 2: Set environment variable in Vercel dashboard (if using build-time injection)

2. **Redeploy if needed**

### Step 4: Test Deployment

1. Visit your frontend URL: `https://your-project.vercel.app`
2. Try a query: "What are the main screening methods for diabetic retinopathy?"
3. Check Vercel logs: `vercel logs --follow`

## ⚙️ Environment Variables

Set these in Vercel Dashboard → Settings → Environment Variables:

| Variable | Value | Required |
|----------|-------|----------|
| `GEMINI_API_KEY` | Your Gemini API key | ✅ Yes |
| `VECTOR_STORE_DIR` | `vector_store` | Optional (defaults from config.yaml) |

## 📦 What Gets Deployed

### ✅ Included (Deployed)
- `vector_store/` directory (FAISS index + metadata)
- All Python code in `see_dr_ragbot/`
- Frontend files in `frontend/`
- Configuration files

### ❌ Excluded (Not Deployed)
- `*.pdf` files (raw PDFs)
- `See_DR_bot/` directory (source PDFs)
- `data/processed/` (processed chunks)
- `.venv/` (virtual environment)
- `.env` files

## 🔧 Troubleshooting

### Issue: "Vector store not found"
**Solution**: Ensure `vector_store/` is committed to git:
```bash
git add vector_store/
git commit -m "Add vector store"
git push
```

### Issue: "Module not found" errors
**Solution**: Check that `api/requirements.txt` includes all dependencies

### Issue: "Function timeout"
**Solution**: Increase timeout in `vercel.json`:
```json
"functions": {
  "api/index.py": {
    "maxDuration": 60,  // Increase from 30
    "memory": 2048      // Increase memory if needed
  }
}
```

### Issue: CORS errors
**Solution**: Add CORS middleware to FastAPI (already should be working, but verify):
```python
from fastapi.middleware.cors import CORSMiddleware
app.add_middleware(CORSMiddleware, allow_origins=["*"])
```

### Issue: Vector store too large
**Solution**: 
- Vercel has a 50MB limit for serverless functions
- If your vector store is too large:
  1. Compress/reduce embedding dimensions
  2. Use external vector DB (Pinecone, Weaviate, etc.)
  3. Split into multiple smaller indices

## 🔄 Updating Vector Store

When you add new PDFs:

1. **Local:**
   ```bash
   # Process new PDFs
   python scripts/build_index.py
   ```

2. **Commit and push:**
   ```bash
   git add vector_store/
   git commit -m "Update vector store with new documents"
   git push
   ```

3. **Vercel auto-deploys** (if connected to GitHub) or manually:
   ```bash
   vercel --prod
   ```

## 📊 Monitoring

- **Vercel Dashboard**: View deployment logs, function invocations
- **Function Logs**: `vercel logs <project-name> --follow`
- **Analytics**: Vercel Analytics (if enabled)

## 🎯 Recommended Architecture

For production, consider:

1. **Frontend**: Vercel (free, fast CDN)
2. **Backend**: Vercel Serverless Functions (or Railway/Render for more control)
3. **Vector Store**: 
   - Small (<25MB): Include in deployment ✅ (current setup)
   - Large (>25MB): Use Pinecone, Weaviate, or Supabase pgvector

## 📝 Notes

- Free tier: 100GB bandwidth, 100 hours function execution
- Serverless functions have cold starts (first request may be slower)
- Vector store is loaded on each function invocation (consider caching)
- For better performance, use Vercel Edge Functions or external vector DB

## ✅ Checklist

- [ ] Vector store built and committed
- [ ] Frontend config updated with API URL
- [ ] Environment variables set in Vercel
- [ ] Repository pushed to GitHub
- [ ] Vercel project created and connected
- [ ] Initial deployment successful
- [ ] Test query works
- [ ] Citations display correctly
- [ ] History persists (localStorage)

## 🆘 Support

If you encounter issues:
1. Check Vercel logs: `vercel logs`
2. Test API directly: `curl https://your-project.vercel.app/api/query -X POST -H "Content-Type: application/json" -d '{"query":"test"}'`
3. Verify environment variables are set
4. Ensure vector store files are in the deployment

