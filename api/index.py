import os
import sys
from urllib.parse import parse_qs

# Ensure project root directory is in sys.path
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from app import app

class VercelPathCorrectionMiddleware:
    """
    WSGI middleware that restores the original client requested path
    from Vercel's rewrite query parameter (?path=$1) or headers.
    """
    def __init__(self, wsgi_app):
        self.wsgi_app = wsgi_app

    def __call__(self, environ, start_response):
        query_string = environ.get('QUERY_STRING', '')
        
        # 1. Check if Vercel passed path via ?path=$1
        if 'path=' in query_string:
            params = parse_qs(query_string)
            if 'path' in params:
                req_path = params['path'][0]
                environ['PATH_INFO'] = '/' + req_path.lstrip('/')
                return self.wsgi_app(environ, start_response)

        # 2. Check Vercel proxy headers
        raw_uri = (
            environ.get("HTTP_X_FORWARDED_PATH") or
            environ.get("HTTP_X_MATCHED_PATH") or
            environ.get("REQUEST_URI")
        )
        if raw_uri:
            clean = raw_uri.split("?")[0]
            if clean and not clean.startswith("/api/index"):
                environ['PATH_INFO'] = '/' + clean.lstrip('/')
                return self.wsgi_app(environ, start_response)

        # 3. Handle default fallback
        path_info = environ.get("PATH_INFO", "")
        if path_info in ("/api/index", "/api/index.py", "/api", "/api/"):
            environ["PATH_INFO"] = "/"
        elif path_info.startswith("/api/index/"):
            environ["PATH_INFO"] = "/" + path_info[len("/api/index/"):].lstrip("/")

        return self.wsgi_app(environ, start_response)

app.wsgi_app = VercelPathCorrectionMiddleware(app.wsgi_app)
application = app
