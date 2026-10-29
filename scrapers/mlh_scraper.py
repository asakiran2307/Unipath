"""
MLH scraper — Major League Hacking uses Inertia.js.
Data is embedded in <div id='app' data-page='...'> as HTML-encoded JSON.
"""
import logging, json, re, html
from bs4 import BeautifulSoup
from .base_scraper import BaseScraper
from datetime import datetime

logger = logging.getLogger(__name__)


class MLHScraper(BaseScraper):
    SOURCE_NAME = "MLH"
    URLS = [
        "https://mlh.io/seasons/2026/events",
        "https://mlh.io/seasons/2025/events",
    ]

    def _parse_date(self, text: str) -> str | None:
        text = str(text or "").strip()
        formats = ["%Y-%m-%dT%H:%M:%S", "%Y-%m-%d", "%B %d, %Y", "%b %d, %Y"]
        for fmt in formats:
            try:
                return datetime.strptime(text[:len(fmt)], fmt).strftime("%Y-%m-%d")
            except Exception:
                pass
        # Try "April 12-14, 2025" style
        m = re.search(r"(\w+ \d+)[\-–]\d+,?\s*(\d{4})", text)
        if m:
            try:
                return datetime.strptime(f"{m.group(1)}, {m.group(2)}", "%B %d, %Y").strftime("%Y-%m-%d")
            except Exception:
                pass
        return None

    def scrape(self) -> list[dict]:
        results = []
        for base_url in self.URLS:
            try:
                resp = self.get(base_url)
                if not resp:
                    continue
                soup = BeautifulSoup(resp.content, "lxml")

                # MLH uses Inertia.js: data embedded in <div id="app" data-page="...">
                app_div = soup.find(id="app")
                if app_div and app_div.get("data-page"):
                    try:
                        page_data = json.loads(html.unescape(app_div["data-page"]))
                        props = page_data.get("props", {})
                        events = props.get("events", props.get("hackathons", []))
                        
                        for ev in events[:30]:
                            title = ev.get("name") or ev.get("title") or ""
                            if not title:
                                continue
                            link = ev.get("url") or ev.get("link") or ev.get("website") or base_url
                            start = ev.get("start_date") or ev.get("starts_at") or ""
                            end = ev.get("end_date") or ev.get("ends_at") or ""
                            deadline = self._parse_date(end or start)
                            location = ev.get("city") or ev.get("location") or "Remote"
                            if ev.get("is_virtual") or ev.get("hybrid"):
                                location = "Remote / Hybrid"
                            
                            opp = self._make_opp(
                                title=title[:120],
                                category="hackathon",
                                apply_link=link,
                                source_url=base_url,
                                deadline=deadline,
                                reward="MLH Certificate + Swag",
                                reward_type="certificate",
                                prize_amount=0,
                                eligibility="Students 18+",
                                tags=["MLH", "Hackathon", "Global"],
                                description=f"MLH-sanctioned hackathon: {title}.",
                                company="Major League Hacking",
                                location=location,
                            )
                            results.append(opp)
                        
                        if results:
                            logger.info(f"[MLH] Found {len(results)} events from Inertia data")
                            break
                    except Exception as e:
                        logger.debug(f"[MLH] Inertia parse error: {e}")

                # Fallback: parse script tags for JSON
                if not results:
                    for script in soup.find_all("script"):
                        txt = script.get_text() or ""
                        if '"events"' in txt or '"hackathons"' in txt:
                            try:
                                m = re.search(r'"events"\s*:\s*(\[.*?\])', txt, re.S)
                                if m:
                                    events = json.loads(m.group(1))
                                    for ev in events[:20]:
                                        title = ev.get("name") or ""
                                        if title:
                                            opp = self._make_opp(
                                                title=title,
                                                category="hackathon",
                                                apply_link=ev.get("url", base_url),
                                                source_url=base_url,
                                                reward="MLH Certificate",
                                                reward_type="certificate",
                                                eligibility="Students",
                                                tags=["MLH"],
                                                description=title,
                                                company="Major League Hacking",
                                            )
                                            results.append(opp)
                                    if results:
                                        break
                            except Exception:
                                pass

                if results:
                    break

            except Exception as e:
                logger.warning(f"[MLH] Error at {base_url}: {e}")

        logger.info(f"[MLH] Total: {len(results)} events")
        return results
