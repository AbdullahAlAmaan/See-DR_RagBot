# 🚀 Vercel Deployment Checklist

## Pre-Deployment

- [ ] Vector store built (`vector_store/index.faiss` and `vector_store/metadata.jsonl` exist)
- [ ] Vector store size < 50MB (yours is ~18MB ✅)
- [ ] `.gitignore` updated to allow `vector_store/` 
- [ ] All code committed to git
- [ ] Gemini API key ready

## Deployment Steps

### 1. Commit Vector Store
```bash
# Check if vector_store is tracked
git status vector_store/

# If not tracked, add it:
git add vector_store/
git commit -m "Add vector store for deployment"
git push
```

### 2. Deploy to Vercel

#### Option A: Dashboard
1. Go to vercel.com → New Project
2. Import GitHub repo
3. Configure:
   - Framework: Other
   - Root: `./`
   - Build: `echo "No build"`
   - Output: `frontend`
4. Add env vars:
   - `GEMINI_API_KEY`: your key
5. Deploy

#### Option B: CLI
```bash
npm i -g vercel
vercel login
vercel
vercel env add GEMINI_API_KEY  # Enter your key
vercel --prod
```

### 3. Configure Frontend

After deployment, get your API URL (e.g., `https://your-project.vercel.app/api`)

Update `frontend/config.js`:
```javascript
window.API_URL = 'https://your-project.vercel.app/api';
```

Or set in Vercel environment variables if using build-time injection.

### 4. Test

- [ ] Frontend loads: `https://your-project.vercel.app`
- [ ] API responds: `https://your-project.vercel.app/api/docs`
- [ ] Query works: Test a search query
- [ ] Citations work: Click citation links
- [ ] History works: Check localStorage

## Post-Deployment

- [ ] Monitor Vercel logs for errors
- [ ] Test from different browsers/devices
- [ ] Verify CORS is working (if frontend on different domain)
- [ ] Check function execution time (should be < 10s)

## Troubleshooting

- **Vector store not found**: Ensure `vector_store/` is committed
- **Import errors**: Check `api/requirements.txt` has all dependencies
- **Timeout**: Increase `maxDuration` in `vercel.json`
- **CORS errors**: CORS middleware is already added

