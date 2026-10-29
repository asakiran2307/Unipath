"""Scraper for Buddy4Study scholarship listings."""
import logging, re
from bs4 import BeautifulSoup
from .base_scraper import BaseScraper

logger = logging.getLogger(__name__)


class ScholarshipScraper(BaseScraper):
    SOURCE_NAME = "Buddy4Study"
    BASE_URL = "https://www.buddy4study.com/scholarships/engineering"

    def _extract_amount(self, text: str) -> int:
        patterns = [
            r"₹\s*([\d,]+)\s*(?:lakh|L|Lakhs?)",
            r"₹\s*([\d,]+)\s*(?:per annum|pa|/year|yearly)",
            r"₹\s*([\d,]+)",
        ]
        for i, pat in enumerate(patterns):
            m = re.search(pat, text, re.IGNORECASE)
            if m:
                n = int(m.group(1).replace(",", ""))
                if i == 0:
                    n = n * 100000
                return n
        return 0

    def scrape(self) -> list[dict]:
        results = []
        try:
            resp = self.get(self.BASE_URL)
            soup = BeautifulSoup(resp.content, "lxml")
            cards = soup.select(".scholarship-section, .sc-block, .scholarship-list-item, article")
            for card in cards[:20]:
                title_el = card.select_one("h2,h3,.title,a")
                amount_el = card.select_one(".amount,.scholarship-amount,.prize")
                deadline_el = card.select_one(".deadline,.last-date,.date")
                link_el = card.select_one("a[href]")
                eligibility_el = card.select_one(".eligibility,.eligible")
                if not title_el:
                    continue
                title = title_el.get_text(strip=True)
                if len(title) < 5:
                    continue
                amount_text = amount_el.get_text(strip=True) if amount_el else ""
                amount = self._extract_amount(amount_text)
                deadline = deadline_el.get_text(strip=True) if deadline_el else None
                link = link_el["href"] if link_el and link_el.get("href") else self.BASE_URL
                if link.startswith("/"):
                    link = f"https://www.buddy4study.com{link}"
                eligibility = eligibility_el.get_text(strip=True) if eligibility_el else "Engineering Students"

                opp = self._make_opp(
                    title=title,
                    category="scholarship",
                    apply_link=link,
                    source_url=self.BASE_URL,
                    deadline=deadline,
                    reward=amount_text if amount_text else "Scholarship Award",
                    reward_type="cash",
                    prize_amount=amount,
                    eligibility=eligibility,
                    tags=["Scholarship", "Buddy4Study", "Education"],
                    description=f"{title}. {eligibility}.",
                    company="Scholarship Provider",
                    location="Pan India",
                )
                results.append(opp)
        except Exception as e:
            logger.error(f"[Buddy4Study] Failed: {e}")
        return results
