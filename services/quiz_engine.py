"""
Quiz Engine — generates 10-question AI MCQ assessments using Gemini,
scores student answers, and determines pass/fail (cutoff: 7/10).
"""
import json, re, logging, random
from services.ai_service import call_gemini

logger = logging.getLogger(__name__)

PASS_MARK = 7           # out of TOTAL_QUESTIONS
TOTAL_QUESTIONS = 10
MINI_QUIZ_TOTAL = 3
MINI_QUIZ_PASS = 2      # need 2/3 to pass learning mini-quiz


# ── Fallback questions (if Gemini fails) ─────────────────────────────────────

GENERIC_FALLBACK = [
    {
        "question": "What is the primary role of a 'variable' in programming?",
        "options": ["To store data for processing", "To connect to the internet", "To design a user interface", "To delete files"],
        "correct_index": 0, "explanation": "Variables are used to store and manipulate data.", "skill": "Programming", "difficulty": "easy"
    },
    {
        "question": "Which data structure follows the 'First In, First Out' (FIFO) principle?",
        "options": ["Stack", "Queue", "Binary Tree", "Linked List"],
        "correct_index": 1, "explanation": "A Queue is FIFO (like a line of people).", "skill": "DSA", "difficulty": "easy"
    },
    {
        "question": "What does a 'git commit' do?",
        "options": ["Downloads code", "Saves a snapshot of your changes", "Deletes a repository", "Runs the server"],
        "correct_index": 1, "explanation": "A commit saves your local changes to the project history.", "skill": "Git", "difficulty": "easy"
    },
    {
        "question": "In Web Development, what is CSS mainly used for?",
        "options": ["Handling data", "Styling and layout", "Connecting to a database", "Optimizing algorithms"],
        "correct_index": 1, "explanation": "CSS (Cascading Style Sheets) is for visual styling.", "skill": "Web Dev", "difficulty": "easy"
    },
    {
        "question": "Which of these is a Python data type for storing unique items?",
        "options": ["List", "Dictionary", "Set", "Tuple"],
        "correct_index": 2, "explanation": "A Set in Python stores unique, unordered elements.", "skill": "Python", "difficulty": "medium"
    },
    {
        "question": "What is the main goal of Agile methodology?",
        "options": ["To write code faster", "To deliver value to users through small steps", "To avoid testing", "To use more tools"],
        "correct_index": 1, "explanation": "Agile focuses on iterative delivery and user feedback.", "skill": "Project Management", "difficulty": "medium"
    },
    {
        "question": "What does 'API' stand for?",
        "options": ["Application Programming Interface", "Advanced Program Integration", "Account Process Input", "Automatic Programming Item"],
        "correct_index": 0, "explanation": "API is the set of tools for building software and talking to other apps.", "skill": "Programming", "difficulty": "easy"
    },
    {
        "question": "Which of these is a NoSQL database?",
        "options": ["PostgreSQL", "MySQL", "MongoDB", "Oracle"],
        "correct_index": 2, "explanation": "MongoDB is a document-based NoSQL database.", "skill": "Databases", "difficulty": "medium"
    },
    {
        "question": "What is the 4-step process of Software Development Life Cycle (SDLC)?",
        "options": ["Code, Test, Deploy, Forget", "Plan, Design, Build, Test", "Eat, Sleep, Code, Repeat", "Start, Finish, Ship, Relax"],
        "correct_index": 1, "explanation": "SDLC involves planning, designing, building, and testing software.", "skill": "Software Engineering", "difficulty": "medium"
    },
    {
        "question": "Why is 'debugging' important?",
        "options": ["To make code look better", "To find and fix errors in software", "To speed up the computer", "To change the colors of the UI"],
        "correct_index": 1, "explanation": "Debugging is the process of identifying and removing bugs from code.", "skill": "Programming", "difficulty": "easy"
    }
]


def generate_quiz(skills: list, num_questions: int = TOTAL_QUESTIONS) -> list:
    """Generate MCQ questions tailored to the student's skill set."""
    if not skills:
        return _build_shuffled_fallback(num_questions)

    skill_str = ", ".join(skills[:6])
    prompt = f"""You are a senior technical interviewer. Generate exactly {num_questions} MCQs for a student.
Skills: {skill_str}

Return ONLY a JSON array:
[
  {{
    "question": "Text",
    "options": ["A", "B", "C", "D"],
    "correct_index": 0,
    "explanation": "Why",
    "skill": "Skill",
    "difficulty": "medium"
  }}
]"""

    raw = call_gemini(prompt)
    if not raw:
        return _build_shuffled_fallback(num_questions)

    try:
        raw = re.sub(r"```(?:json)?", "", raw).strip().rstrip("`").strip()
        m = re.search(r'\[.*\]', raw, re.DOTALL)
        if m: raw = m.group(0)
        
        questions = json.loads(raw)
        if isinstance(questions, list) and len(questions) >= 5:
            return questions[:num_questions]
        return _build_shuffled_fallback(num_questions)
    except Exception:
        return _build_shuffled_fallback(num_questions)


def _build_shuffled_fallback(n: int) -> list:
    """Return n randomized questions from the high-quality backup pool."""
    pool = list(GENERIC_FALLBACK)
    random.shuffle(pool)
    return pool[:n]


def score_quiz(questions: list, student_answers: list) -> dict:
    """Calculate score and identify weak/strong skills."""
    if not questions:
        return {"score": 0, "total": 0, "passed": False, "skill_breakdown": {}, "incorrect": []}

    score = 0
    skill_correct = {}
    skill_total = {}
    incorrect = []

    for i, q in enumerate(questions):
        skill = q.get("skill", "General")
        skill_total[skill] = skill_total.get(skill, 0) + 1
        chosen = student_answers[i] if i < len(student_answers) else -1

        if chosen == q["correct_index"]:
            score += 1
            skill_correct[skill] = skill_correct.get(skill, 0) + 1
        else:
            incorrect.append({
                "question": q["question"],
                "your_answer": q["options"][chosen] if 0 <= chosen <= 3 else "Not answered",
                "correct_answer": q["options"][q["correct_index"]],
                "explanation": q.get("explanation", ""),
                "skill": skill,
            })

    # Skill breakdown: {skill: {"correct": N, "total": M, "pct": X}}
    breakdown = {}
    for skill, total in skill_total.items():
        correct = skill_correct.get(skill, 0)
        breakdown[skill] = {
            "correct": correct,
            "total": total,
            "pct": round((correct / total) * 100),
            "strong": correct >= total * 0.7,
        }

    weak_skills = [s for s, d in breakdown.items() if not d["strong"]]

    return {
        "score": score,
        "total": len(questions),
        "passed": score >= PASS_MARK,
        "percentage": round((score / len(questions)) * 100),
        "skill_breakdown": breakdown,
        "weak_skills": weak_skills,
        "strong_skills": [s for s, d in breakdown.items() if d["strong"]],
        "incorrect": incorrect,
    }


def generate_mini_quiz(skill: str) -> list:
    """Generate 3 mini-quiz questions for learning path module."""
    prompt = f"""Generate exactly 3 multiple-choice questions to test basic understanding of {skill}.

Return ONLY a JSON array:
[
  {{
    "question": "Simple practical question",
    "options": ["A", "B", "C", "D"],
    "correct_index": 0,
    "explanation": "Why this is correct"
  }}
]

Make questions simple (beginner-friendly) since student just watched a tutorial video."""

    raw = call_gemini(prompt)
    if not raw:
        return _mini_fallback(skill)
    raw = re.sub(r"```(?:json)?", "", raw).strip().rstrip("`").strip()
    m = re.search(r'\[.*\]', raw, re.DOTALL)
    if m:
        raw = m.group(0)
    try:
        questions = json.loads(raw)
        valid = [q for q in questions if len(q.get("options", [])) == 4 and "question" in q]
        if len(valid) >= 2:
            return valid[:3]
    except Exception:
        pass
    return _mini_fallback(skill)


def _mini_fallback(skill: str) -> list:
    return [
        {
            "question": f"Which of the following is a core concept in {skill}?",
            "options": ["Variables", "Cooking", "Painting", "Swimming"],
            "correct_index": 0,
            "explanation": f"Variables are fundamental in {skill}.",
        },
        {
            "question": f"What is the primary use case of {skill}?",
            "options": ["Building applications", "Making music", "Cooking food", "Drawing pictures"],
            "correct_index": 0,
            "explanation": f"{skill} is used to build software applications.",
        },
        {
            "question": f"Which company is famous for contributing to {skill}?",
            "options": ["Google/Meta/Microsoft", "McDonald's", "Nike", "Toyota"],
            "correct_index": 0,
            "explanation": "Major tech companies drive the development of programming technologies.",
        },
    ]
