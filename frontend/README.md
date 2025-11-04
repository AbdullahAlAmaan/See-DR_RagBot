# See-DR RAGBot Frontend

Simple HTML/CSS/JS frontend for the See-DR RAGBot, designed for Vercel deployment.

## Setup

1. Update `app.js` to set your API URL:
   ```javascript
   const API_URL = 'https://your-api-url.vercel.app';
   ```

2. Or set it via environment variable in Vercel:
   - Go to your Vercel project settings
   - Add environment variable: `API_URL`
   - Value: Your FastAPI backend URL

## Deployment to Vercel

1. Install Vercel CLI (if not already installed):
   ```bash
   npm i -g vercel
   ```

2. Deploy:
   ```bash
   cd frontend
   vercel
   ```

   Or connect your GitHub repo to Vercel and deploy automatically.

## Local Development

1. Start your FastAPI backend:
   ```bash
   uvicorn see_dr_ragbot.api.main:app --reload --port 8000
   ```

2. Serve the frontend (using Python's http.server):
   ```bash
   cd frontend
   python3 -m http.server 3000
   ```

3. Open http://localhost:3000

## Features

- ✅ Query interface
- ✅ Citation links with smooth scrolling
- ✅ Conversation history (stored in localStorage)
- ✅ Responsive design
- ✅ Loading states
- ✅ Error handling

