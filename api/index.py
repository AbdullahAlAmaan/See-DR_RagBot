"""
Vercel serverless function wrapper for FastAPI
"""
import sys
import os
from pathlib import Path

# Add the parent directory to the path so we can import see_dr_ragbot
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Import the FastAPI app
from see_dr_ragbot.api.main import app

# Export the app for Vercel
handler = app
