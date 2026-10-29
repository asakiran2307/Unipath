# Unipath 🚀

**The Ultimate AI-Powered Student Professional Opportunity & Talent Ecosystem**

Built for verified opportunity discovery, automated scraping, skill testing, and student team formation.

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![Flask](<https://img.shields.io/badge/Framework-Flask%203.0-green.svg>)](https://flask.palletsprojects.com/)
[![AI](<https://img.shields.io/badge/AI-Google%20Gemini%202.5-orange.svg>)](https://ai.google.dev/)
[![Deployment](<https://img.shields.io/badge/Deploy-Vercel%20Serverless-black.svg>)](https://vercel.com/)

---

## 📖 Project Overview

**Unipath** is a unified, intelligent platform connecting students with hackathons, internships, scholarships, and job opportunities across the web. Powered by **Google Gemini AI**, it analyzes student resumes, verifies practical technical skills via timed dynamic quizzes, auto-generates personalized learning paths, and allows team formation and recruiter discovery.

### 🏗️ Tech Stack

* **Web Framework:** Flask 3 (WSGI Serverless Ready)
* **AI Engine:** Google Gemini 2.5 Flash via official Google GenAI SDK
* **Database:** SQLite (with serverless auto-initialization & cold-start auto-seeding)
* **Frontend:** Modern Glassmorphic CSS3, Vanilla JavaScript, Jinja2 Templates
* **Automation:** Requests, BeautifulSoup4, LXML, and APScheduler
* **Cloud Deployment:** Vercel Serverless Functions (`vercel.json` rewrites + `api/index.py`)

---

## 📂 Project Structure

```text
Unipath/
├── api/
│   └── index.py               # Vercel Serverless Entrypoint (WSGI handler)
├── scrapers/                  # Intelligent Anti-Bot Web Scrapers
│   ├── base_scraper.py        # User-Agent rotation & retry engine
│   ├── devfolio_scraper.py    # Devfolio & Devpost hackathons
│   ├── internshala_scraper.py # Student internships
│   └── news_rss_scraper.py    # Google News RSS live feed
├── services/                  # Business Logic & AI Services
│   ├── ai_service.py          # Google Gemini AI integration
│   ├── resume_parser.py       # PDF parsing & AI skill extraction
│   ├── quiz_engine.py         # Dynamic AI-generated MCQ quizzes
│   ├── learning_path.py       # Personalized 4-step skill roadmaps
│   ├── recommendation.py      # Personalized opportunity matching
│   └── scheduler.py           # Background scraper scheduler
├── static/                    # Frontend Assets (CSS, JS, Logos)
│   ├── css/style.css          # Glassmorphic UI design system
│   ├── js/app.js              # Interactive client features
│   └── logo.jpeg              # Brand identity
├── templates/                 # Jinja2 HTML Templates
│   ├── admin/                 # Admin management & social monitor
│   ├── organizer/             # Event posting & management
│   ├── recruiter/             # Talent board & applicant chat
│   └── student/               # Feed, profile, quiz, roadmap, teams
├── app.py                     # Main Flask Application
├── config.py                  # Dynamic cloud/local configuration
├── database.py                # Database models & queries
├── seed_data.py               # Pre-seeded demo users & opportunities
├── requirements.txt           # Production dependencies
├── vercel.json                # Vercel Serverless routing & rewrites
├── .env.example               # Environment template
└── README.md                  # Project documentation
```

---

## 🔑 Demo Login Credentials

The application auto-seeds with pre-configured accounts:

| Role                    | Email                  | Password             | Access / Notes                           |
| ----------------------- | ---------------------- | -------------------- | ---------------------------------------- |
| **Student**       | `student@pulse.ai`   | `Demo@123`         | Feed, AI Roadmap, Quiz, Profile          |
| **Organizer**     | `organizer@pulse.ai` | `Demo@123`         | Post & manage hackathons                 |
| **Recruiter**     | `recruiter@pulse.ai` | `Demo@123`         | Talent Board, candidate review           |
| **Administrator** | `admin@pulse.ai`     | `PulseAdmin#2026X` | Admin Dashboard at `/pulse-command-x9` |

---

## 🚀 Local Development Setup

1. **Clone the repository:**

   ```bash
   git clone https://github.com/asakiran2307/Unipath.git
   cd Unipath
   ```
2. **Create a virtual environment (optional but recommended):**

   ```bash
   python -m venv venv
   # Windows:
   venv\Scripts\activate
   # Linux/macOS:
   source venv/bin/activate
   ```
3. **Install dependencies:**

   ```bash
   pip install -r requirements.txt
   ```
4. **Configure environment:**
   Copy `.env.example` to `.env` and add your Google Gemini API key:

   ```bash
   cp .env.example .env
   ```
5. **Start the application:**

   ```bash
   python app.py
   ```

   Open [http://127.0.0.1:5000](http://127.0.0.1:5000) in your browser.

---

## ☁️ Vercel Cloud Deployment

This project is fully configured for zero-config Vercel Serverless deployment using `vercel.json` and `api/index.py`.

### Deploy via Vercel Web Dashboard:

1. Push this repository to GitHub.
2. Go to [vercel.com/new](https://vercel.com/new) and import `asakiran2307/Unipath`.
3. In **Environment Variables**, add:
   * `GEMINI_API_KEY`: Your Google Gemini API Key
   * `SECRET_KEY`: Any secure random secret string
4. Click **Deploy**. Vercel will automatically build and deploy your Flask serverless function!

### Deploy via Vercel CLI:

```bash
npm i -g vercel
vercel
```
