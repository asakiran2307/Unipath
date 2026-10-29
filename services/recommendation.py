"""Personalized recommendation engine for student opportunity matching."""
import json
from datetime import datetime, date


BRANCH_TAGS = {
    "CSE": ["AI/ML", "Web Development", "Data Science", "Cybersecurity", "Cloud Computing", "DevOps", "Competitive Programming"],
    "ECE": ["IoT", "Robotics", "Embedded Systems", "VLSI", "Signal Processing", "Electronics"],
    "EEE": ["Power Systems", "IoT", "Robotics", "Embedded Systems", "Electrical"],
    "IT": ["Web Development", "Cloud Computing", "Cybersecurity", "DevOps", "Networking"],
    "ME": ["Robotics", "Manufacturing", "CAD", "3D Printing", "IoT"],
    "CE": ["Construction Tech", "GIS", "Structural", "Smart Cities"],
    "MBA": ["Finance & Fintech", "Marketing", "Business Analytics", "Entrepreneurship"],
}

YEAR_ELIGIBLE = {
    "1st Year": ["Open to All", "1st Year", "Freshers", "All Years"],
    "2nd Year": ["Open to All", "1st Year", "2nd Year", "Freshers", "All Years", "1st/2nd Year"],
    "3rd Year": ["Open to All", "2nd/3rd Year", "3rd Year", "Pre-final", "All Years", "3rd/4th Year"],
    "4th Year": ["Open to All", "4th Year", "Final Year", "2026 Batch", "All Years", "3rd/4th Year"],
    "Postgraduate": ["Open to All", "PG", "Postgraduate", "M.Tech", "MBA", "All Years"],
}


def _score_opportunity(opp: dict, profile: dict) -> float:
    """Score 0.0-1.0 how well an opportunity matches a student profile."""
    score = 0.5  # Base score

    tags = [t.lower() for t in (opp.get("tags") or [])]
    eligibility = (opp.get("eligibility") or "").lower()
    category = opp.get("category", "")
    title_lower = (opp.get("title") or "").lower()

    year = profile.get("year", "")
    branch = profile.get("branch", "")
    interests = [x.lower() for x in (profile.get("interests") or [])]
    preferred_cats = [x.lower() for x in (profile.get("preferred_categories") or [])]
    skills = [s.lower() for s in (profile.get("skills") or [])]

    # Category preference
    if category.lower() in preferred_cats:
        score += 0.2

    # Interest/tag overlap
    for interest in interests:
        for tag in tags:
            if interest in tag or tag in interest:
                score += 0.1
                break

    # Branch relevance
    branch_relevant_tags = [t.lower() for t in BRANCH_TAGS.get(branch, [])]
    for rt in branch_relevant_tags:
        for tag in tags:
            if rt in tag or tag in rt:
                score += 0.05
                break

    # Year eligibility
    allowed_years = YEAR_ELIGIBLE.get(year, [])
    is_year_eligible = any(y.lower() in eligibility for y in allowed_years) or "open" in eligibility
    if is_year_eligible:
        score += 0.1
    else:
        # Penalize if clearly not eligible (e.g., "Final Year" when 1st Year)
        if year == "1st Year" and any(k in eligibility for k in ["final year", "4th year", "3rd year"]):
            score -= 0.3
        elif year == "4th Year" and "1st year" in eligibility and "only" in eligibility:
            score -= 0.2

    # Skills overlap with title/description
    desc = (opp.get("description") or "").lower()
    for skill in skills:
        if skill in title_lower or skill in desc:
            score += 0.05

    # Featured bonus
    if opp.get("is_featured"):
        score += 0.1

    # Deadline urgency (upcoming deadlines rank higher, expired rank lower)
    deadline = opp.get("deadline")
    if deadline:
        try:
            dl = datetime.strptime(deadline[:10], "%Y-%m-%d").date()
            days_left = (dl - date.today()).days
            if days_left < 0:
                score -= 0.5  # Expired
            elif days_left <= 7:
                score += 0.08  # Closing soon
            elif days_left <= 30:
                score += 0.04
        except Exception:
            pass

    return max(0.0, min(1.0, score))


def get_personalized_feed(opportunities: list[dict], profile: dict) -> list[dict]:
    """Return opportunities sorted by relevance score for the student's profile."""
    if not profile:
        return opportunities

    scored = []
    for opp in opportunities:
        s = _score_opportunity(opp, profile)
        opp_copy = dict(opp)
        opp_copy["_relevance_score"] = round(s, 3)
        scored.append((s, opp_copy))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [o for _, o in scored]


def filter_by_profile(opportunities: list[dict], profile: dict, min_score: float = 0.0) -> list[dict]:
    """Filter out low-relevance opportunities."""
    return [o for o in get_personalized_feed(opportunities, profile) if o.get("_relevance_score", 0.5) >= min_score]
