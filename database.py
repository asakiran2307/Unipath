import sqlite3
import json
from config import DATABASE_PATH


def get_db():
    conn = sqlite3.connect(DATABASE_PATH, timeout=20.0)
    conn.row_factory = sqlite3.Row
    try:
        conn.execute("PRAGMA journal_mode=WAL")
    except Exception:
        pass
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db():
    conn = get_db()
    c = conn.cursor()

    c.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            name TEXT NOT NULL,
            role TEXT NOT NULL CHECK(role IN ('student','organizer','recruiter','admin')),
            profile TEXT DEFAULT '{}',
            organization TEXT DEFAULT '',
            is_active INTEGER DEFAULT 1,
            created_at TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS opportunities (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            category TEXT NOT NULL,
            source TEXT DEFAULT 'Manual',
            source_url TEXT DEFAULT '',
            apply_link TEXT NOT NULL,
            deadline TEXT,
            reward TEXT DEFAULT '',
            reward_type TEXT DEFAULT 'certificate',
            prize_amount INTEGER DEFAULT 0,
            eligibility TEXT DEFAULT 'Open to All',
            tags TEXT DEFAULT '[]',
            description TEXT DEFAULT '',
            company TEXT DEFAULT '',
            location TEXT DEFAULT 'Remote',
            posted_by INTEGER REFERENCES users(id),
            status TEXT DEFAULT 'pending',
            is_featured INTEGER DEFAULT 0,
            hash TEXT UNIQUE,
            scraped_at TEXT DEFAULT (datetime('now')),
            ai_analyzed INTEGER DEFAULT 0,
            legitimacy_score REAL DEFAULT 1.0
        );

        CREATE TABLE IF NOT EXISTS saved_opportunities (
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            opportunity_id INTEGER NOT NULL REFERENCES opportunities(id) ON DELETE CASCADE,
            saved_at TEXT DEFAULT (datetime('now')),
            PRIMARY KEY (user_id, opportunity_id)
        );

        CREATE TABLE IF NOT EXISTS scrape_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source TEXT NOT NULL,
            status TEXT NOT NULL,
            count_new INTEGER DEFAULT 0,
            count_duplicate INTEGER DEFAULT 0,
            error TEXT DEFAULT '',
            ran_at TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS notifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
            message TEXT NOT NULL,
            link TEXT DEFAULT '',
            is_read INTEGER DEFAULT 0,
            created_at TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS social_credentials (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            platform TEXT UNIQUE NOT NULL,
            credentials TEXT DEFAULT '{}',
            is_active INTEGER DEFAULT 0,
            last_scraped TEXT,
            scrape_count INTEGER DEFAULT 0,
            updated_at TEXT DEFAULT (datetime('now'))
        );

        INSERT OR IGNORE INTO social_credentials (platform, credentials, is_active)
        VALUES
            ('instagram', '{}', 0),
            ('twitter', '{}', 0),
            ('linkedin', '{}', 0);

        CREATE TABLE IF NOT EXISTS resumes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER UNIQUE NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            file_path TEXT NOT NULL,
            raw_text TEXT DEFAULT '',
            skills TEXT DEFAULT '[]',
            domains TEXT DEFAULT '[]',
            experience_level TEXT DEFAULT 'fresher',
            college_extracted TEXT DEFAULT '',
            year_extracted TEXT DEFAULT '',
            uploaded_at TEXT DEFAULT (datetime('now')),
            updated_at TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS student_assessments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            questions TEXT DEFAULT '[]',
            student_answers TEXT DEFAULT '[]',
            score INTEGER DEFAULT 0,
            total INTEGER DEFAULT 10,
            passed INTEGER DEFAULT 0,
            weak_skills TEXT DEFAULT '[]',
            strong_skills TEXT DEFAULT '[]',
            skill_breakdown TEXT DEFAULT '{}',
            status TEXT DEFAULT 'pending',
            attempt INTEGER DEFAULT 1,
            created_at TEXT DEFAULT (datetime('now')),
            completed_at TEXT
        );

        CREATE TABLE IF NOT EXISTS learning_progress (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            skill TEXT NOT NULL,
            module_index INTEGER DEFAULT 0,
            video_watched INTEGER DEFAULT 0,
            mini_quiz_score INTEGER DEFAULT 0,
            mini_quiz_passed INTEGER DEFAULT 0,
            completed_at TEXT,
            started_at TEXT DEFAULT (datetime('now')),
            UNIQUE(user_id, skill)
        );

        CREATE TABLE IF NOT EXISTS team_pools (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            hackathon_id INTEGER REFERENCES opportunities(id) ON DELETE SET NULL,
            hackathon_name TEXT NOT NULL,
            creator_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            team_name TEXT DEFAULT '',
            team_size INTEGER DEFAULT 4,
            current_size INTEGER DEFAULT 1,
            roles_needed TEXT DEFAULT '[]',
            skills_needed TEXT DEFAULT '[]',
            description TEXT DEFAULT '',
            status TEXT DEFAULT 'open',
            created_at TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS team_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pool_id INTEGER NOT NULL REFERENCES team_pools(id) ON DELETE CASCADE,
            requester_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            message TEXT DEFAULT '',
            status TEXT DEFAULT 'pending',
            created_at TEXT DEFAULT (datetime('now')),
            UNIQUE(pool_id, requester_id)
        );

        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sender_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            receiver_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            content TEXT NOT NULL,
            is_read INTEGER DEFAULT 0,
            created_at TEXT DEFAULT (datetime('now'))
        );

        CREATE INDEX IF NOT EXISTS idx_messages_receiver ON messages(receiver_id, is_read);
        CREATE INDEX IF NOT EXISTS idx_team_pools_status ON team_pools(status);

        CREATE INDEX IF NOT EXISTS idx_opportunities_category ON opportunities(category);
        CREATE INDEX IF NOT EXISTS idx_opportunities_status ON opportunities(status);
        CREATE INDEX IF NOT EXISTS idx_opportunities_deadline ON opportunities(deadline);
        CREATE INDEX IF NOT EXISTS idx_opportunities_reward_type ON opportunities(reward_type);
        CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
        CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);

        CREATE TABLE IF NOT EXISTS ads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            image_url TEXT NOT NULL,
            target_link TEXT NOT NULL,
            status TEXT DEFAULT 'pending',
            created_at TEXT DEFAULT (datetime('now'))
        );
    """)

    conn.commit()
    conn.close()


# ─── User Queries ──────────────────────────────────────────────────────────────

def create_user(email, password_hash, name, role, organization=""):
    conn = get_db()
    try:
        conn.execute(
            "INSERT INTO users (email, password_hash, name, role, organization) VALUES (?,?,?,?,?)",
            (email.lower().strip(), password_hash, name, role, organization),
        )
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()


def get_user_by_email(email):
    conn = get_db()
    row = conn.execute("SELECT * FROM users WHERE email=? AND is_active=1", (email.lower().strip(),)).fetchone()
    conn.close()
    return dict(row) if row else None


def get_user_by_id(user_id):
    conn = get_db()
    row = conn.execute("SELECT * FROM users WHERE id=?", (user_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def update_user_profile(user_id, profile_dict):
    conn = get_db()
    conn.execute("UPDATE users SET profile=? WHERE id=?", (json.dumps(profile_dict), user_id))
    conn.commit()
    conn.close()


def get_all_users():
    conn = get_db()
    rows = conn.execute("SELECT id,email,name,role,organization,is_active,created_at FROM users ORDER BY created_at DESC").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def toggle_user_active(user_id):
    conn = get_db()
    conn.execute("UPDATE users SET is_active = CASE WHEN is_active=1 THEN 0 ELSE 1 END WHERE id=?", (user_id,))
    conn.commit()
    conn.close()


# ─── Opportunity Queries ────────────────────────────────────────────────────────

def insert_opportunity(data):
    """Insert opportunity if hash doesn't exist. Returns (id, is_new)."""
    conn = get_db()
    existing = conn.execute("SELECT id FROM opportunities WHERE hash=?", (data.get("hash"),)).fetchone()
    if existing:
        conn.close()
        return existing["id"], False
    c = conn.cursor()
    c.execute("""
        INSERT INTO opportunities
            (title, category, source, source_url, apply_link, deadline, reward,
             reward_type, prize_amount, eligibility, tags, description, company,
             location, posted_by, status, is_featured, hash)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
    """, (
        data.get("title", ""),
        data.get("category", "hackathon"),
        data.get("source", "Manual"),
        data.get("source_url", ""),
        data.get("apply_link", "#"),
        data.get("deadline"),
        data.get("reward", ""),
        data.get("reward_type", "certificate"),
        data.get("prize_amount", 0),
        data.get("eligibility", "Open to All"),
        json.dumps(data.get("tags", [])),
        data.get("description", ""),
        data.get("company", ""),
        data.get("location", "Remote"),
        data.get("posted_by"),
        data.get("status", "pending"),
        data.get("is_featured", 0),
        data.get("hash"),
    ))
    conn.commit()
    new_id = c.lastrowid
    conn.close()
    return new_id, True


def get_opportunities(
    category=None, reward_type=None, min_prize=0,
    status="approved", search=None, limit=100, offset=0,
    sort="deadline_asc"
):
    conn = get_db()
    query = "SELECT * FROM opportunities WHERE status=?"
    params = [status]

    if category and category != "all":
        query += " AND category=?"
        params.append(category)
    if reward_type and reward_type != "all":
        query += " AND reward_type=?"
        params.append(reward_type)
    if min_prize and int(min_prize) > 0:
        query += " AND prize_amount>=?"
        params.append(int(min_prize))
    if search:
        query += " AND (title LIKE ? OR description LIKE ? OR company LIKE ? OR tags LIKE ?)"
        s = f"%{search}%"
        params += [s, s, s, s]

    order_map = {
        "deadline_asc": "ORDER BY CASE WHEN deadline IS NULL THEN 1 ELSE 0 END, deadline ASC",
        "deadline_desc": "ORDER BY deadline DESC",
        "newest": "ORDER BY scraped_at DESC",
        "prize_desc": "ORDER BY prize_amount DESC",
    }
    query += f" {order_map.get(sort, order_map['deadline_asc'])}"
    query += " LIMIT ? OFFSET ?"
    params += [limit, offset]

    rows = conn.execute(query, params).fetchall()
    conn.close()
    result = []
    for r in rows:
        d = dict(r)
        d["tags"] = json.loads(d.get("tags") or "[]")
        result.append(d)
    return result


def get_opportunity_by_id(opp_id):
    conn = get_db()
    row = conn.execute("SELECT * FROM opportunities WHERE id=?", (opp_id,)).fetchone()
    conn.close()
    if row:
        d = dict(row)
        d["tags"] = json.loads(d.get("tags") or "[]")
        return d
    return None


def get_opportunities_by_user(user_id):
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM opportunities WHERE posted_by=? ORDER BY scraped_at DESC", (user_id,)
    ).fetchall()
    conn.close()
    result = []
    for r in rows:
        d = dict(r)
        d["tags"] = json.loads(d.get("tags") or "[]")
        result.append(d)
    return result


def update_opportunity_status(opp_id, status):
    conn = get_db()
    conn.execute("UPDATE opportunities SET status=? WHERE id=?", (status, opp_id))
    conn.commit()
    conn.close()


def delete_opportunity(opp_id, user_id=None):
    conn = get_db()
    if user_id:
        conn.execute("DELETE FROM opportunities WHERE id=? AND posted_by=?", (opp_id, user_id))
    else:
        conn.execute("DELETE FROM opportunities WHERE id=?", (opp_id,))
    conn.commit()
    conn.close()


def get_pending_opportunities():
    conn = get_db()
    rows = conn.execute(
        "SELECT o.*, u.name as poster_name, u.email as poster_email FROM opportunities o "
        "LEFT JOIN users u ON o.posted_by=u.id WHERE o.status='pending' ORDER BY o.scraped_at DESC"
    ).fetchall()
    conn.close()
    result = []
    for r in rows:
        d = dict(r)
        d["tags"] = json.loads(d.get("tags") or "[]")
        result.append(d)
    return result


def mark_ai_analyzed(opp_id, score=1.0):
    conn = get_db()
    conn.execute("UPDATE opportunities SET ai_analyzed=1, legitimacy_score=? WHERE id=?", (score, opp_id))
    conn.commit()
    conn.close()


# ─── Saved Opportunities ───────────────────────────────────────────────────────

def save_opportunity(user_id, opp_id):
    conn = get_db()
    try:
        conn.execute("INSERT INTO saved_opportunities (user_id, opportunity_id) VALUES (?,?)", (user_id, opp_id))
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        conn.close()
        return False


def unsave_opportunity(user_id, opp_id):
    conn = get_db()
    conn.execute("DELETE FROM saved_opportunities WHERE user_id=? AND opportunity_id=?", (user_id, opp_id))
    conn.commit()
    conn.close()


def get_saved_ids(user_id):
    conn = get_db()
    rows = conn.execute("SELECT opportunity_id FROM saved_opportunities WHERE user_id=?", (user_id,)).fetchall()
    conn.close()
    return {r["opportunity_id"] for r in rows}


def get_saved_opportunities(user_id):
    conn = get_db()
    rows = conn.execute("""
        SELECT o.* FROM opportunities o
        JOIN saved_opportunities s ON o.id=s.opportunity_id
        WHERE s.user_id=? AND o.status='approved'
        ORDER BY s.saved_at DESC
    """, (user_id,)).fetchall()
    conn.close()
    result = []
    for r in rows:
        d = dict(r)
        d["tags"] = json.loads(d.get("tags") or "[]")
        result.append(d)
    return result


# ─── Scrape Logs ───────────────────────────────────────────────────────────────

def log_scrape(source, status, count_new=0, count_dup=0, error=""):
    conn = get_db()
    conn.execute(
        "INSERT INTO scrape_logs (source, status, count_new, count_duplicate, error) VALUES (?,?,?,?,?)",
        (source, status, count_new, count_dup, error),
    )
    conn.commit()
    conn.close()


def get_scrape_logs(limit=50):
    conn = get_db()
    rows = conn.execute("SELECT * FROM scrape_logs ORDER BY ran_at DESC LIMIT ?", (limit,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ─── Stats ─────────────────────────────────────────────────────────────────────

def get_stats():
    conn = get_db()
    stats = {}
    stats["total_opportunities"] = conn.execute("SELECT COUNT(*) FROM opportunities WHERE status='approved'").fetchone()[0]
    stats["total_users"] = conn.execute("SELECT COUNT(*) FROM users WHERE role='student'").fetchone()[0]
    stats["total_organizers"] = conn.execute("SELECT COUNT(*) FROM users WHERE role='organizer'").fetchone()[0]
    stats["total_recruiters"] = conn.execute("SELECT COUNT(*) FROM users WHERE role='recruiter'").fetchone()[0]
    stats["pending_count"] = conn.execute("SELECT COUNT(*) FROM opportunities WHERE status='pending'").fetchone()[0]
    stats["hackathons"] = conn.execute("SELECT COUNT(*) FROM opportunities WHERE category='hackathon' AND status='approved'").fetchone()[0]
    stats["internships"] = conn.execute("SELECT COUNT(*) FROM opportunities WHERE category='internship' AND status='approved'").fetchone()[0]
    stats["scholarships"] = conn.execute("SELECT COUNT(*) FROM opportunities WHERE category='scholarship' AND status='approved'").fetchone()[0]
    stats["workshops"] = conn.execute("SELECT COUNT(*) FROM opportunities WHERE category='workshop' AND status='approved'").fetchone()[0]
    stats["cash_prizes"] = conn.execute("SELECT COUNT(*) FROM opportunities WHERE reward_type='cash' AND status='approved'").fetchone()[0]
    conn.close()
    return stats


def get_notifications(user_id, limit=10):
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM notifications WHERE user_id=? ORDER BY created_at DESC LIMIT ?", (user_id, limit)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def add_notification(user_id, message, link=""):
    conn = get_db()
    conn.execute("INSERT INTO notifications (user_id, message, link) VALUES (?,?,?)", (user_id, message, link))
    conn.commit()
    conn.close()


def mark_notifications_read(user_id):
    conn = get_db()
    conn.execute("UPDATE notifications SET is_read=1 WHERE user_id=?", (user_id,))
    conn.commit()
    conn.close()


# ─── Social Credentials ────────────────────────────────────────────────────────

def get_social_credentials(platform: str) -> dict:
    conn = get_db()
    row = conn.execute("SELECT * FROM social_credentials WHERE platform=?", (platform,)).fetchone()
    conn.close()
    if row:
        d = dict(row)
        try:
            d["credentials"] = json.loads(d.get("credentials") or "{}")
        except Exception:
            d["credentials"] = {}
        return d
    return {"platform": platform, "credentials": {}, "is_active": 0}


def get_all_social_credentials() -> list:
    conn = get_db()
    rows = conn.execute("SELECT * FROM social_credentials ORDER BY platform").fetchall()
    conn.close()
    result = []
    for r in rows:
        d = dict(r)
        try:
            d["credentials"] = json.loads(d.get("credentials") or "{}")
        except Exception:
            d["credentials"] = {}
        result.append(d)
    return result


def save_social_credentials(platform: str, credentials: dict, is_active: bool = True):
    conn = get_db()
    conn.execute("""
        INSERT OR REPLACE INTO social_credentials (platform, credentials, is_active, updated_at)
        VALUES (?, ?, ?, datetime('now'))
    """, (platform, json.dumps(credentials), 1 if is_active else 0))
    conn.commit()
    conn.close()


def update_social_scrape_time(platform: str):
    conn = get_db()
    conn.execute("""
        UPDATE social_credentials
        SET last_scraped=datetime('now'), scrape_count=scrape_count+1
        WHERE platform=?
    """, (platform,))
    conn.commit()
    conn.close()


# ─── Resume Functions ──────────────────────────────────────────────────────────

def save_resume(user_id: int, file_path: str, skills: list, domains: list,
                experience_level: str, college: str, year: str, raw_text: str):
    conn = get_db()
    conn.execute("""
        INSERT OR REPLACE INTO resumes
            (user_id, file_path, raw_text, skills, domains, experience_level,
             college_extracted, year_extracted, updated_at)
        VALUES (?,?,?,?,?,?,?,?,datetime('now'))
    """, (user_id, file_path, raw_text[:5000],
          json.dumps(skills), json.dumps(domains),
          experience_level, college, year))
    conn.commit()
    conn.close()


def get_resume(user_id: int) -> dict | None:
    conn = get_db()
    row = conn.execute("SELECT * FROM resumes WHERE user_id=?", (user_id,)).fetchone()
    conn.close()
    if not row:
        return None
    d = dict(row)
    d["skills"] = json.loads(d.get("skills") or "[]")
    d["domains"] = json.loads(d.get("domains") or "[]")
    return d


def has_resume(user_id: int) -> bool:
    conn = get_db()
    row = conn.execute("SELECT id FROM resumes WHERE user_id=?", (user_id,)).fetchone()
    conn.close()
    return row is not None


# ─── Assessment Functions ──────────────────────────────────────────────────────

def save_assessment_questions(user_id: int, questions: list, attempt: int = 1):
    """Store generated quiz questions (pending state) for a student."""
    conn = get_db()
    # Remove any previous unanswered quiz for this user
    conn.execute("DELETE FROM student_assessments WHERE user_id=? AND status='pending'", (user_id,))
    # 4 columns → 4 values (user_id, questions, attempt, status)
    conn.execute("""
        INSERT INTO student_assessments (user_id, questions, attempt, status)
        VALUES (?, ?, ?, 'pending')
    """, (user_id, json.dumps(questions), attempt))
    conn.commit()
    conn.close()



def get_pending_assessment(user_id: int) -> dict | None:
    conn = get_db()
    row = conn.execute(
        "SELECT * FROM student_assessments WHERE user_id=? AND status='pending' ORDER BY created_at DESC LIMIT 1",
        (user_id,)
    ).fetchone()
    conn.close()
    if not row:
        return None
    d = dict(row)
    d["questions"] = json.loads(d.get("questions") or "[]")
    return d


def complete_assessment(assessment_id: int, answers: list, score: int, total: int,
                        passed: bool, weak_skills: list, strong_skills: list, breakdown: dict):
    conn = get_db()
    conn.execute("""
        UPDATE student_assessments
        SET student_answers=?, score=?, total=?, passed=?, weak_skills=?, strong_skills=?,
            skill_breakdown=?, status='completed', completed_at=datetime('now')
        WHERE id=?
    """, (json.dumps(answers), score, total, 1 if passed else 0,
          json.dumps(weak_skills), json.dumps(strong_skills),
          json.dumps(breakdown), assessment_id))
    conn.commit()
    conn.close()


def get_latest_assessment(user_id: int) -> dict | None:
    conn = get_db()
    row = conn.execute(
        "SELECT * FROM student_assessments WHERE user_id=? AND status='completed' ORDER BY completed_at DESC LIMIT 1",
        (user_id,)
    ).fetchone()
    conn.close()
    if not row:
        return None
    d = dict(row)
    for f in ["questions", "student_answers", "weak_skills", "strong_skills"]:
        d[f] = json.loads(d.get(f) or "[]")
    d["skill_breakdown"] = json.loads(d.get("skill_breakdown") or "{}")
    return d


def get_assessment_attempt_count(user_id: int) -> int:
    conn = get_db()
    row = conn.execute(
        "SELECT COUNT(*) FROM student_assessments WHERE user_id=? AND status='completed'",
        (user_id,)
    ).fetchone()
    conn.close()
    return row[0] if row else 0


# ─── Learning Progress Functions ───────────────────────────────────────────────

def mark_video_watched(user_id: int, skill: str, module_index: int):
    conn = get_db()
    conn.execute("""
        INSERT INTO learning_progress (user_id, skill, module_index, video_watched)
        VALUES (?,?,?,1)
        ON CONFLICT(user_id, skill) DO UPDATE SET video_watched=1
    """, (user_id, skill, module_index))
    conn.commit()
    conn.close()


def complete_learning_module(user_id: int, skill: str, mini_score: int, mini_passed: bool):
    conn = get_db()
    if mini_passed:
        conn.execute("""
            INSERT INTO learning_progress
                (user_id, skill, mini_quiz_score, mini_quiz_passed, completed_at)
            VALUES (?, ?, ?, 1, datetime('now'))
            ON CONFLICT(user_id, skill) DO UPDATE
                SET mini_quiz_score=excluded.mini_quiz_score,
                    mini_quiz_passed=1,
                    completed_at=datetime('now')
        """, (user_id, skill, mini_score))
    else:
        conn.execute("""
            INSERT INTO learning_progress
                (user_id, skill, mini_quiz_score, mini_quiz_passed, completed_at)
            VALUES (?, ?, ?, 0, NULL)
            ON CONFLICT(user_id, skill) DO UPDATE
                SET mini_quiz_score=excluded.mini_quiz_score,
                    mini_quiz_passed=0
        """, (user_id, skill, mini_score))
    conn.commit()
    conn.close()



def get_learning_progress(user_id: int) -> list:
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM learning_progress WHERE user_id=? ORDER BY module_index ASC",
        (user_id,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def count_completed_modules(user_id: int) -> int:
    conn = get_db()
    row = conn.execute(
        "SELECT COUNT(*) FROM learning_progress WHERE user_id=? AND mini_quiz_passed=1",
        (user_id,)
    ).fetchone()
    conn.close()
    return row[0] if row else 0


# ─── Talent Board (for Recruiters) ────────────────────────────────────────────

def get_talent_board(skill_filter: str = None, min_score: int = 7,
                     limit: int = 200) -> list:
    """
    Return students for the recruiter Talent Board.
    Includes:
      - Students who passed the AI assessment (score >= min_score)
      - Plus students who completed the learning path (course_completed=True)
    Adds flags: passed, course_completed, is_job_seeking (from profile)
    """
    conn = get_db()
    query = """
        SELECT
            u.id, u.name, u.email, u.organization,
            u.profile, u.created_at as joined,
            r.file_path as resume_path,
            r.skills as resume_skills,
            r.domains, r.experience_level, r.college_extracted, r.year_extracted,
            sa.score, sa.total, sa.strong_skills,
            sa.passed,
            sa.completed_at as assessed_at,
            (SELECT COUNT(*) FROM learning_progress lp
             WHERE lp.user_id = u.id AND lp.mini_quiz_passed = 1) as modules_done
        FROM users u
        JOIN resumes r ON r.user_id = u.id
        LEFT JOIN student_assessments sa ON sa.user_id = u.id
            AND sa.id = (
                SELECT MAX(id) FROM student_assessments
                WHERE user_id = u.id AND status = 'completed'
            )
        WHERE u.role = 'student'
          AND (
              (sa.passed = 1 AND sa.score >= ?)
              OR
              (SELECT COUNT(*) FROM learning_progress lp2
               WHERE lp2.user_id = u.id AND lp2.mini_quiz_passed = 1) >= 1
          )
    """
    params = [min_score]
    if skill_filter:
        query += " AND (r.skills LIKE ? OR sa.strong_skills LIKE ?)"
        s = f"%{skill_filter}%"
        params += [s, s]
    query += " ORDER BY sa.score DESC NULLS LAST, sa.completed_at DESC LIMIT ?"
    params.append(limit)

    rows = conn.execute(query, params).fetchall()
    conn.close()

    result = []
    for r in rows:
        d = dict(r)
        d["resume_skills"] = json.loads(d.get("resume_skills") or "[]")
        d["domains"] = json.loads(d.get("domains") or "[]")
        d["strong_skills"] = json.loads(d.get("strong_skills") or "[]")
        d["score"] = d.get("score") or 0
        d["total"] = d.get("total") or 10
        d["passed"] = bool(d.get("passed"))
        d["course_completed"] = (d.get("modules_done") or 0) >= 1
        try:
            profile = json.loads(d.get("profile") or "{}")
        except Exception:
            profile = {}
        d["linkedin"] = profile.get("linkedin", "")
        d["github"] = profile.get("github", "")
        d["year"] = d.get("year_extracted") or profile.get("year", "")
        d["college"] = d.get("college_extracted") or profile.get("college", "")
        d["branch"] = profile.get("branch", "")
        d["is_job_seeking"] = profile.get("open_to_work", True)
        # Determine badge
        if d["passed"]:
            d["status_badge"] = "verified"
        elif d["course_completed"]:
            d["status_badge"] = "course_done"
        else:
            d["status_badge"] = "resume_only"
        result.append(d)
    return result


def get_skill_matched_students(skills: list, limit: int = 20) -> list:
    """Return students whose resume skills match any of the given skills."""
    if not skills:
        return []
    conn = get_db()
    rows = conn.execute("""
        SELECT u.id, u.name, u.email, u.profile,
               r.skills as resume_skills, r.college_extracted, r.year_extracted,
               sa.score, sa.passed
        FROM users u
        JOIN resumes r ON r.user_id = u.id
        LEFT JOIN student_assessments sa ON sa.user_id = u.id
            AND sa.id = (SELECT MAX(id) FROM student_assessments
                         WHERE user_id=u.id AND status='completed')
        WHERE u.role='student'
        ORDER BY sa.score DESC NULLS LAST
        LIMIT ?
    """, (limit * 3,)).fetchall()
    conn.close()
    matched = []
    for r in rows:
        d = dict(r)
        d["resume_skills"] = json.loads(d.get("resume_skills") or "[]")
        # Check overlap
        student_skills_lower = {s.lower() for s in d["resume_skills"]}
        query_lower = {s.lower() for s in skills}
        overlap = student_skills_lower & query_lower
        if overlap:
            d["matched_skills"] = list(overlap)
            d["score"] = d.get("score") or 0
            d["passed"] = bool(d.get("passed"))
            try:
                prof = json.loads(d.get("profile") or "{}")
            except Exception:
                prof = {}
            d["college"] = d.get("college_extracted") or prof.get("college", "")
            d["linkedin"] = prof.get("linkedin", "")
            matched.append(d)
    matched.sort(key=lambda x: len(x["matched_skills"]), reverse=True)
    return matched[:limit]



# ─── Team Pool Functions ───────────────────────────────────────────────────────

def create_team_pool(creator_id: int, hackathon_name: str, team_name: str,
                     team_size: int, roles_needed: list, skills_needed: list,
                     description: str, hackathon_id: int = None) -> int:
    conn = get_db()
    cur = conn.execute("""
        INSERT INTO team_pools
            (creator_id, hackathon_id, hackathon_name, team_name, team_size,
             roles_needed, skills_needed, description)
        VALUES (?,?,?,?,?,?,?,?)
    """, (creator_id, hackathon_id, hackathon_name, team_name, team_size,
          json.dumps(roles_needed), json.dumps(skills_needed), description))
    pool_id = cur.lastrowid
    conn.commit()
    conn.close()
    return pool_id


def get_team_pools(status: str = "open", skill: str = None,
                   limit: int = 50) -> list:
    conn = get_db()
    query = """
        SELECT tp.*, u.name as creator_name, u.profile as creator_profile
        FROM team_pools tp
        JOIN users u ON u.id = tp.creator_id
        WHERE tp.status = ?
    """
    params = [status]
    if skill:
        query += " AND (tp.skills_needed LIKE ? OR tp.roles_needed LIKE ?)"
        s = f"%{skill}%"
        params += [s, s]
    query += " ORDER BY tp.created_at DESC LIMIT ?"
    params.append(limit)
    rows = conn.execute(query, params).fetchall()
    conn.close()
    result = []
    for r in rows:
        d = dict(r)
        d["roles_needed"] = json.loads(d.get("roles_needed") or "[]")
        d["skills_needed"] = json.loads(d.get("skills_needed") or "[]")
        try:
            prof = json.loads(d.get("creator_profile") or "{}")
        except Exception:
            prof = {}
        d["creator_college"] = prof.get("college", "")
        d["creator_branch"] = prof.get("branch", "")
        result.append(d)
    return result


def get_team_pool(pool_id: int) -> dict | None:
    conn = get_db()
    row = conn.execute("""
        SELECT tp.*, u.name as creator_name, u.email as creator_email,
               u.profile as creator_profile
        FROM team_pools tp JOIN users u ON u.id = tp.creator_id
        WHERE tp.id = ?
    """, (pool_id,)).fetchone()
    conn.close()
    if not row:
        return None
    d = dict(row)
    d["roles_needed"] = json.loads(d.get("roles_needed") or "[]")
    d["skills_needed"] = json.loads(d.get("skills_needed") or "[]")
    return d


def get_my_team_pools(user_id: int) -> list:
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM team_pools WHERE creator_id=? ORDER BY created_at DESC",
        (user_id,)
    ).fetchall()
    conn.close()
    result = []
    for r in rows:
        d = dict(r)
        d["roles_needed"] = json.loads(d.get("roles_needed") or "[]")
        d["skills_needed"] = json.loads(d.get("skills_needed") or "[]")
        result.append(d)
    return result


def request_join_pool(pool_id: int, requester_id: int, message: str) -> bool:
    conn = get_db()
    try:
        conn.execute("""
            INSERT INTO team_requests (pool_id, requester_id, message)
            VALUES (?,?,?)
        """, (pool_id, requester_id, message))
        conn.commit()
        return True
    except Exception:
        return False
    finally:
        conn.close()


def get_pool_requests(pool_id: int) -> list:
    conn = get_db()
    rows = conn.execute("""
        SELECT tr.*, u.name as requester_name, u.email as requester_email,
               u.profile as requester_profile
        FROM team_requests tr JOIN users u ON u.id = tr.requester_id
        WHERE tr.pool_id = ? ORDER BY tr.created_at DESC
    """, (pool_id,)).fetchall()
    conn.close()
    result = []
    for r in rows:
        d = dict(r)
        try:
            prof = json.loads(d.get("requester_profile") or "{}")
        except Exception:
            prof = {}
        d["requester_college"] = prof.get("college", "")
        d["requester_branch"] = prof.get("branch", "")
        d["requester_skills"] = prof.get("skills", [])
        result.append(d)
    return result


def respond_to_request(request_id: int, action: str):
    """action: 'accepted' or 'rejected'"""
    conn = get_db()
    conn.execute(
        "UPDATE team_requests SET status=? WHERE id=?",
        (action, request_id)
    )
    if action == "accepted":
        # Get pool_id and increment current_size
        row = conn.execute(
            "SELECT pool_id FROM team_requests WHERE id=?", (request_id,)
        ).fetchone()
        if row:
            conn.execute(
                "UPDATE team_pools SET current_size=current_size+1 WHERE id=?",
                (row["pool_id"],)
            )
            # Auto-close if full
            conn.execute("""
                UPDATE team_pools SET status='full'
                WHERE id=? AND current_size >= team_size
            """, (row["pool_id"],))
    conn.commit()
    conn.close()


def has_requested_pool(pool_id: int, user_id: int) -> bool:
    conn = get_db()
    row = conn.execute(
        "SELECT id FROM team_requests WHERE pool_id=? AND requester_id=?",
        (pool_id, user_id)
    ).fetchone()
    conn.close()
    return row is not None


def close_team_pool(pool_id: int):
    conn = get_db()
    conn.execute("UPDATE team_pools SET status='closed' WHERE id=?", (pool_id,))
    conn.commit()
    conn.close()


# ─── Chat/Messaging Functions ──────────────────────────────────────────────────

def send_message(sender_id: int, receiver_id: int, content: str) -> int:
    conn = get_db()
    cur = conn.execute("""
        INSERT INTO messages (sender_id, receiver_id, content)
        VALUES (?,?,?)
    """, (sender_id, receiver_id, content.strip()))
    msg_id = cur.lastrowid
    conn.commit()
    conn.close()
    return msg_id


def get_conversation(user_a: int, user_b: int, limit: int = 100) -> list:
    conn = get_db()
    rows = conn.execute("""
        SELECT m.*, su.name as sender_name, ru.name as receiver_name
        FROM messages m
        JOIN users su ON su.id = m.sender_id
        JOIN users ru ON ru.id = m.receiver_id
        WHERE (m.sender_id=? AND m.receiver_id=?)
           OR (m.sender_id=? AND m.receiver_id=?)
        ORDER BY m.created_at ASC
        LIMIT ?
    """, (user_a, user_b, user_b, user_a, limit)).fetchall()
    # Mark as read
    conn.execute("""
        UPDATE messages SET is_read=1
        WHERE receiver_id=? AND sender_id=? AND is_read=0
    """, (user_a, user_b))
    conn.commit()
    conn.close()
    return [dict(r) for r in rows]


def get_new_messages(user_a: int, user_b: int, after_id: int) -> list:
    """AJAX poll — fetch messages after a given ID."""
    conn = get_db()
    rows = conn.execute("""
        SELECT m.*, su.name as sender_name
        FROM messages m JOIN users su ON su.id = m.sender_id
        WHERE ((m.sender_id=? AND m.receiver_id=?)
            OR (m.sender_id=? AND m.receiver_id=?))
          AND m.id > ?
        ORDER BY m.id ASC
    """, (user_a, user_b, user_b, user_a, after_id)).fetchall()
    conn.execute(
        "UPDATE messages SET is_read=1 WHERE receiver_id=? AND sender_id=? AND is_read=0",
        (user_a, user_b)
    )
    conn.commit()
    conn.close()
    return [dict(r) for r in rows]


def get_chat_list(user_id: int) -> list:
    """Return all conversations with latest message + unread count."""
    conn = get_db()
    rows = conn.execute("""
        WITH convs AS (
            -- For every message involving this user, identify the "other" person
            SELECT
                CASE WHEN sender_id=? THEN receiver_id ELSE sender_id END AS other_id,
                MAX(id) AS last_msg_id,
                SUM(CASE WHEN receiver_id=? AND is_read=0 THEN 1 ELSE 0 END) AS unread
            FROM messages
            WHERE sender_id=? OR receiver_id=?
            GROUP BY
                CASE WHEN sender_id=? THEN receiver_id ELSE sender_id END
        )
        SELECT
            c.other_id,
            u.name  AS other_name,
            u.role  AS other_role,
            c.last_msg_id,
            m.content    AS last_content,
            m.created_at AS last_time,
            c.unread
        FROM convs c
        JOIN users    u ON u.id = c.other_id
        JOIN messages m ON m.id = c.last_msg_id
        ORDER BY c.last_msg_id DESC
    """, (user_id, user_id, user_id, user_id, user_id)).fetchall()
    conn.close()
    return [dict(r) for r in rows]

# ─── Ads Logic ─────────────────────────────────────────────────────────────

def create_ad(title: str, image_url: str, target_link: str) -> None:
    conn = get_db()
    conn.execute(
        "INSERT INTO ads (title, image_url, target_link) VALUES (?, ?, ?)",
        (title, image_url, target_link)
    )
    conn.commit()
    conn.close()

def get_ads(status=None) -> list:
    conn = get_db()
    if status is None:
        rows = conn.execute("SELECT * FROM ads ORDER BY id DESC").fetchall()
    else:
        rows = conn.execute("SELECT * FROM ads WHERE status=? ORDER BY id DESC", (status,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def update_ad_status(ad_id: int, status: str) -> None:
    conn = get_db()
    conn.execute("UPDATE ads SET status=? WHERE id=?", (status, ad_id))
    conn.commit()
    conn.close()

def delete_ad(ad_id: int) -> None:
    conn = get_db()
    conn.execute("DELETE FROM ads WHERE id=?", (ad_id,))
    conn.commit()
    conn.close()
def get_unread_count(user_id: int) -> int:
    conn = get_db()
    row = conn.execute(
        "SELECT COUNT(*) FROM messages WHERE receiver_id=? AND is_read=0",
        (user_id,)
    ).fetchone()
    conn.close()
    return row[0] if row else 0
