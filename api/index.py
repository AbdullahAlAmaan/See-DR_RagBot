"""
Vercel serverless function wrapper for FastAPI
"""
import sys
from pathlib import Path

# Add the parent directory to the path so we can import see_dr_ragbot
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Import the FastAPI app
from see_dr_ragbot.api.main import app

# Export as 'application' - Vercel's Python runtime convention
application = app
