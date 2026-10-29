"""Deduplication engine using hash + fuzzy title matching."""
import hashlib
from difflib import SequenceMatcher


def make_hash(title: str, source: str) -> str:
    key = f"{normalize(title)}::{source.lower().strip()}"
    return hashlib.sha256(key.encode()).hexdigest()[:32]


def normalize(text: str) -> str:
    """Normalize text for comparison: lowercase, strip, collapse spaces."""
    import re
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9 ]", "", text)
    text = re.sub(r"\s+", " ", text)
    return text


def similarity(a: str, b: str) -> float:
    return SequenceMatcher(None, normalize(a), normalize(b)).ratio()


def is_duplicate(title: str, existing_titles: list[str], threshold: float = 0.88) -> bool:
    """Return True if title is a near-duplicate of any in existing_titles."""
    for et in existing_titles:
        if similarity(title, et) >= threshold:
            return True
    return False


def deduplicate_list(opportunities: list[dict]) -> list[dict]:
    """Remove near-duplicates from a list of opportunity dicts (in-memory)."""
    seen_titles = []
    seen_hashes = set()
    unique = []
    for opp in opportunities:
        h = opp.get("hash") or make_hash(opp.get("title", ""), opp.get("source", ""))
        if h in seen_hashes:
            continue
        if is_duplicate(opp.get("title", ""), seen_titles):
            continue
        seen_hashes.add(h)
        seen_titles.append(opp.get("title", ""))
        unique.append(opp)
    return unique
