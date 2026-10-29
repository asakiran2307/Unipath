"""
Google News RSS Scraper — replaces Twitter/X.
No API key, no login, no token. Uses Google News RSS feeds.
Searches: hackathon India, internship India, scholarship India, etc.
"""
import re
import logging
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from urllib.parse import quote
from .base_scraper import BaseScraper

logger = logging.getLogger(__name__)

# ── Queries for each category ──────────────────────────────────────────────────
RSS_QUERIES = [
    ("hackathon India 2025 2026 register",          "hackathon"),
    ("hackathon India prize cash register",          "hackathon"),
    ("internship India students apply stipend",      "internship"),
    ("internship hiring freshers India 2025 2026",   "internship"),
    ("scholarship India students apply 2025 2026",   "scholarship"),
    ("fellowship India students 2025",               "scholarship"),
    ("coding contest India prize",                   "hackathon"),
    ("buildathon datathon India 2025",               "hackathon"),
    ("campus hiring India fresher 2026",             "job"),
    ("bootcamp workshop India students free",        "workshop"),
    ("IIT hackathon competition students",           "hackathon"),
    ("AICTE scholarship students India",             "scholarship"),
]

GOOGLE_NEWS_RSS = "https://news.google.com/rss/search?q={query}&hl=en-IN&gl=IN&ceid=IN%3Aen"

# Only keep articles from last N days
MAX_AGE_DAYS = 14

JUNK_SOURCES = [
    "dailyhunt", "patrika", "navbharat", "bhaskar",
    "lokmat", "divyabhaskar",  # non-English vernacular
]

OPPORTUNITY_KEYWORDS = [
    "hackathon", "internship", "scholarship", "fellowship",
    "register", "apply", "competition", "prize", "stipend",
    "hiring", "fresher", "campus", "bootcamp", "workshop",
    "contest", "challenge", "coding",
]


class NewsRSSScraper(BaseScraper):
    SOURCE_NAME = "Google News"
    BASE_URL = "https://news.google.com"

    def _is_junk(self, title: str, source: str) -> bool:
        source_lower = source.lower()
        return any(j in source_lower for j in JUNK_SOURCES)

    def _is_opportunity(self, text: str) -> bool:
        t = text.lower()
        return sum(1 for kw in OPPORTUNITY_KEYWORDS if kw in t) >= 1

    def _detect_category(self, text: str, default: str) -> str:
        t = text.lower()
        if any(k in t for k in ["hackathon", "buildathon", "datathon",
                                  "coding contest", "code", "challenge",
                                  "competition", "techfest"]):
            return "hackathon"
        if any(k in t for k in ["internship", "intern ", "stipend",
                                  "campus hiring", "fresher"]):
            return "internship"
        if any(k in t for k in ["scholarship", "fellowship", "grant",
                                  "financial aid", "aicte"]):
            return "scholarship"
        if any(k in t for k in ["workshop", "bootcamp", "webinar",
                                  "seminar", "training", "course"]):
            return "workshop"
        if any(k in t for k in ["job", "hiring", "vacancy", "opening",
                                  "recruitment", "career"]):
            return "job"
        return default

    def _extract_prize(self, text: str):
        prize_amount = 0
        reward = ""
        reward_type = "certificate"
        patterns = [
            (r"(?:₹|rs\.?|inr)\s*([\d,]+)\s*lakh", 100000),
            (r"(?:₹|rs\.?|inr)\s*([\d,]+)\s*k",     1000),
            (r"(?:₹|rs\.?|inr)\s*([\d,]+)",          1),
            (r"\$([\d,]+)\s*k",                       83000),
            (r"\$([\d,]+)",                           83),
        ]
        for pat, mult in patterns:
            m = re.search(pat, text, re.I)
            if m:
                prize_amount = int(m.group(1).replace(",", "")) * mult
                reward = m.group(0).strip()
                reward_type = "cash"
                break
        if not reward:
            if re.search(r"stipend|paid|salary", text, re.I):
                reward_type = "stipend"
                reward = "Paid Position"
            elif re.search(r"free|complimentary|no.?cost", text, re.I):
                reward_type = "free"
                reward = "Free"
            else:
                reward = "Certificate / Prize"
        return prize_amount, reward, reward_type

    def _parse_pub_date(self, pub_date_str: str) -> str | None:
        """Parse RFC 822 date like 'Mon, 14 Apr 2025 08:00:00 GMT'"""
        if not pub_date_str:
            return None
        try:
            from email.utils import parsedate_to_datetime
            dt = parsedate_to_datetime(pub_date_str)
            return dt.strftime("%Y-%m-%d")
        except Exception:
            return None

    def _fetch_rss(self, query: str, default_category: str) -> list[dict]:
        url = GOOGLE_NEWS_RSS.format(query=quote(query))
        try:
            resp = self.get(url)
            if not resp or resp.status_code != 200:
                logger.warning(f"[NewsRSS] HTTP {resp.status_code if resp else '?'} for: {query}")
                return []
        except Exception as e:
            logger.warning(f"[NewsRSS] Fetch error for '{query}': {e}")
            return []

        results = []
        cutoff = datetime.now() - timedelta(days=MAX_AGE_DAYS)

        try:
            root = ET.fromstring(resp.content)
        except ET.ParseError as e:
            logger.warning(f"[NewsRSS] XML parse error: {e}")
            return []

        ns = {"media": "http://search.yahoo.com/mrss/"}
        channel = root.find("channel")
        if channel is None:
            return []

        for item in channel.findall("item"):
            title = (item.findtext("title") or "").strip()
            link  = (item.findtext("link")  or "").strip()
            desc  = (item.findtext("description") or "").strip()
            pub   = item.findtext("pubDate") or ""
            source_el = item.find("source")
            source = source_el.text.strip() if source_el is not None else "News"

            # Age filter
            pub_date = self._parse_pub_date(pub)
            if pub_date:
                try:
                    if datetime.strptime(pub_date, "%Y-%m-%d") < cutoff:
                        continue
                except Exception:
                    pass

            # Clean title (Google News wraps: "Title - Source")
            clean_title = re.sub(r"\s*[-–—]\s*[^-–—]+$", "", title).strip()
            if not clean_title or len(clean_title) < 10:
                clean_title = title[:100]

            full_text = f"{clean_title} {desc}"

            if not self._is_opportunity(full_text):
                continue
            if self._is_junk(clean_title, source):
                continue

            category = self._detect_category(full_text, default_category)
            prize_amount, reward, reward_type = self._extract_prize(full_text)

            tags = ["News", source[:25], category.title()]
            # Extract any hashtags/keywords
            extra_tags = re.findall(r"\b(hackathon|internship|scholarship|fellowship|prize|IIT|NIT|coding)\b",
                                    full_text, re.I)
            tags += [t.title() for t in dict.fromkeys(extra_tags)][:3]

            opp = self._make_opp(
                title=clean_title[:120],
                category=category,
                apply_link=link or self.BASE_URL,
                source_url=link or self.BASE_URL,
                deadline=None,
                reward=reward,
                reward_type=reward_type,
                prize_amount=prize_amount,
                eligibility="See article for eligibility",
                tags=list(dict.fromkeys(tags))[:6],
                description=f"{desc[:300] or clean_title}",
                company=source,
                location="India",
            )
            results.append(opp)

        return results

    def scrape(self) -> list[dict]:
        import time
        all_results = []
        seen_titles = set()

        for query, cat in RSS_QUERIES:
            fresh = self._fetch_rss(query, cat)
            for opp in fresh:
                key = opp["title"].lower()[:60]
                if key not in seen_titles:
                    seen_titles.add(key)
                    all_results.append(opp)
            logger.info(f"[NewsRSS] '{query[:40]}': {len(fresh)} articles")
            time.sleep(0.5)  # be gentle with Google

        logger.info(f"[NewsRSS] Total unique: {len(all_results)}")
        return all_results
