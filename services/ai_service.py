"""AI service — calls Google Gemini via official GenAI SDK (cloud-ready) with local CLI fallback."""
import os, json, logging, re, subprocess, warnings
warnings.filterwarnings("ignore", category=FutureWarning, module="google")

from config import GEMINI_API_KEY, GEMINI_MODEL

logger = logging.getLogger(__name__)


def call_gemini(prompt: str) -> str:
    """Call Gemini using official SDK with API key (cloud/Vercel ready) or local fallback."""
    # 1. Cloud-ready API key approach (google.genai or google.generativeai)
    if GEMINI_API_KEY:
        # Try modern google.genai SDK
        try:
            from google import genai
            client = genai.Client(api_key=GEMINI_API_KEY)
            response = client.models.generate_content(
                model=GEMINI_MODEL,
                contents=prompt,
            )
            if response and response.text:
                return response.text.strip()
        except Exception as e_new:
            logger.debug(f"[Gemini genai SDK] {e_new}")

        # Try legacy google.generativeai SDK
        try:
            import google.generativeai as genai_legacy
            genai_legacy.configure(api_key=GEMINI_API_KEY)
            model = genai_legacy.GenerativeModel(GEMINI_MODEL)
            response = model.generate_content(prompt)
            if response and response.text:
                return response.text.strip()
        except Exception as e_old:
            logger.debug(f"[Gemini legacy SDK] {e_old}")

    # 2. Local Windows CLI Fallback (if running locally with npm @google/gemini-cli)
    gemini_cli_path = os.path.expanduser(r"~\AppData\Roaming\npm\gemini.ps1")
    if os.name == "nt" and os.path.exists(gemini_cli_path):
        try:
            safe_prompt = prompt[:3000].replace('"', "'")
            result = subprocess.run(
                ["powershell", "-NoProfile", "-Command",
                 f"& '{gemini_cli_path}' --prompt \"{safe_prompt}\" --output-format text"],
                capture_output=True,
                text=True,
                timeout=30,
                encoding="utf-8",
                errors="replace"
            )
            if result.returncode == 0:
                output = result.stdout.strip()
                lines = [l for l in output.splitlines()
                         if not l.startswith("Loaded cached") and "DeprecationWarning" not in l and l.strip()]
                if lines:
                    return "\n".join(lines).strip()
        except Exception as e_cli:
            logger.debug(f"[Gemini CLI fallback] {e_cli}")

    return ""


def _extract_json(text: str) -> dict:
    """Extract JSON from a response that may contain markdown fences."""
    text = re.sub(r"```(?:json)?", "", text).strip().rstrip("`").strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        m = re.search(r"\{.*\}", text, re.DOTALL)
        if m:
            try:
                return json.loads(m.group())
            except Exception:
                pass
    return {}


def analyze_opportunity(title: str, description: str, reward: str, eligibility: str) -> dict:
    """Use Gemini to analyze and classify an opportunity."""
    prompt = f"""You are an AI assistant for a student opportunity platform. Analyze this opportunity:

Title: {title}
Description: {description}
Reward: {reward}
Eligibility: {eligibility}

Return ONLY a valid JSON object with these exact keys:
{{
  "category": "hackathon" or "internship" or "scholarship" or "workshop" or "job",
  "reward_type": "cash" or "stipend" or "certificate" or "free",
  "prize_amount_inr": <integer, 0 if none>,
  "tags": [<up to 5 relevant tags as strings>],
  "eligibility_clean": "<clean 1-line eligibility string>",
  "is_legitimate": <true or false>,
  "legitimacy_reason": "<1 sentence reason>",
  "clean_summary": "<2 sentence max summary for students>"
}}"""
    raw = call_gemini(prompt)
    data = _extract_json(raw)
    return {
        "category": data.get("category", "hackathon"),
        "reward_type": data.get("reward_type", "certificate"),
        "prize_amount": int(data.get("prize_amount_inr", 0)),
        "tags": data.get("tags", []),
        "eligibility": data.get("eligibility_clean", eligibility),
        "is_legitimate": data.get("is_legitimate", True),
        "legitimacy_reason": data.get("legitimacy_reason", ""),
        "clean_summary": data.get("clean_summary", description[:200]),
    }


def get_recommendation_reason(opportunity: dict, profile: dict) -> str:
    """Return a 1-sentence personalized reason why this opportunity suits the student."""
    prompt = f"""Student profile: Year={profile.get('year')}, Branch={profile.get('branch')}, 
Interests={profile.get('interests')}, Skills={profile.get('skills')}.

Opportunity: {opportunity.get('title')} — {opportunity.get('description', '')[:200]}

Write exactly ONE sentence (max 20 words) explaining why this opportunity is perfect for this student.
Start with "Perfect for you because..." or "Great match —"."""
    return call_gemini(prompt) or "Great match for your profile!"


def check_scam(title: str, description: str, apply_link: str) -> dict:
    """Flag suspicious opportunities."""
    prompt = f"""Is this student opportunity legitimate or a potential scam?
Title: {title}
Description: {description[:300]}
Link: {apply_link}

Return JSON: {{"is_scam": true/false, "confidence": 0.0-1.0, "reason": "short reason"}}"""
    raw = call_gemini(prompt)
    data = _extract_json(raw)
    return {
        "is_scam": data.get("is_scam", False),
        "confidence": float(data.get("confidence", 0.0)),
        "reason": data.get("reason", ""),
    }


def generate_opportunity_summary(title: str, description: str) -> str:
    """Generate a clean 2-sentence summary for an opportunity."""
    prompt = f"""Summarize this student opportunity in exactly 2 sentences for Indian college students.
Keep it engaging, specific, and informative. Include the main benefit.

Title: {title}
Description: {description[:500]}"""
    return call_gemini(prompt) or description[:200]


def smart_search(query: str, opportunities: list[dict]) -> list[dict]:
    """Use Gemini to rank which opportunities best match a natural language query."""
    if not opportunities:
        return []
    titles_str = "\n".join([f"{i+1}. {o['title']} ({o['category']})" for i, o in enumerate(opportunities[:30])])
    prompt = f"""A student searched: "{query}"

Available opportunities (numbered):
{titles_str}

Return ONLY a JSON array of the best matching opportunity numbers (1-indexed), sorted by relevance.
Return at most 10. Example: [3, 1, 7, 2]"""
    raw = call_gemini(prompt)
    try:
        raw = re.sub(r"```(?:json)?", "", raw).strip().rstrip("`").strip()
        indices = json.loads(raw)
        result = []
        seen = set()
        for idx in indices:
            i = int(idx) - 1
            if 0 <= i < len(opportunities) and i not in seen:
                result.append(opportunities[i])
                seen.add(i)
        return result
    except Exception:
        return opportunities[:10]

def generate_learning_path(skills: list[str], experience_level: str = "fresher") -> list[dict]:
    """Generate a 4-step AI learning roadmap based on extracted resume skills."""
    if not skills:
        skills = ["General Software Engineering basics", "Communication"]
        
    skills_str = ", ".join(skills[:10])
    prompt = f"""You are an expert tech career coach. A student ({experience_level}) has uploaded their resume.
Based on these extracted skills: {skills_str}

Please generate a personalized, 4-step actionable learning roadmap for them to level up and become highly employable in the current tech market.

Return ONLY a JSON array of 4 objects. Each object must have:
- "step": integer (1 to 4)
- "title": string (Action-oriented title, max 5-6 words)
- "duration": string (e.g. "Week 1-2")
- "description": string (Detailed 2-sentence description of what to learn/do)
- "resource": string (Name of exactly ONE specific tool, platform, or framework they need to practice)

JSON output format:
[{{
  "step": 1,
  "title": "Master React Fundamentals",
  "duration": "Weeks 1-2",
  "description": "...",
  "resource": "React.dev documentation"
}}]"""
    raw = call_gemini(prompt)
    
    if not raw:
        return []

    try:
        # Strip ALL markdown fences and find the JSON array
        clean = re.sub(r"```[a-z]*", "", raw).replace("```", "").strip()
        # Find the array specifically
        m = re.search(r'\[.*\]', clean, re.DOTALL)
        if m:
            clean = m.group(0)
        roadmap = json.loads(clean)
        return roadmap[:4] if (isinstance(roadmap, list) and len(roadmap) > 0) else []
    except Exception as e:
        logger.error(f"[Learning Path] JSON parse failed: {e} | raw: {raw[:100]}")
        return []
