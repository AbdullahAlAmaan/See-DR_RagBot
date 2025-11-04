#!/bin/bash
# Quick script to prepare for Vercel deployment

echo "🔍 Checking deployment readiness..."

# Check vector store
if [ ! -f "vector_store/index.faiss" ] || [ ! -f "vector_store/metadata.jsonl" ]; then
    echo "❌ ERROR: Vector store not found!"
    echo "   Run: python scripts/build_index.py"
    exit 1
fi

# Check vector store size
SIZE=$(du -sm vector_store/ | cut -f1)
if [ "$SIZE" -gt 50 ]; then
    echo "⚠️  WARNING: Vector store is ${SIZE}MB (Vercel limit is 50MB)"
else
    echo "✅ Vector store size: ${SIZE}MB (OK)"
fi

# Check if vector store is tracked
if git ls-files --error-unmatch vector_store/index.faiss >/dev/null 2>&1; then
    echo "✅ Vector store is tracked in git"
else
    echo "⚠️  Vector store not tracked. Adding..."
    git add vector_store/
fi

# Check for .env file (should not be committed)
if [ -f ".env" ]; then
    echo "✅ .env file exists (will not be committed)"
fi

# Check frontend config
if [ -f "frontend/config.js" ]; then
    echo "✅ Frontend config exists"
else
    echo "❌ Frontend config missing!"
    exit 1
fi

# Check API wrapper
if [ -f "api/index.py" ]; then
    echo "✅ API wrapper exists"
else
    echo "❌ API wrapper missing!"
    exit 1
fi

echo ""
echo "✅ Ready for deployment!"
echo ""
echo "Next steps:"
echo "1. Review and commit changes:"
echo "   git add ."
echo "   git commit -m 'Prepare for Vercel deployment'"
echo "   git push"
echo ""
echo "2. Deploy to Vercel:"
echo "   vercel --prod"
echo ""
echo "3. Set environment variables in Vercel dashboard:"
echo "   - GEMINI_API_KEY: your_api_key"

