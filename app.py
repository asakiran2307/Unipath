"""Opportunity Pulse – Main Flask Application"""
import json, os, logging
from datetime import datetime, date
from functools import wraps
from werkzeug.utils import secure_filename

from flask import (
    Flask, render_template, request, redirect, url_for,
    session, flash, jsonify, abort, send_from_directory
)
from werkzeug.security import generate_password_hash, check_password_hash

from config import (SECRET_KEY, DEBUG, ADMIN_SECRET_PATH, CATEGORIES, BRANCHES,
                    YEARS, INTEREST_TAGS, PRIZE_FILTERS, ROLE_LABELS,
                    UPLOAD_FOLDER, MAX_CONTENT_LENGTH, ALLOWED_EXTENSIONS,
                    QUIZ_PASS_MARK)
from database import (
    init_db, create_user, get_user_by_email, get_user_by_id,
    update_user_profile, get_all_users, toggle_user_active,
    insert_opportunity, get_opportunities, get_opportunity_by_id,
    get_opportunities_by_user, update_opportunity_status, delete_opportunity,
    get_pending_opportunities, mark_ai_analyzed,
    save_opportunity, unsave_opportunity, get_saved_ids, get_saved_opportunities,
    log_scrape, get_scrape_logs, get_stats,
    get_notifications, add_notification, mark_notifications_read,
    get_social_credentials, get_all_social_credentials, save_social_credentials,
    # Assessment / Resume / Talent
    save_resume, get_resume, has_resume,
    save_assessment_questions, get_pending_assessment, complete_assessment,
    get_latest_assessment, get_assessment_attempt_count,
    mark_video_watched, complete_learning_module,
    get_learning_progress, count_completed_modules,
    get_talent_board,
    # Team Pool
    create_team_pool, get_team_pools, get_team_pool, get_my_team_pools,
    request_join_pool, get_pool_requests, respond_to_request,
    has_requested_pool, close_team_pool,
    # Chat / Messaging
    send_message, get_conversation, get_new_messages, get_chat_list, get_unread_count,
    # Ads
    create_ad, get_ads, update_ad_status, delete_ad
)
from services.recommendation import get_personalized_feed
from services.scheduler import start_scheduler, trigger_now, trigger_social_now, trigger_core_now

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = SECRET_KEY
app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Jinja enumerate filter
app.jinja_env.filters['enumerate'] = enumerate
app.url_map.strict_slashes = False

# Auto-initialize database on startup (crucial for Serverless / Vercel deployment)
try:
    init_db()
    from database import get_stats as _gs
    if _gs().get("total_opportunities", 0) == 0:
        try:
            from seed_data import seed
            seed()
        except Exception as _seed_err:
            logger.warning(f"Auto-seed failed: {_seed_err}")
except Exception as _db_init_err:
    logger.warning(f"Database initialization notice: {_db_init_err}")


# ─── Helpers ──────────────────────────────────────────────────────────────────

def days_left(deadline_str):
    if not deadline_str:
        return None
    try:
        dl = datetime.strptime(str(deadline_str)[:10], "%Y-%m-%d").date()
        return (dl - date.today()).days
    except Exception:
        return None


def enrich_opps(opps):
    """Add days_left and deadline_label to each opportunity."""
    for o in opps:
        dl = days_left(o.get("deadline"))
        o["days_left"] = dl
        if dl is None:
            o["deadline_label"] = "Rolling"
            o["deadline_color"] = "muted"
        elif dl < 0:
            o["deadline_label"] = "Expired"
            o["deadline_color"] = "expired"
        elif dl == 0:
            o["deadline_label"] = "Last Day!"
            o["deadline_color"] = "red"
        elif dl <= 3:
            o["deadline_label"] = f"{dl}d left – Urgent!"
            o["deadline_color"] = "red"
        elif dl <= 7:
            o["deadline_label"] = f"{dl} days left"
            o["deadline_color"] = "amber"
        elif dl <= 30:
            o["deadline_label"] = f"{dl} days left"
            o["deadline_color"] = "green"
        else:
            o["deadline_label"] = f"{dl} days left"
            o["deadline_color"] = "teal"
    return opps


def current_user():
    uid = session.get("user_id")
    if not uid:
        return None
    return get_user_by_id(uid)


def get_profile():
    user = current_user()
    if not user:
        return {}
    try:
        return json.loads(user.get("profile") or "{}")
    except Exception:
        return {}


# ─── Decorators ───────────────────────────────────────────────────────────────

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("user_id"):
            flash("Please log in to continue.", "warning")
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated


def role_required(*roles):
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if not session.get("user_id"):
                flash("Please log in.", "warning")
                return redirect(url_for("login"))
            user = current_user()
            if not user or user["role"] not in roles:
                flash("Access denied.", "danger")
                return redirect(url_for("index"))
            return f(*args, **kwargs)
        return decorated
    return decorator


# ─── Template Context ─────────────────────────────────────────────────────────

@app.context_processor
def inject_globals():
    user = current_user()
    notifs = []
    unread = 0
    chat_unread = 0
    user_profile = {}
    if user:
        notifs = get_notifications(user["id"])
        unread = sum(1 for n in notifs if not n["is_read"])
        chat_unread = get_unread_count(user["id"])
        try:
            user_profile = json.loads(user.get("profile") or "{}")
        except:
            pass

    return {
        "current_user": user,
        "notifications": notifs,
        "unread_count": unread,
        "chat_unread": chat_unread,
        "categories": CATEGORIES,
        "role_labels": ROLE_LABELS,
        "now": datetime.utcnow(),
        "user_profile": user_profile,
    }


# ─── Public Routes ────────────────────────────────────────────────────────────

@app.route("/")
@app.route("/api/index")
@app.route("/api/index.py")
def index():
    if session.get("user_id"):
        user = current_user()
        if user:
            role_redirect = {
                "student": "student_feed",
                "organizer": "organizer_dashboard",
                "recruiter": "recruiter_dashboard",
                "admin": "admin_dashboard",
            }
            return redirect(url_for(role_redirect.get(user["role"], "student_feed")))
    # Public landing
    stats = get_stats()
    featured = enrich_opps(get_opportunities(status="approved", limit=6, sort="newest"))
    featured_opps = [o for o in featured if o.get("is_featured")][:6] or featured[:6]
    return render_template("landing.html", stats=stats, featured=featured_opps)


@app.route("/login", methods=["GET", "POST"])
def login():
    if session.get("user_id"):
        return redirect(url_for("index"))
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        user = get_user_by_email(email)
        if user and check_password_hash(user["password_hash"], password):
            if not user["is_active"]:
                flash("Your account has been suspended. Contact admin.", "danger")
                return redirect(url_for("login"))
            session["user_id"] = user["id"]
            session["role"] = user["role"]
            session.permanent = True
            flash(f"Welcome back, {user['name'].split()[0]}! 👋", "success")
            role_redirect = {
                "student": "student_feed",
                "organizer": "organizer_dashboard",
                "recruiter": "recruiter_dashboard",
                "admin": "admin_dashboard",
            }
            return redirect(url_for(role_redirect.get(user["role"], "student_feed")))
        flash("Invalid email or password.", "danger")
    return render_template("login.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if session.get("user_id"):
        return redirect(url_for("index"))
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm = request.form.get("confirm_password", "")
        role = request.form.get("role", "student")
        organization = request.form.get("organization", "").strip()

        if role not in ["student", "organizer", "recruiter"]:
            flash("Invalid role selected.", "danger")
            return redirect(url_for("register"))
        if len(password) < 8:
            flash("Password must be at least 8 characters.", "danger")
            return redirect(url_for("register"))
        if password != confirm:
            flash("Passwords do not match.", "danger")
            return redirect(url_for("register"))

        ph = generate_password_hash(password)
        if create_user(email, ph, name, role, organization):
            flash("Account created! Please log in.", "success")
            return redirect(url_for("login"))
        else:
            flash("Email already registered.", "danger")
    return render_template("register.html", branches=BRANCHES, years=YEARS)


@app.route("/logout")
def logout():
    session.clear()
    flash("You've been logged out.", "info")
    return redirect(url_for("index"))


# ─── Student: Onboarding (Resume Upload) ─────────────────────────────────────

@app.route("/student/onboarding", methods=["GET", "POST"])
@role_required("student")
def student_onboarding():
    user = current_user()
    if request.method == "POST":
        if "resume" not in request.files:
            flash("No file selected.", "danger")
            return redirect(url_for("student_onboarding"))
        f = request.files["resume"]
        if not f or f.filename == "":
            flash("Please select a PDF file.", "danger")
            return redirect(url_for("student_onboarding"))
        if not f.filename.lower().endswith(".pdf"):
            flash("Only PDF files are accepted.", "danger")
            return redirect(url_for("student_onboarding"))

        # Save file
        import time as _t
        filename = secure_filename(f"{user['id']}_{int(_t.time())}.pdf")
        fpath = os.path.join(UPLOAD_FOLDER, filename)
        f.save(fpath)

        # Parse resume
        flash("AI is reading your resume... ⚙️", "info")
        from services.resume_parser import parse_resume
        parsed = parse_resume(fpath)

        save_resume(
            user_id=user["id"],
            file_path=fpath,
            skills=parsed.get("skills", []),
            domains=parsed.get("domains", []),
            experience_level=parsed.get("experience_level", "fresher"),
            college=parsed.get("college", ""),
            year=parsed.get("year", ""),
            raw_text=parsed.get("raw_text", ""),
        )

        # Update user profile with extracted info
        profile = get_profile()
        profile["skills"] = profile.get("skills") or parsed.get("skills", [])
        profile["assessment_status"] = "quiz_pending"
        if parsed.get("college") and not profile.get("college"):
            profile["college"] = parsed["college"]
        if parsed.get("year") and not profile.get("year"):
            profile["year"] = parsed["year"]

        # Generate Learning Path
        from services.ai_service import generate_learning_path
        roadmap = generate_learning_path(
            skills=parsed.get("skills", []),
            experience_level=parsed.get("experience_level", "fresher")
        )
        profile["learning_path"] = roadmap
        update_user_profile(user["id"], profile)

        skills = parsed.get("skills", [])
        flash(f"Resume parsed! AI generated a custom roadmap based on your {len(skills)} skills.", "success")
        return redirect(url_for("student_learning_path"))

    return render_template("student/onboarding.html", user=user)


# ─── Student: Learning Path ───────────────────────────────────────────────────

@app.route("/student/learning-path")
@role_required("student")
def student_learning_path():
    user = current_user()
    profile = get_profile()
    roadmap = profile.get("learning_path", [])
    
    # If no roadmap exists but they have skills, perhaps gen it now?
    if not roadmap and profile.get("skills"):
        from services.ai_service import generate_learning_path
        roadmap = generate_learning_path(profile.get("skills", []))
        profile["learning_path"] = roadmap
        update_user_profile(user["id"], profile)

    return render_template("student/learning_path.html", user=user, roadmap=roadmap, profile=profile)


# ─── Student: Quiz ────────────────────────────────────────────────────────────

@app.route("/student/quiz")
@role_required("student")
def student_quiz():
    user = current_user()
    resume = get_resume(user["id"])
    if not resume:
        flash("Please upload your resume first.", "warning")
        return redirect(url_for("student_onboarding"))

    skills = resume.get("skills", [])
    attempt_count = get_assessment_attempt_count(user["id"])

    # Check for existing pending quiz, else generate new one
    existing = get_pending_assessment(user["id"])
    if existing and existing["questions"]:
        assessment_id = existing["id"]
        questions = existing["questions"]
    else:
        from services.quiz_engine import generate_quiz
        questions = generate_quiz(skills)
        if not questions:
            flash("Gemini is still warming up. Please try again in a moment.", "warning")
            return redirect(url_for("student_quiz"))
        save_assessment_questions(user["id"], questions, attempt=attempt_count + 1)
        fresh = get_pending_assessment(user["id"])
        assessment_id = fresh["id"] if fresh else 0

    return render_template(
        "student/quiz.html",
        user=user, skills=skills,
        questions=questions,
        assessment_id=assessment_id,
        attempt_count=attempt_count,
    )


@app.route("/student/quiz/submit", methods=["POST"])
@role_required("student")
def student_quiz_submit():
    user = current_user()
    assessment_id = int(request.form.get("assessment_id", 0))
    pending = get_pending_assessment(user["id"])
    if not pending or pending["id"] != assessment_id:
        flash("Quiz session expired. Please start again.", "warning")
        return redirect(url_for("student_quiz"))

    questions = pending["questions"]
    answers = []
    for i in range(len(questions)):
        val = request.form.get(f"answer_{i}", "-1")
        answers.append(int(val))

    from services.quiz_engine import score_quiz
    result = score_quiz(questions, answers)

    complete_assessment(
        assessment_id=assessment_id,
        answers=answers,
        score=result["score"],
        total=result["total"],
        passed=result["passed"],
        weak_skills=result["weak_skills"],
        strong_skills=result["strong_skills"],
        breakdown=result.get("skill_breakdown", {}),
    )

    # Update profile status
    profile = get_profile()
    profile["assessment_status"] = "passed" if result["passed"] else "learning"
    profile["assessment_score"] = result["score"]
    update_user_profile(user["id"], profile)

    # Flash the result inline and redirect to feed
    score = result["score"]
    total = result["total"]
    passed = result["passed"]
    strong = ", ".join(result.get("strong_skills", [])[:3])

    if passed:
        flash(f"Quiz Passed! You scored {score}/{total}. Strong areas: {strong or 'Great job!'}", "success")
    else:
        weak = ", ".join(result.get("weak_skills", [])[:3])
        flash(f"Quiz done. Score: {score}/{total}. Focus on: {weak or 'Keep practicing!'}. Your Learning Path is ready!", "info")

    return redirect(url_for("student_feed"))


@app.route("/student/quiz/result")
@role_required("student")
def student_quiz_result():
    user = current_user()
    result = session.pop("last_result", None)
    if not result:
        latest = get_latest_assessment(user["id"])
        if not latest:
            return redirect(url_for("student_quiz"))
        from services.quiz_engine import score_quiz
        result = score_quiz(latest["questions"], latest["student_answers"])
    attempt_count = get_assessment_attempt_count(user["id"])
    return render_template("student/quiz_result.html",
                           user=user, result=result, attempt_count=attempt_count)


# ─── Student: Learning Path ───────────────────────────────────────────────────

@app.route("/student/learning")
@role_required("student")
def student_learning():
    user = current_user()
    resume = get_resume(user["id"])
    if not resume:
        flash("Upload your resume first.", "warning")
        return redirect(url_for("student_onboarding"))

    latest = get_latest_assessment(user["id"])
    weak_skills = latest["weak_skills"] if latest else []

    from services.learning_path import get_learning_path
    skills = resume.get("skills", [])
    modules = get_learning_path(skills, weak_skills)

    if not modules:
        flash("Gemini is generating your learning path. Please refresh in a moment.", "info")
        return redirect(url_for("student_feed"))

    current_module_index = int(request.args.get("module", 0))
    current_module_index = min(current_module_index, len(modules) - 1)
    current_module = modules[current_module_index] if modules else None

    # Progress map skill → progress row
    progress = get_learning_progress(user["id"])
    progress_map = {p["skill"]: p for p in progress}
    completed_count = count_completed_modules(user["id"])

    # Mini quiz for current module
    mini_quiz = []
    if current_module:
        prog_entry = progress_map.get(current_module["skill"], {})
        if prog_entry.get("video_watched") and not prog_entry.get("mini_quiz_passed"):
            from services.quiz_engine import generate_mini_quiz
            mini_quiz = generate_mini_quiz(current_module["skill"])

    return render_template(
        "student/learning_path.html",
        user=user, profile=resume, modules=modules,
        current_module=current_module,
        current_module_index=current_module_index,
        progress_map=progress_map,
        completed_count=completed_count,
        mini_quiz=mini_quiz,
        pass_mark=2,
    )


@app.route("/student/learning/watch", methods=["POST"])
@role_required("student")
def student_learning_watch():
    user = current_user()
    skill = request.form.get("skill", "")
    module_index = int(request.form.get("module_index", 0))
    mark_video_watched(user["id"], skill, module_index)
    flash(f"Video marked as watched! Now take the quick quiz.", "success")
    return redirect(url_for("student_learning", module=module_index))


@app.route("/student/learning/quiz", methods=["POST"])
@role_required("student")
def student_learning_quiz():
    user = current_user()
    skill = request.form.get("skill", "")
    module_index = int(request.form.get("module_index", 0))

    from services.quiz_engine import generate_mini_quiz
    questions = generate_mini_quiz(skill)
    answers = [int(request.form.get(f"answer_{i}", -1)) for i in range(len(questions))]
    score = sum(1 for i, q in enumerate(questions) if answers[i] == q["correct_index"])
    passed = score >= 2  # 2/3 to pass

    complete_learning_module(user["id"], skill, score, passed)

    if passed:
        flash(f"Mini-quiz passed! ({score}/{len(questions)}) Module complete.", "success")
    else:
        flash(f"Mini-quiz score: {score}/{len(questions)}. Need 2/3. Try again!", "warning")

    return redirect(url_for("student_learning", module=module_index))


# ─── Student Routes ───────────────────────────────────────────────────────────

@app.route("/student/feed")
@role_required("student")
def student_feed():
    user = current_user()          # ← must be first; used everywhere below
    profile = get_profile()
    category = request.args.get("category", "all")
    reward_type = request.args.get("reward_type", "all")
    min_prize = int(request.args.get("min_prize", 0))
    search = request.args.get("q", "").strip()
    sort = request.args.get("sort", "deadline_asc")

    opps = get_opportunities(
        category=category if category != "all" else None,
        reward_type=reward_type if reward_type != "all" else None,
        min_prize=min_prize, status="approved",
        search=search if search else None, limit=100, sort=sort,
    )

    # Skill-based filtering / ranking
    resume = get_resume(user["id"])
    student_skills = resume["skills"] if resume else profile.get("skills", [])
    if student_skills and not search:
        from services.learning_path import check_skill_in_opportunities
        skill_matched, others = [], []
        for o in opps:
            _, mscore, _ = check_skill_in_opportunities(
                student_skills, o["title"], o["description"],
                o.get("tags", []), o.get("company", "")
            )
            o["skill_match_score"] = mscore
            (skill_matched if mscore > 0 else others).append(o)
        skill_matched.sort(key=lambda x: x["skill_match_score"], reverse=True)
        opps = skill_matched + others

    # AI personalisation (only if no skill data)
    if not search and profile and not student_skills:
        opps = get_personalized_feed(opps, profile)

    # Filter out expired
    opps = [o for o in opps if days_left(o.get("deadline")) is None or days_left(o.get("deadline")) >= 0]
    opps = enrich_opps(opps)

    saved_ids = get_saved_ids(session["user_id"])
    assessment = get_latest_assessment(user["id"])
    assessment_status = profile.get("assessment_status", "none" if not resume else "quiz_pending")
    active_ads = get_ads("approved")

    return render_template(
        "student/feed.html",
        opportunities=opps, saved_ids=saved_ids,
        profile=profile, user=user,
        active_category=category, active_reward=reward_type,
        min_prize=min_prize, search=search, sort=sort,
        prize_filters=PRIZE_FILTERS, total=len(opps),
        assessment_status=assessment_status,
        student_skills=student_skills,
        assessment=assessment,
        ads=active_ads
    )



@app.route("/student/profile", methods=["GET", "POST"])
@role_required("student")
def student_profile():
    user = current_user()
    profile = get_profile()
    if request.method == "POST":
        new_profile = dict(profile)
        new_profile.update({
            "year": request.form.get("year", ""),
            "branch": request.form.get("branch", ""),
            "college": request.form.get("college", ""),
            "interests": request.form.getlist("interests"),
            "preferred_categories": request.form.getlist("preferred_categories"),
            "location": request.form.get("location", ""),
            "skills": [s.strip() for s in request.form.get("skills", "").split(",") if s.strip()],
            "linkedin": request.form.get("linkedin", ""),
            "github": request.form.get("github", ""),
        })
        
        if "avatar" in request.files:
            f = request.files["avatar"]
            if f and f.filename != "":
                import time as _t
                ext = f.filename.rsplit('.', 1)[1].lower() if '.' in f.filename else 'png'
                filename = secure_filename(f"avatar_{user['id']}_{int(_t.time())}.{ext}")
                fpath = os.path.join(UPLOAD_FOLDER, filename)
                f.save(fpath)
                new_profile["avatar"] = filename

        update_user_profile(user["id"], new_profile)
        flash("Profile updated! Your feed is now personalized. ✨", "success")
        return redirect(url_for("student_feed"))
    return render_template(
        "student/profile.html",
        user=user, profile=profile,
        branches=BRANCHES, years=YEARS, interest_tags=INTEREST_TAGS,
    )


@app.route("/student/saved")
@role_required("student")
def student_saved():
    user = current_user()
    saved = get_saved_opportunities(user["id"])
    saved = enrich_opps(saved)
    return render_template("student/saved.html", opportunities=saved, user=user)


@app.route("/student/save/<int:opp_id>", methods=["POST"])
@role_required("student")
def toggle_save(opp_id):
    user = current_user()
    saved_ids = get_saved_ids(user["id"])
    if opp_id in saved_ids:
        unsave_opportunity(user["id"], opp_id)
        return jsonify({"saved": False, "msg": "Removed from saved"})
    else:
        save_opportunity(user["id"], opp_id)
        return jsonify({"saved": True, "msg": "Saved!"})


# ─── Organizer Routes ─────────────────────────────────────────────────────────

@app.route("/organizer/dashboard")
@role_required("organizer")
def organizer_dashboard():
    user = current_user()
    opps = get_opportunities_by_user(user["id"])
    opps = enrich_opps(opps)
    stats = {
        "total": len(opps),
        "approved": sum(1 for o in opps if o["status"] == "approved"),
        "pending": sum(1 for o in opps if o["status"] == "pending"),
        "rejected": sum(1 for o in opps if o["status"] == "rejected"),
    }
    return render_template("organizer/dashboard.html", user=user, opportunities=opps, stats=stats)


@app.route("/organizer/new", methods=["GET", "POST"])
@role_required("organizer")
def organizer_new():
    user = current_user()
    if request.method == "POST":
        tags = [t.strip() for t in request.form.get("tags", "").split(",") if t.strip()]
        from services.dedup_engine import make_hash
        title = request.form.get("title", "")
        data = {
            "title": title,
            "category": request.form.get("category", "hackathon"),
            "source": user.get("organization") or "Event Organizer",
            "source_url": request.form.get("source_url", ""),
            "apply_link": request.form.get("apply_link", ""),
            "deadline": request.form.get("deadline") or None,
            "reward": request.form.get("reward", ""),
            "reward_type": request.form.get("reward_type", "certificate"),
            "prize_amount": int(request.form.get("prize_amount", 0) or 0),
            "eligibility": request.form.get("eligibility", "Open to All"),
            "tags": tags,
            "description": request.form.get("description", ""),
            "company": request.form.get("company", user.get("organization", "")),
            "location": request.form.get("location", "Remote"),
            "posted_by": user["id"],
            "status": "pending",
            "is_featured": 0,
            "hash": make_hash(title, user.get("organization", "organizer")),
        }
        _, is_new = insert_opportunity(data)
        if is_new:
            flash("Event submitted for admin review! You'll be notified once approved. 🚀", "success")
            add_notification(user["id"], f"Your event '{title}' is under review.", "/organizer/dashboard")
        else:
            flash("An event with this title already exists.", "warning")
        return redirect(url_for("organizer_dashboard"))
    return render_template("organizer/new_event.html", user=user, categories=CATEGORIES)


@app.route("/organizer/delete/<int:opp_id>", methods=["POST"])
@role_required("organizer")
def organizer_delete(opp_id):
    user = current_user()
    delete_opportunity(opp_id, user_id=user["id"])
    flash("Event deleted.", "info")
    return redirect(url_for("organizer_dashboard"))


# ─── Recruiter Routes ─────────────────────────────────────────────────────────

@app.route("/recruiter/dashboard")
@role_required("recruiter")
def recruiter_dashboard():
    user = current_user()
    opps = get_opportunities_by_user(user["id"])
    opps = enrich_opps(opps)
    stats = {
        "total": len(opps),
        "approved": sum(1 for o in opps if o["status"] == "approved"),
        "pending": sum(1 for o in opps if o["status"] == "pending"),
        "rejected": sum(1 for o in opps if o["status"] == "rejected"),
    }
    # For each approved listing, find skill-matched students
    from database import get_skill_matched_students
    import json as _json
    for opp in opps:
        if opp["status"] == "approved":
            tags = opp.get("tags") or []
            if isinstance(tags, str):
                try: tags = _json.loads(tags)
                except: tags = [t.strip() for t in tags.split(",") if t.strip()]
            title_words = [w for w in opp["title"].split() if len(w) > 3]
            skills = list(set(tags + title_words))[:10]
            opp["matched_students"] = get_skill_matched_students(skills, limit=3)
        else:
            opp["matched_students"] = []
    return render_template("recruiter/dashboard.html", user=user, opportunities=opps, stats=stats)


@app.route("/recruiter/new", methods=["GET", "POST"])
@role_required("recruiter")
def recruiter_new():
    user = current_user()
    if request.method == "POST":
        tags = [t.strip() for t in request.form.get("tags", "").split(",") if t.strip()]
        from services.dedup_engine import make_hash
        title = request.form.get("title", "")
        data = {
            "title": title,
            "category": request.form.get("category", "internship"),
            "source": user.get("organization") or "Company Recruiter",
            "source_url": request.form.get("source_url", ""),
            "apply_link": request.form.get("apply_link", ""),
            "deadline": request.form.get("deadline") or None,
            "reward": request.form.get("reward", ""),
            "reward_type": request.form.get("reward_type", "stipend"),
            "prize_amount": 0,
            "eligibility": request.form.get("eligibility", "Open to All"),
            "tags": tags,
            "description": request.form.get("description", ""),
            "company": request.form.get("company", user.get("organization", "")),
            "location": request.form.get("location", "Remote"),
            "posted_by": user["id"],
            "status": "pending",
            "is_featured": 0,
            "hash": make_hash(title, user.get("organization", "recruiter")),
        }
        _, is_new = insert_opportunity(data)
        if is_new:
            flash("Job/Internship submitted for admin review! 📌", "success")
            add_notification(user["id"], f"Your listing '{title}' is under review.", "/recruiter/dashboard")
        else:
            flash("A listing with this title already exists.", "warning")
        return redirect(url_for("recruiter_dashboard"))
    return render_template("recruiter/new_job.html", user=user)


@app.route("/recruiter/delete/<int:opp_id>", methods=["POST"])
@role_required("recruiter")
def recruiter_delete(opp_id):
    user = current_user()
    delete_opportunity(opp_id, user_id=user["id"])
    flash("Listing deleted.", "info")
    return redirect(url_for("recruiter_dashboard"))


@app.route("/recruiter/talent")
@role_required("recruiter")
def recruiter_talent():
    from database import get_skill_matched_students
    skill_filter = request.args.get("skill", "").strip() or None
    min_score = int(request.args.get("min_score", 0))  # 0 = show all (course+quiz)
    status_filter = request.args.get("status", "all")  # all / verified / course_done
    students = get_talent_board(skill_filter=skill_filter, min_score=min_score)
    # Apply status filter
    if status_filter == "verified":
        students = [s for s in students if s["passed"]]
    elif status_filter == "course_done":
        students = [s for s in students if s["course_completed"] and not s["passed"]]
    # Build unique skill list
    all_skills_set = set()
    for s in students:
        all_skills_set.update(s.get("strong_skills", []))
        all_skills_set.update(s.get("resume_skills", []))
    all_skills = sorted(all_skills_set)
    # Recruiter's own approved listings for skill-match panel
    user = current_user()
    my_opps = [o for o in get_opportunities_by_user(user["id"]) if o["status"] == "approved"]
    return render_template(
        "recruiter/talent.html",
        students=students,
        all_skills=all_skills,
        active_skill=skill_filter,
        active_status=status_filter,
        min_score=min_score,
        my_opps=my_opps,
    )



# ─── Team Pool Routes ─────────────────────────────────────────────────────────

@app.route("/teams")
@role_required("student", "recruiter")
def teams():
    active_skill = request.args.get("skill", "").strip() or None
    active_status = request.args.get("status", "open")
    pools = get_team_pools(status=active_status, skill=active_skill)
    user = current_user()
    my_pools = get_my_team_pools(user["id"]) if session.get("role") == "student" else []
    requested_ids = set()
    for p in pools:
        if has_requested_pool(p["id"], user["id"]):
            requested_ids.add(p["id"])
    return render_template(
        "student/teams.html",
        pools=pools, my_pools=my_pools,
        active_skill=active_skill, active_status=active_status,
        requested_ids=requested_ids,
        current_uid=user["id"],
    )


@app.route("/teams/create", methods=["POST"])
@role_required("student")
def team_create():
    user = current_user()
    hackathon_name = request.form.get("hackathon_name", "").strip()
    if not hackathon_name:
        flash("Hackathon name is required.", "danger")
        return redirect(url_for("teams"))
    team_name = request.form.get("team_name", "").strip()
    team_size = int(request.form.get("team_size", 4))
    current_size = int(request.form.get("current_size", 1))
    roles_needed = request.form.getlist("roles_needed")
    skills_raw = request.form.get("skills_needed", "")
    skills_needed = [s.strip() for s in skills_raw.split(",") if s.strip()]
    description = request.form.get("description", "").strip()
    pool_id = create_team_pool(
        creator_id=user["id"],
        hackathon_name=hackathon_name,
        team_name=team_name,
        team_size=team_size,
        roles_needed=roles_needed,
        skills_needed=skills_needed,
        description=description,
    )
    # Set current_size
    from database import get_db
    conn = get_db()
    conn.execute("UPDATE team_pools SET current_size=? WHERE id=?", (current_size, pool_id))
    conn.commit()
    conn.close()
    flash(f"Team pool posted for '{hackathon_name}'! Waiting for teammates to find you.", "success")
    return redirect(url_for("team_detail", pool_id=pool_id))


@app.route("/teams/<int:pool_id>")
@role_required("student", "recruiter")
def team_detail(pool_id):
    pool = get_team_pool(pool_id)
    if not pool:
        abort(404)
    user = current_user()
    is_creator = pool["creator_id"] == user["id"]
    requests_list = get_pool_requests(pool_id) if is_creator else []
    already_requested = has_requested_pool(pool_id, user["id"]) if not is_creator else False
    return render_template(
        "student/team_detail.html",
        pool=pool, is_creator=is_creator,
        requests=requests_list,
        already_requested=already_requested,
        current_uid=user["id"],
    )


@app.route("/teams/<int:pool_id>/join", methods=["POST"])
@role_required("student")
def team_join(pool_id):
    user = current_user()
    pool = get_team_pool(pool_id)
    if not pool or pool["status"] != "open":
        flash("This pool is no longer accepting requests.", "warning")
        return redirect(url_for("teams"))
    if pool["creator_id"] == user["id"]:
        flash("You can't join your own pool.", "warning")
        return redirect(url_for("team_detail", pool_id=pool_id))
    message = request.form.get("message", "").strip()
    ok = request_join_pool(pool_id, user["id"], message)
    if ok:
        flash("Join request sent! The team creator will review your request.", "success")
    else:
        flash("You've already requested to join this team.", "info")
    return redirect(url_for("team_detail", pool_id=pool_id))


@app.route("/teams/request/<int:request_id>/respond", methods=["POST"])
@role_required("student")
def team_respond(request_id):
    action = request.form.get("action", "rejected")
    if action not in ("accepted", "rejected"):
        abort(400)
    respond_to_request(request_id, action)
    msg = "Teammate accepted! 🎉" if action == "accepted" else "Request rejected."
    flash(msg, "success" if action == "accepted" else "info")
    return redirect(request.referrer or url_for("teams"))


@app.route("/teams/<int:pool_id>/close", methods=["POST"])
@role_required("student")
def team_close(pool_id):
    user = current_user()
    pool = get_team_pool(pool_id)
    if pool and pool["creator_id"] == user["id"]:
        close_team_pool(pool_id)
        flash("Team pool closed.", "info")
    return redirect(url_for("team_detail", pool_id=pool_id))


# ─── Chat Routes (Students / Team Pool) ───────────────────────────────────────

@app.route("/chat")
@role_required("student")
def chat_list():
    user = current_user()
    chats = get_chat_list(user["id"])
    return render_template("student/chat.html",
                           chat_list=chats, other_user=None,
                           messages=[], current_uid=user["id"])


@app.route("/chat/<int:other_id>")
@role_required("student")
def chat_thread(other_id):
    user = current_user()
    other = get_user_by_id(other_id)
    if not other:
        abort(404)
    messages = get_conversation(user["id"], other_id)
    chats = get_chat_list(user["id"])
    return render_template(
        "student/chat.html",
        chat_list=chats,
        other_user=other,
        messages=messages,
        current_uid=user["id"],
    )


# ─── Recruiter Direct Inbox (separate from team pool chat) ─────────────────────

@app.route("/recruiter/inbox")
@role_required("recruiter")
def recruiter_chat_list():
    user = current_user()
    chats = get_chat_list(user["id"])
    return render_template(
        "recruiter/chat.html",
        chat_list=chats,
        other_user=None,
        messages=[],
        current_uid=user["id"],
    )


@app.route("/recruiter/inbox/<int:other_id>")
@role_required("recruiter")
def recruiter_chat_thread(other_id):
    user = current_user()
    other = get_user_by_id(other_id)
    if not other:
        abort(404)
    messages = get_conversation(user["id"], other_id)
    chats = get_chat_list(user["id"])
    return render_template(
        "recruiter/chat.html",
        chat_list=chats,
        other_user=other,
        messages=messages,
        current_uid=user["id"],
    )


@app.route("/chat/send", methods=["POST"])
@role_required("student", "recruiter")
def chat_send():
    user = current_user()
    data = request.get_json(force=True)
    receiver_id = int(data.get("receiver_id", 0))
    content = (data.get("content") or "").strip()
    if not content or not receiver_id:
        return jsonify(ok=False, error="empty")
    msg_id = send_message(user["id"], receiver_id, content)
    return jsonify(ok=True, msg={
        "id": msg_id,
        "sender_id": user["id"],
        "receiver_id": receiver_id,
        "content": content,
        "created_at": __import__("datetime").datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "sender_name": user["name"],
    })


@app.route("/chat/poll/<int:other_id>")
@role_required("student", "recruiter")
def chat_poll(other_id):
    user = current_user()
    after_id = int(request.args.get("after", 0))
    new_msgs = get_new_messages(user["id"], other_id, after_id)
    return jsonify(messages=new_msgs)


# ─── Admin (Hidden) ───────────────────────────────────────────────────────────

@app.route(f"/{ADMIN_SECRET_PATH}")
def admin_secret_entry():
    """Hidden admin URL. Redirect to admin dashboard if logged in as admin."""
    if session.get("user_id") and session.get("role") == "admin":
        return redirect(url_for("admin_dashboard"))
    # Show a fake 404-looking page that actually has a login button
    return redirect(url_for("login"))


@app.route("/admin/dashboard")
@role_required("admin")
def admin_dashboard():
    stats = get_stats()
    pending = get_pending_opportunities()
    pending = enrich_opps(pending)
    logs = get_scrape_logs(20)
    all_ads = get_ads()
    return render_template("admin/dashboard.html", stats=stats, pending=pending, logs=logs, ads=all_ads)


@app.route("/admin/opportunities")
@role_required("admin")
def admin_opportunities():
    category = request.args.get("category")
    status_filter = request.args.get("status", "approved")
    opps = get_opportunities(category=category, status=status_filter, limit=200)
    opps = enrich_opps(opps)
    return render_template("admin/opportunities.html", opportunities=opps,
                           active_category=category or "all", active_status=status_filter)


@app.route("/admin/approve/<int:opp_id>", methods=["POST"])
@role_required("admin")
def admin_approve(opp_id):
    update_opportunity_status(opp_id, "approved")
    opp = get_opportunity_by_id(opp_id)
    if opp and opp.get("posted_by"):
        add_notification(
            opp["posted_by"],
            f"✅ Your listing '{opp['title']}' has been approved and is now live!",
            "/student/feed",
        )
    flash("Approved and published!", "success")
    return redirect(request.referrer or url_for("admin_dashboard"))


@app.route("/admin/reject/<int:opp_id>", methods=["POST"])
@role_required("admin")
def admin_reject(opp_id):
    update_opportunity_status(opp_id, "rejected")
    opp = get_opportunity_by_id(opp_id)
    if opp and opp.get("posted_by"):
        add_notification(
            opp["posted_by"],
            f"❌ Your listing '{opp['title']}' was not approved. Contact admin for details.",
            "/student/feed",
        )
    flash("Listing rejected.", "warning")
    return redirect(request.referrer or url_for("admin_dashboard"))


@app.route("/admin/delete/<int:opp_id>", methods=["POST"])
@role_required("admin")
def admin_delete(opp_id):
    delete_opportunity(opp_id)
    flash("Opportunity permanently deleted.", "danger")
    return redirect(request.referrer or url_for("admin_dashboard"))


@app.route("/admin/users")
@role_required("admin")
def admin_users():
    users = get_all_users()
    return render_template("admin/users.html", users=users)


@app.route("/admin/toggle-user/<int:user_id>", methods=["POST"])
@role_required("admin")
def admin_toggle_user(user_id):
    user = get_user_by_id(user_id)
    if user and user["role"] == "admin":
        flash("Cannot disable admin accounts.", "danger")
        return redirect(url_for("admin_users"))
    toggle_user_active(user_id)
    flash("User status updated.", "info")
    return redirect(url_for("admin_users"))


@app.route("/admin/scrape", methods=["POST"])
@role_required("admin")
def admin_scrape():
    """Synchronous scrape — runs NOW and returns JSON results for AJAX."""
    scraper_type = request.form.get("type", "core")  # core | social | all
    results_summary = []

    from scrapers import CORE_SCRAPERS
    from services.dedup_engine import deduplicate_list
    from database import insert_opportunity, log_scrape

    def _run_scraper(ScraperClass, **kwargs):
        try:
            scraper = ScraperClass(**kwargs)
            results, error = scraper.run()
            unique = deduplicate_list(results)
            new_count = sum(1 for opp in unique if insert_opportunity(opp)[1])
            dup_count = len(results) - len(unique)
            log_scrape(scraper.SOURCE_NAME,
                       "success" if not error else "error",
                       new_count, dup_count, error)
            return {
                "source": scraper.SOURCE_NAME,
                "status": "error" if error else "success",
                "new": new_count,
                "duplicates": dup_count,
                "total": len(results),
                "error": error or "",
            }
        except Exception as e:
            log_scrape(getattr(ScraperClass, 'SOURCE_NAME', '?'), "error", 0, 0, str(e))
            return {
                "source": getattr(ScraperClass, 'SOURCE_NAME', ScraperClass.__name__),
                "status": "error",
                "new": 0,
                "duplicates": 0,
                "total": 0,
                "error": str(e),
            }

    if scraper_type in ("core", "all"):
        for ScraperClass in CORE_SCRAPERS:
            results_summary.append(_run_scraper(ScraperClass))

    if scraper_type in ("social", "all"):
        from database import get_social_credentials
        from scrapers.instagram_scraper import InstagramScraper
        from scrapers.linkedin_scraper import LinkedInScraper

        ig_creds = get_social_credentials("instagram").get("credentials", {})
        results_summary.append(_run_scraper(
            InstagramScraper,
            ig_username=ig_creds.get("username"),
            ig_password=ig_creds.get("password"),
        ))

        li_creds = get_social_credentials("linkedin").get("credentials", {})
        results_summary.append(_run_scraper(
            LinkedInScraper,
            email=li_creds.get("email") or None,
            password=li_creds.get("password") or None,
            headless=True,
        ))

    total_new = sum(r["new"] for r in results_summary)

    # If AJAX request, return JSON
    if request.headers.get("X-Requested-With") == "XMLHttpRequest" or \
       request.accept_mimetypes.best == "application/json":
        return jsonify(ok=True, results=results_summary, total_new=total_new)

    # Normal form submit fallback
    flash(f"Scrape complete! Found {total_new} new opportunities across {len(results_summary)} sources.", "success")
    return redirect(url_for("admin_dashboard"))


@app.route("/admin/feature/<int:opp_id>", methods=["POST"])
@role_required("admin")
def admin_feature(opp_id):
    from database import get_db
    conn = get_db()
    conn.execute("UPDATE opportunities SET is_featured = CASE WHEN is_featured=1 THEN 0 ELSE 1 END WHERE id=?", (opp_id,))
    conn.commit()
    conn.close()
    flash("Featured status toggled.", "info")
    return redirect(request.referrer or url_for("admin_dashboard"))


# ─── Admin: Ads ─────────────────────────────────────────────────────────────

@app.route("/admin/ads", methods=["POST"])
@role_required("admin")
def admin_create_ad():
    """Create a new ad banner."""
    title = request.form.get("title")
    image_url = request.form.get("image_url")
    target_link = request.form.get("target_link")
    if title and image_url and target_link:
        create_ad(title, image_url, target_link)
        flash("Ad created successfully! It is pending approval.", "success")
    else:
        flash("All fields are required.", "danger")
    return redirect(url_for("admin_dashboard") + "#ads")

@app.route("/admin/ads/<int:ad_id>/toggle", methods=["POST"])
@role_required("admin")
def admin_toggle_ad(ad_id):
    """Approve or Reject an ad."""
    status = request.form.get("status", "approved")
    update_ad_status(ad_id, status)
    flash(f"Ad marked as {status}.", "success")
    return redirect(url_for("admin_dashboard") + "#ads")

@app.route("/admin/ads/<int:ad_id>/delete", methods=["POST"])
@role_required("admin")
def admin_delete_ad(ad_id):
    """Delete an ad entirely."""
    delete_ad(ad_id)
    flash("Ad deleted.", "info")
    return redirect(url_for("admin_dashboard") + "#ads")

# ─── Admin: Social Media ──────────────────────────────────────────────────────

@app.route("/admin/social")
@role_required("admin")
def admin_social():
    """Social media scraper configuration page."""
    social_creds = get_all_social_credentials()
    ig = get_social_credentials("instagram")
    tw = get_social_credentials("twitter")
    li = get_social_credentials("linkedin")
    return render_template(
        "admin/social_config.html",
        social_creds=social_creds,
        ig_creds=ig.get("credentials", {}),
        tw_creds=tw.get("credentials", {}),
        li_creds=li.get("credentials", {}),
        tw_active=tw.get("is_active", 0),
        li_active=li.get("is_active", 0),
    )


@app.route("/admin/social/save/<platform>", methods=["POST"])
@role_required("admin")
def admin_social_save(platform):
    """Save social media credentials for a platform."""
    if platform not in ("instagram", "twitter", "linkedin"):
        flash("Invalid platform.", "danger")
        return redirect(url_for("admin_social"))

    existing = get_social_credentials(platform).get("credentials", {})

    if platform == "instagram":
        username = request.form.get("username", "").strip()
        raw_pw = request.form.get("password", "")
        # Keep existing password if placeholder sent
        password = existing.get("password", "") if raw_pw.startswith("●") else raw_pw
        creds = {"username": username, "password": password}
        is_active = True  # Instagram always active (no-auth for public)

    elif platform == "twitter":
        raw_bearer = request.form.get("bearer_token", "")
        raw_api_secret = request.form.get("api_secret", "")
        raw_at_secret = request.form.get("access_token_secret", "")
        bearer = existing.get("bearer_token", "") if raw_bearer.startswith("●") else raw_bearer
        api_secret = existing.get("api_secret", "") if raw_api_secret.startswith("●") else raw_api_secret
        at_secret = existing.get("access_token_secret", "") if raw_at_secret.startswith("●") else raw_at_secret
        creds = {
            "bearer_token": bearer.strip(),
            "api_key": request.form.get("api_key", "").strip(),
            "api_secret": api_secret.strip(),
            "access_token": request.form.get("access_token", "").strip(),
            "access_token_secret": at_secret.strip(),
        }
        is_active = bool(creds.get("bearer_token"))

    elif platform == "linkedin":
        email = request.form.get("email", "").strip()
        raw_pw = request.form.get("password", "")
        password = existing.get("password", "") if raw_pw.startswith("●") else raw_pw
        creds = {"email": email, "password": password}
        is_active = bool(email and password)

    save_social_credentials(platform, creds, is_active)
    flash(f"{platform.title()} credentials saved! {'Active' if is_active else 'Not active — check required fields'}.",
          "success" if is_active else "warning")
    return redirect(url_for("admin_social"))


@app.route("/admin/social/trigger/<platform>", methods=["POST"])
@role_required("admin")
def admin_social_trigger(platform):
    """Trigger a one-off scrape for a specific social platform."""
    import threading
    from services.scheduler import run_social_scrapers

    if platform == "all":
        trigger_social_now()
        flash("All social media scrapers triggered in background!", "info")
    elif platform == "core":
        trigger_core_now()
        flash("Core web scrapers triggered in background!", "info")
    else:
        def _run_one():
            from database import (
                get_social_credentials as _gsc,
                insert_opportunity, log_scrape, update_social_scrape_time,
            )
            from services.dedup_engine import deduplicate_list
            cred = _gsc(platform)
            creds = cred.get("credentials", {})
            try:
                if platform == "instagram":
                    from scrapers.instagram_scraper import InstagramScraper
                    s = InstagramScraper(creds.get("username"), creds.get("password"))
                elif platform == "twitter":
                    from scrapers.twitter_scraper import TwitterScraper
                    s = TwitterScraper(**{k: creds.get(k) for k in
                                         ["bearer_token","api_key","api_secret","access_token","access_token_secret"]})
                elif platform == "linkedin":
                    from scrapers.linkedin_scraper import LinkedInScraper
                    s = LinkedInScraper(email=creds.get("email"), password=creds.get("password"))
                else:
                    return
                results, err = s.run()
                unique = deduplicate_list(results)
                new_count = sum(1 for o in unique if insert_opportunity(o)[1])
                log_scrape(platform.title(), "success" if not err else "error", new_count, len(results)-len(unique), err)
                update_social_scrape_time(platform)
            except Exception as e:
                log_scrape(platform.title(), "error", 0, 0, str(e))
        threading.Thread(target=_run_one, daemon=True, name=f"{platform}-trigger").start()
        flash(f"{platform.title()} scraper triggered in background! Check logs shortly.", "info")
    return redirect(url_for("admin_social"))


# ─── API Routes ───────────────────────────────────────────────────────────────

@app.route("/api/opportunities")
def api_opportunities():
    category = request.args.get("category")
    reward_type = request.args.get("reward_type")
    min_prize = int(request.args.get("min_prize", 0))
    search = request.args.get("q")
    sort = request.args.get("sort", "deadline_asc")
    limit = min(int(request.args.get("limit", 50)), 200)
    opps = get_opportunities(
        category=category, reward_type=reward_type,
        min_prize=min_prize, status="approved",
        search=search, limit=limit, sort=sort,
    )
    opps = enrich_opps(opps)
    return jsonify({"count": len(opps), "opportunities": opps})


@app.route("/api/stats")
def api_stats():
    return jsonify(get_stats())


@app.route("/api/mark-notifications-read", methods=["POST"])
@login_required
def api_mark_notifications():
    mark_notifications_read(session["user_id"])
    return jsonify({"ok": True})


@app.route("/api/ai-analyze/<int:opp_id>", methods=["POST"])
@role_required("admin")
def api_ai_analyze(opp_id):
    opp = get_opportunity_by_id(opp_id)
    if not opp:
        return jsonify({"error": "Not found"}), 404
    from services.ai_service import analyze_opportunity
    result = analyze_opportunity(
        opp["title"], opp["description"], opp["reward"], opp["eligibility"]
    )
    mark_ai_analyzed(opp_id, result.get("legitimacy_score", 1.0) if isinstance(result.get("legitimacy_score"), float) else 1.0)
    return jsonify(result)


@app.route('/uploads/<path:filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


# ─── Error Handlers ───────────────────────────────────────────────────────────

@app.errorhandler(404)
def not_found(e):
    return render_template("404.html"), 404


@app.errorhandler(403)
def forbidden(e):
    return render_template("404.html"), 403


# ─── Entrypoint ───────────────────────────────────────────────────────────────

@app.route("/api/ai_status")
def ai_status():
    """Check Gemini connectivity without consuming heavy quota."""
    from services.ai_service import call_gemini
    from config import GEMINI_API_KEY
    if not GEMINI_API_KEY or GEMINI_API_KEY.startswith("AIzaSyAW..."):
        return {"status": "error", "message": "No API Key"}
    
    # Simple check call
    res = call_gemini("Ping")
    if res:
        return {"status": "online", "message": "Gemini Active"}
    else:
        return {"status": "exhausted", "message": "Quota Full (20/20 reached)"}

if __name__ == "__main__":
    init_db()
    # Auto-seed if DB is fresh
    from database import get_stats as _gs
    if _gs()["total_opportunities"] == 0:
        try:
            from seed_data import seed
            seed()
        except Exception as ex:
            logger.warning(f"Seed failed: {ex}")
    start_scheduler()
    app.run(debug=DEBUG, host="0.0.0.0", port=5000)
