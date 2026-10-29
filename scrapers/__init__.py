from .devfolio_scraper import DevfolioScraper
from .internshala_scraper import InternshalaSimpleScraper
from .instagram_scraper import InstagramScraper
from .linkedin_scraper import LinkedInScraper
from .news_rss_scraper import NewsRSSScraper   # replaces Twitter/X

# Core web scrapers (always run, no credentials needed)
# Removed MLH, Unstop, Buddy4Study due to javascript rendering
CORE_SCRAPERS = [
    DevfolioScraper,         # (Devpost fallback)
    InternshalaSimpleScraper,
    NewsRSSScraper,          # Google News RSS — no auth, always works
]

# Social scrapers (credentials-dependent, loaded dynamically by scheduler)
SOCIAL_SCRAPER_MAP = {
    "instagram": InstagramScraper,
    "linkedin": LinkedInScraper,
    # Twitter replaced by NewsRSSScraper (now in CORE_SCRAPERS)
}

# All scrapers (for backward compatibility)
ALL_SCRAPERS = CORE_SCRAPERS

__all__ = [
    "DevfolioScraper",
    "InternshalaSimpleScraper",
    "InstagramScraper", "LinkedInScraper", "NewsRSSScraper",
    "CORE_SCRAPERS", "SOCIAL_SCRAPER_MAP", "ALL_SCRAPERS",
]
