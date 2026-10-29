"""
Resume parser — sends the PDF directly to Gemini (multimodal) for skill extraction.
No intermediate text extraction; Gemini reads the document natively.
"""
import os, re, logging, json, time
from config import GEMINI_API_KEY, GEMINI_MODEL

logger = logging.getLogger(__name__)

SKILL_ALIASES = {
    "py": "Python", "python3": "Python",
    "js": "JavaScript", "typescript": "TypeScript", "ts": "TypeScript",
    "cpp": "C++", "ml": "Machine Learning", "dl": "Deep Learning",
    "nlp": "NLP", "cv": "Computer Vision", "ds": "Data Science",
    "reactjs": "React", "react.js": "React",
    "nodejs": "Node.js", "node.js": "Node.js",
    "expressjs": "Express.js", "mongodb": "MongoDB",
    "postgresql": "PostgreSQL", "postgres": "PostgreSQL",
    "aws": "AWS", "docker": "Docker", "kubernetes": "Kubernetes",
    "html5": "HTML/CSS", "css3": "HTML/CSS",
    "dsa": "DSA", "data structures": "DSA",
    "django": "Django", "flask": "Flask", "fastapi": "FastAPI",
    "tensorflow": "TensorFlow", "pytorch": "PyTorch",
    "pandas": "Pandas", "numpy": "NumPy",
    "spring boot": "Spring Boot",
}


def normalize_skill(raw: str) -> str:
    s = raw.strip().lower()
    return SKILL_ALIASES.get(s, raw.strip().title())


from pypdf import PdfReader
from services.ai_service import call_gemini

# Update prompt for TEXT analysis (since we extract text locally now)
RESUME_PROMPT_TEXT = """You are an expert resume analyzer. Analyze the following resume text.

Extract and return ONLY a valid JSON object (no markdown, no explanation) exactly in this format:
{
  "skills": ["Skill1", "Skill2"],
  "domains": ["Domain1"],
  "experience_level": "fresher",
  "college": "College Name",
  "year": "Year",
  "raw_text_summary": "One sentence summary"
}

Resume Text:
{text}"""


def _extract_text_from_pdf(file_path: str) -> str:
    """Extract raw text from PDF using pypdf."""
    try:
        reader = PdfReader(file_path)
        text = ""
        for page in reader.pages:
            t = page.extract_text()
            if t: text += t + "\n"
        return text.strip()
    except Exception as e:
        logger.error(f"[Resume] PDF text extraction failed: {e}")
        return ""


def parse_resume(file_path: str) -> dict:
    """
    Full pipeline using Local Extraction + Gemini CLI:
      PDF file -> Extract Text (pypdf) -> Gemini CLI Analysis -> structured dict
    """
    if not os.path.exists(file_path):
        logger.error(f"[Resume] File not found: {file_path}")
        return {"skills": [], "domains": [], "experience_level": "fresher",
                "college": "", "year": "", "raw_text": ""}

    # 1. Extract text locally
    text = _extract_text_from_pdf(file_path)
    if not text:
        logger.warning("[Resume] No text could be extracted from PDF")
        return {"skills": [], "domains": [], "experience_level": "fresher",
                "college": "", "year": "", "raw_text": ""}

    # 2. Call Gemini CLI via our centralized service
    logger.info(f"[Resume] Sending {len(text)} chars to Gemini for analysis")
    prompt = RESUME_PROMPT_TEXT.format(text=text[:4000]) # Cap text for CLI
    raw = call_gemini(prompt)

    if not raw:
        logger.error("[Resume] Gemini CLI returned empty response")
        return {"skills": [], "domains": [], "experience_level": "fresher",
                "college": "", "year": "", "raw_text": ""}

    # 3. Parse JSON result
    try:
        # Clean JSON
        raw = re.sub(r"```(?:json)?", "", raw).strip().rstrip("`").strip()
        m = re.search(r'\{.*\}', raw, re.DOTALL)
        if m: raw = m.group(0)
        
        data = json.loads(raw)
        skills = [normalize_skill(s) for s in data.get("skills", [])]
        skills = list(dict.fromkeys(skills))[:15]
        
        return {
            "skills": skills,
            "domains": data.get("domains", [])[:3],
            "experience_level": data.get("experience_level", "fresher"),
            "college": data.get("college", ""),
            "year": data.get("year", ""),
            "summary": data.get("raw_text_summary", ""),
            "raw_text": text[:2000],  # Store some raw text for context
        }
    except Exception as e:
        logger.error(f"[Resume] JSON parse failed: {e} | raw: {raw[:200]}")
        return {"skills": [], "domains": [], "experience_level": "fresher",
                "college": "", "year": "", "raw_text": ""}
