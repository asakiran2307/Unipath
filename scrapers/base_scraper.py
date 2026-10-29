"""Base scraper abstract class with anti-bot resilience."""
import random, time, hashlib, logging
import requests
from abc import ABC, abstractmethod
from config import USER_AGENTS, REQUEST_DELAY_MIN, REQUEST_DELAY_MAX, MAX_RETRIES

logger = logging.getLogger(__name__)


def make_hash(title: str, source: str) -> str:
    return hashlib.sha256(f"{title.lower().strip()}::{source.lower()}".encode()).hexdigest()[:32]


def normalize_title(title: str) -> str:
    return " ".join(title.lower().split())


class BaseScraper(ABC):
    SOURCE_NAME = "Unknown"
    BASE_URL = ""

    def __init__(self):
        self.session = requests.Session()
        self._rotate_agent()

    def _rotate_agent(self):
        self.session.headers.update({
            "User-Agent": random.choice(USER_AGENTS),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "DNT": "1",
        })

    def get(self, url, **kwargs):
        self._rotate_agent()
        for attempt in range(MAX_RETRIES):
            try:
                delay = random.uniform(REQUEST_DELAY_MIN, REQUEST_DELAY_MAX)
                time.sleep(delay)
                resp = self.session.get(url, timeout=15, **kwargs)
                if resp.status_code == 429:
                    wait = (attempt + 1) * 5
                    logger.warning(f"[{self.SOURCE_NAME}] Rate limited. Waiting {wait}s...")
                    time.sleep(wait)
                    continue
                resp.raise_for_status()
                return resp
            except requests.RequestException as e:
                logger.warning(f"[{self.SOURCE_NAME}] Attempt {attempt + 1} failed: {e}")
                if attempt == MAX_RETRIES - 1:
                    raise
                time.sleep((attempt + 1) * 2)
        return None

    def _make_opp(self, **kwargs) -> dict:
        """Build a normalized opportunity dict."""
        title = kwargs.get("title", "")
        opp = {
            "title": title,
            "category": kwargs.get("category", "hackathon"),
            "source": self.SOURCE_NAME,
            "source_url": kwargs.get("source_url", self.BASE_URL),
            "apply_link": kwargs.get("apply_link", self.BASE_URL),
            "deadline": kwargs.get("deadline"),
            "reward": kwargs.get("reward", ""),
            "reward_type": kwargs.get("reward_type", "certificate"),
            "prize_amount": kwargs.get("prize_amount", 0),
            "eligibility": kwargs.get("eligibility", "Open to All"),
            "tags": kwargs.get("tags", []),
            "description": kwargs.get("description", ""),
            "company": kwargs.get("company", ""),
            "location": kwargs.get("location", "Remote"),
            "status": "approved",  # Scraped items auto-approved
            "is_featured": 0,
            "hash": make_hash(title, self.SOURCE_NAME),
        }
        return opp

    @abstractmethod
    def scrape(self) -> list[dict]:
        """Return list of normalized opportunity dicts."""
        pass

    def run(self) -> tuple[list[dict], str]:
        """Run scraper and return (results, error_or_empty)."""
        try:
            results = self.scrape()
            logger.info(f"[{self.SOURCE_NAME}] Scraped {len(results)} items.")
            return results, ""
        except Exception as e:
            logger.error(f"[{self.SOURCE_NAME}] Scrape failed: {e}")
            return [], str(e)
