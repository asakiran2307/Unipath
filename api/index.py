import os
import sys

# Ensure project root directory is in sys.path
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from app import app

class VercelPathFixMiddleware:
    """
    Middleware ensuring that Vercel serverless rewrites 
    correctly pass the client requested path to Flask.
    """
    def __init__(self, wsgi_app):
        self.wsgi_app = wsgi_app

    def __call__(self, environ, start_response):
        # 1. Check if Vercel provided original requested path in headers
        raw_uri = (
            environ.get("HTTP_X_FORWARDED_PATH") or
            environ.get("HTTP_X_MATCHED_PATH") or
            environ.get("HTTP_X_NOW_ROUTE_MATCHES") or
            environ.get("REQUEST_URI")
        )
        
        path_info = environ.get("PATH_INFO", "")
        
        if raw_uri:
            # Strip query string if present
            clean_path = raw_uri.split("?")[0]
            if clean_path and not clean_path.startswith("/api/index"):
                environ["PATH_INFO"] = clean_path
                return self.wsgi_app(environ, start_response)
        
        # 2. If path_info was rewritten to /api/index or /api/index.py
        if path_info in ("/api/index.py", "/api/index", "/api", "/api/"):
            environ["PATH_INFO"] = "/"
        elif path_info.startswith("/api/index.py/"):
            environ["PATH_INFO"] = path_info[len("/api/index.py"):]
        elif path_info.startswith("/api/index/"):
            environ["PATH_INFO"] = path_info[len("/api/index"):]

        return self.wsgi_app(environ, start_response)

# Apply middleware
app.wsgi_app = VercelPathFixMiddleware(app.wsgi_app)
application = app
