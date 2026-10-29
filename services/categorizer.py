"""Keyword + regex opportunity categorizer."""
import re


CASH_KEYWORDS = ["cash prize", "cash award", "prize pool", "prize money", "₹", "$", "usd", "inr", "winning amount", "grand prize"]
STIPEND_KEYWORDS = ["stipend", "per month", "/month", "monthly", "salary", "ctc", "lpa", "per annum"]
CERTIFICATE_KEYWORDS = ["certificate", "merit certificate", "letter of appreciation", "digital badge", "badge only"]
FREE_KEYWORDS = ["free", "no cost", "complimentary", "waived", "scholarship seat"]

HACKATHON_KEYWORDS = ["hackathon", "hack", "buildathon", "datathon", "codeathon", "sprint", "challenge", "competition", "contest"]
INTERNSHIP_KEYWORDS = ["internship", "intern ", "summer intern", "winter intern", "research fellow", "research intern"]
SCHOLARSHIP_KEYWORDS = ["scholarship", "grant", "fellowship", "financial aid", "award", "bursary"]
WORKSHOP_KEYWORDS = ["workshop", "bootcamp", "training", "course", "webinar", "seminar", "masterclass", "live session", "certification program"]
JOB_KEYWORDS = ["job", "full-time", "full time", "hiring", "recruit", "analyst", "engineer", "developer", "fresher hiring", "campus placement", "2026 batch"]


def classify_reward_type(reward_text: str, description: str = "") -> tuple[str, int]:
    """Return (reward_type, prize_amount_inr)."""
    text = (reward_text + " " + description).lower()

    # Extract prize amount
    amount = 0
    usd_match = re.search(r"\$([\d,]+)", text)
    inr_lakh = re.search(r"₹\s*([\d.]+)\s*(?:lakh|l\b)", text)
    inr_k = re.search(r"₹\s*([\d,]+)\s*k\b", text)
    inr_plain = re.search(r"₹\s*([\d,]+)", text)

    if usd_match:
        amount = int(usd_match.group(1).replace(",", "")) * 83
    elif inr_lakh:
        amount = int(float(inr_lakh.group(1)) * 100000)
    elif inr_k:
        amount = int(inr_k.group(1).replace(",", "")) * 1000
    elif inr_plain:
        amount = int(inr_plain.group(1).replace(",", ""))

    if any(k in text for k in STIPEND_KEYWORDS):
        return "stipend", 0
    if amount > 0 or any(k in text for k in CASH_KEYWORDS):
        return "cash", amount
    if any(k in text for k in FREE_KEYWORDS):
        return "free", 0
    return "certificate", 0


def classify_category(title: str, description: str = "") -> str:
    text = (title + " " + description).lower()
    if any(k in text for k in INTERNSHIP_KEYWORDS):
        return "internship"
    if any(k in text for k in SCHOLARSHIP_KEYWORDS):
        return "scholarship"
    if any(k in text for k in WORKSHOP_KEYWORDS):
        return "workshop"
    if any(k in text for k in JOB_KEYWORDS):
        return "job"
    if any(k in text for k in HACKATHON_KEYWORDS):
        return "hackathon"
    return "hackathon"


def extract_tags(title: str, description: str, category: str) -> list[str]:
    text = (title + " " + description).lower()
    tag_map = {
        "AI/ML": ["ai", "machine learning", "deep learning", "neural", "nlp", "llm", "gpt", "tensorflow", "pytorch"],
        "Web Development": ["web", "frontend", "backend", "react", "django", "flask", "html", "css"],
        "Android/iOS": ["android", "ios", "mobile", "flutter", "kotlin", "swift"],
        "Cybersecurity": ["security", "cyber", "ctf", "ethical hacking", "penetration"],
        "Data Science": ["data science", "data analytics", "pandas", "tableau", "power bi", "sql"],
        "Cloud Computing": ["cloud", "aws", "azure", "gcp", "kubernetes", "devops"],
        "Blockchain": ["blockchain", "web3", "solidity", "nft", "defi", "crypto"],
        "IoT": ["iot", "arduino", "raspberry pi", "embedded", "sensor"],
        "Open Source": ["open source", "github", "git", "contribution"],
        "Finance & Fintech": ["finance", "fintech", "banking", "trading", "quant"],
        "Women in STEM": ["women", "girls", "female", "gender"],
        "Govt": ["government", "govt", "ministry", "aicte", "drdo", "isro", "nsdc"],
        "Remote": ["remote", "work from home", "wfh", "online"],
        "Team Event": ["team", "group", "squad"],
        "Solo": ["individual", "solo", "single"],
        "Beginner Friendly": ["beginner", "no experience", "fresher", "all year"],
    }
    found_tags = []
    for tag, keywords in tag_map.items():
        if any(kw in text for kw in keywords):
            found_tags.append(tag)
    return found_tags[:6]
