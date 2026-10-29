"""
HackerEarth Challenges scraper.
Uses HackerEarth's public challenges API (unauthenticated).
Replaces Unstop which is fully JS-rendered + API blocked.
"""
import logging, re
from .base_scraper import BaseScraper

logger = logging.getLogger(__name__)


class UnstopScraper(BaseScraper):
    """Renamed to keep import compatibility, now actually scrapes HackerEarth + Unstop RSS."""
    SOURCE_NAME = "HackerEarth"
    BASE_URL = "https://www.hackerearth.com/challenges/"

    CHALLENGE_APIS = [
        # HackerEarth public challenges API
        "https://www.hackerearth.com/challenges/json/",
        "https://api.hackerearth.com/v3/challenges/?type=hackathon&sort_by=start_date&order=desc&limit=20",
    ]

    def _parse_he_challenge(self, ch: dict) -> dict | None:
        title = ch.get("title") or ch.get("challenge_name") or ""
        if not title:
            return None
        slug = ch.get("url") or ch.get("challenge_url") or ""
        link = slug if slug.startswith("http") else f"https://www.hackerearth.com{slug}"
        start = ch.get("start_utc") or ch.get("start_date") or ""
        end = ch.get("end_utc") or ch.get("end_date") or ""
        deadline = str(end)[:10] if end else None
        prize_text = str(ch.get("prize_amount") or ch.get("prizes") or "")
        prize_amount = 0
        reward = "Certificate + Swag"
        if prize_text and prize_text.isdigit():
            prize_amount = int(prize_text)
            reward = f"${prize_amount:,}" if prize_amount > 0 else reward
        cat = "hackathon"
        if "internship" in title.lower():
            cat = "internship"
        elif "scholarship" in title.lower():
            cat = "scholarship"
        return self._make_opp(
            title=title[:120],
            category=cat,
            apply_link=link,
            source_url=link,
            deadline=deadline,
            reward=reward,
            reward_type="cash" if prize_amount > 0 else "certificate",
            prize_amount=prize_amount,
            eligibility="Students / Developers",
            tags=["HackerEarth", "Challenge", "Coding"],
            description=ch.get("description") or ch.get("tagline") or f"{title} on HackerEarth.",
            company="HackerEarth",
            location="Remote",
        )

    def scrape(self) -> list[dict]:
        results = []

        # Try HackerEarth public JSON API
        for api_url in self.CHALLENGE_APIS:
            try:
                resp = self.get(api_url)
                if not resp or resp.status_code != 200:
                    continue
                try:
                    data = resp.json()
                except Exception:
                    continue
                challenges = (
                    data.get("response", {}).get("challenges", [])
                    or data.get("challenges", [])
                    or (data if isinstance(data, list) else [])
                )
                for ch in challenges[:25]:
                    opp = self._parse_he_challenge(ch)
                    if opp:
                        results.append(opp)
                if results:
                    logger.info(f"[HackerEarth] API got {len(results)} results")
                    break
            except Exception as e:
                logger.debug(f"[HackerEarth] API error {api_url}: {e}")

        # Fallback: scrape HTML page
        if not results:
            try:
                import json as _json
                from bs4 import BeautifulSoup
                resp = self.get(self.BASE_URL)
                if resp and resp.status_code == 200:
                    soup = BeautifulSoup(resp.content, "lxml")
                    # HackerEarth embeds challenge data in script tags
                    for script in soup.find_all("script"):
                        txt = script.get_text() or ""
                        if "challenges" in txt and '"title"' in txt:
                            try:
                                m = re.search(r'challenges\s*[=:]\s*(\[.*?\])', txt, re.S)
                                if m:
                                    items = _json.loads(m.group(1))
                                    for it in items[:20]:
                                        opp = self._parse_he_challenge(it)
                                        if opp:
                                            results.append(opp)
                                    if results:
                                        break
                            except Exception:
                                pass

                    if not results:
                        # Generic card scraping
                        cards = (
                            soup.select(".challenge-card") or
                            soup.select("[class*='challenge']") or
                            soup.select("article") or
                            soup.select(".card")
                        )
                        for card in cards[:20]:
                            title_el = card.select_one("h2,h3,h4,[class*='title'],[class*='name']")
                            if not title_el:
                                continue
                            title = title_el.get_text(strip=True)
                            if not title or len(title) < 5:
                                continue
                            link_el = card.select_one("a[href]")
                            link = link_el.get("href", self.BASE_URL) if link_el else self.BASE_URL
                            if link.startswith("/"):
                                link = f"https://www.hackerearth.com{link}"
                            opp = self._make_opp(
                                title=title[:120],
                                category="hackathon",
                                apply_link=link,
                                source_url=self.BASE_URL,
                                reward="Certificate + Swag",
                                reward_type="certificate",
                                eligibility="Students / Developers",
                                tags=["HackerEarth", "Challenge"],
                                description=f"{title} on HackerEarth.",
                                company="HackerEarth",
                                location="Remote",
                            )
                            results.append(opp)
            except Exception as e:
                logger.warning(f"[HackerEarth] HTML fallback error: {e}")

        logger.info(f"[HackerEarth] Found {len(results)} challenges")
        return results
