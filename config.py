import os
from dotenv import load_dotenv

# Load local .env if present
load_dotenv()

# --- Core ---
SECRET_KEY = os.environ.get("SECRET_KEY", "unipath-secret-x7k-2026-!@#$%")
DEBUG = os.environ.get("DEBUG", "false").lower() == "true"

# --- Cloud / Vercel Detection ---
IS_VERCEL = bool(os.environ.get("VERCEL") or os.environ.get("AWS_LAMBDA_FUNCTION_NAME"))

# --- Database ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if IS_VERCEL:
    DATABASE_PATH = os.environ.get("DATABASE_PATH", "/tmp/opportunity_pulse.db")
    UPLOAD_FOLDER = os.environ.get("UPLOAD_FOLDER", "/tmp/uploads/resumes")
else:
    DATABASE_PATH = os.environ.get("DATABASE_PATH", os.path.join(BASE_DIR, "opportunity_pulse.db"))
    UPLOAD_FOLDER = os.environ.get("UPLOAD_FOLDER", os.path.join(BASE_DIR, "static", "uploads", "resumes"))

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
if os.path.dirname(DATABASE_PATH):
    os.makedirs(os.path.dirname(DATABASE_PATH), exist_ok=True)

# --- File Uploads ---
MAX_CONTENT_LENGTH = 5 * 1024 * 1024   # 5 MB max resume size
ALLOWED_EXTENSIONS = {"pdf"}

# --- Assessment ---
QUIZ_PASS_MARK = 7       # out of 10
QUIZ_TOTAL = 10
MINI_QUIZ_PASS = 2       # out of 3 for learning path

# --- Gemini AI ---
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")

# --- Scraping ---
SCRAPE_INTERVAL_HOURS = int(os.environ.get("SCRAPE_INTERVAL_HOURS", "4"))
REQUEST_DELAY_MIN = 1.0   # seconds
REQUEST_DELAY_MAX = 3.0
MAX_RETRIES = 3

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_2_1) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36 Edg/122.0.0.0",
    "Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.6099.210 Mobile Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36 OPR/108.0.0.0",
    "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:122.0) Gecko/20100101 Firefox/122.0",
]

# --- Admin Secret ---
ADMIN_SECRET_PATH = "pulse-command-x9"  # Hidden admin URL

# --- Roles ---
ROLES = ["student", "organizer", "recruiter", "admin"]
ROLE_LABELS = {
    "student": "Student",
    "organizer": "Event Organizer",
    "recruiter": "Company Recruiter",
    "admin": "Administrator",
}

# --- Categories ---
CATEGORIES = ["hackathon", "internship", "scholarship", "workshop", "job"]
CATEGORY_LABELS = {
    "hackathon": "Hackathon",
    "internship": "Internship",
    "scholarship": "Scholarship",
    "workshop": "Workshop",
    "job": "Job",
}

# --- Branches ---
BRANCHES = ["CSE", "ECE", "EEE", "IT", "ME", "CE", "Chemical", "Biotech", "MBA", "Other"]

# --- Years ---
YEARS = ["1st Year", "2nd Year", "3rd Year", "4th Year", "Postgraduate"]

# --- Interest Tags ---
INTEREST_TAGS = [
    "AI/ML", "Web Development", "Android/iOS", "Cybersecurity",
    "Data Science", "Cloud Computing", "Blockchain", "IoT",
    "Competitive Programming", "DevOps", "UI/UX Design", "Open Source",
    "Finance & Fintech", "Healthcare Tech", "Gaming", "Robotics",
]

# --- Prize Filters ---
PRIZE_FILTERS = [
    {"label": "Any Prize", "min": 0},
    {"label": "₹5,000+", "min": 5000},
    {"label": "₹25,000+", "min": 25000},
    {"label": "₹1,00,000+", "min": 100000},
    {"label": "₹5,00,000+", "min": 500000},
]
