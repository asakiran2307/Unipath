import os
import sys

# Ensure project root directory is in sys.path
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

# Import the Flask application instance
from app import app

# Expose WSGI handler for Vercel
# Vercel's Python runtime looks for 'app' or 'application'
application = app
