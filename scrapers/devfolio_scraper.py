"""
Devfolio replacement — scrapes from DoraHacks (public GraphQL API) and
Devpost (public hackathons API). Both work without auth.
"""
import logging, json, re
from bs4 import BeautifulSoup
from .base_scraper import BaseScraper

logger = logging.getLogger(__name__)


class DevfolioScraper(BaseScraper):
    SOURCE_NAME = "Devpost"
    BASE_URL = "https://devpost.com/hackathons"

    # Devpost has a public API
    DEVPOST_API = "https://devpost.com/api/hackathons?status=open&order_by=deadline&per_page=20"

    def scrape(self) -> list[dict]:
        results = []

        # 1. Devpost public hackathons API
        try:
            resp = self.get(self.DEVPOST_API)
            if resp and resp.status_code == 200:
                try:
                    data = resp.json()
                    hackathons = data.get("hackathons", [])
                    for h in hackathons[:20]:
                        title = h.get("title") or h.get("name") or ""
                        if not title:
                            continue
                        link = h.get("url") or self.BASE_URL
                        deadline_raw = h.get("submission_period_dates") or h.get("ends_at") or ""
                        deadline = None
                        if deadline_raw:
                            # "Oct 10, 2025" or "2025-10-10"
                            try:
                                from datetime import datetime
                                for fmt in ["%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%d", "%b %d, %Y", "%B %d, %Y"]:
                                    try:
                                        deadline = datetime.strptime(str(deadline_raw)[:20], fmt).strftime("%Y-%m-%d")
                                        break
                                    except Exception:
                                        pass
                            except Exception:
                                pass
                        prize = h.get("prize_amount") or 0
                        try:
                            prize = int(str(prize).replace("$", "").replace(",", "").strip() or "0")
                        except Exception:
                            prize = 0
                        themes = h.get("themes", [])
                        tags_raw = [t.get("name", "") for t in themes if t.get("name")][:4]
                        tags = ["Devpost", "Hackathon"] + tags_raw
                        opp = self._make_opp(
                            title=title[:120],
                            category="hackathon",
                            apply_link=link,
                            source_url=link,
                            deadline=deadline,
                            reward=f"${prize:,}" if prize else "Prizes + Certificate",
                            reward_type="cash" if prize > 0 else "certificate",
                            prize_amount=prize * 83 if prize else 0,  # USD to INR approx
                            eligibility="Open to All Students",
                            tags=tags[:6],
                            description=h.get("tagline") or f"{title} on Devpost.",
                            company=h.get("organization_name") or "Devpost",
                            location="Remote" if h.get("is_online") else h.get("displayed_location", {}).get("location", "Remote"),
                        )
                        results.append(opp)
                    logger.info(f"[Devpost] API got {len(results)} hackathons")
                except Exception as e:
                    logger.debug(f"[Devpost] JSON error: {e}")
        except Exception as e:
            logger.warning(f"[Devpost] API error: {e}")

        # 2. Fallback: HTML scrape of Devpost
        if not results:
            try:
                resp = self.get(self.BASE_URL)
                if resp and resp.status_code == 200:
                    soup = BeautifulSoup(resp.content, "lxml")
                    cards = (
                        soup.select(".hackathon-tile") or
                        soup.select("[class*='hackathon']") or
                        soup.select("article.hackathon") or
                        soup.select(".tile")
                    )
                    for card in cards[:20]:
                        title_el = card.select_one("h2,h3,.title,[class*='title']")
                        if not title_el:
                            continue
                        title = title_el.get_text(strip=True)
                        if not title or len(title) < 5:
                            continue
                        link_el = card.select_one("a[href*='devpost']")
                        link = link_el.get("href", self.BASE_URL) if link_el else self.BASE_URL
                        opp = self._make_opp(
                            title=title[:120],
                            category="hackathon",
                            apply_link=link,
                            source_url=self.BASE_URL,
                            reward="Prizes + Certificate",
                            reward_type="certificate",
                            eligibility="Open to All",
                            tags=["Devpost", "Hackathon"],
                            description=f"{title} on Devpost.",
                            company="Devpost",
                            location="Remote",
                        )
                        results.append(opp)
            except Exception as e:
                logger.warning(f"[Devpost] HTML fallback: {e}")

        logger.info(f"[Devpost] Total: {len(results)} hackathons")
        return results
