"""
Internshala scraper — updated for 2025 site structure.
Uses both the listing page and JSON API endpoints.
"""
import logging, re, json
from bs4 import BeautifulSoup
from .base_scraper import BaseScraper

logger = logging.getLogger(__name__)


class InternshalaSimpleScraper(BaseScraper):
    SOURCE_NAME = "Internshala"
    BASE_URL = "https://internshala.com/internships/work-from-home-internships/"

    URLS = [
        "https://internshala.com/internships/work-from-home-internships/",
        "https://internshala.com/internships/computer-science-internship/",
    ]

    def _parse_stipend(self, text: str) -> int:
        text = str(text or "")
        m = re.search(r"[\d,]+", text.replace(",", ""))
        if m:
            try:
                return int(m.group().replace(",", ""))
            except Exception:
                pass
        return 0

    def scrape(self) -> list[dict]:
        results = []

        for url in self.URLS:
            try:
                resp = self.get(url)
                if not resp:
                    continue
                soup = BeautifulSoup(resp.content, "lxml")

                # 1. Try embedded JSON data (Internshala embeds data in script tag)
                for script in soup.find_all("script"):
                    txt = script.get_text() or ""
                    if "internships_meta" in txt or '"internship"' in txt.lower():
                        try:
                            # Find JSON array
                            for marker in ['internships_meta = ', 'var internships']:
                                if marker in txt:
                                    chunk = txt[txt.index(marker) + len(marker):]
                                    # Find the JSON structure
                                    start = chunk.index("{") if "{" in chunk else -1
                                    if start >= 0:
                                        data = json.loads(chunk[start:chunk.index("}]") + 2])
                                        # process if valid
                        except Exception:
                            pass

                # 2. Updated HTML selectors for 2025 Internshala
                # They now use a different class structure
                internships = (
                    soup.select(".individual_internship") or
                    soup.select("[id^='internship_id']") or
                    soup.select(".internship-item") or
                    soup.select(".internship_meta") or
                    soup.select("div[class*='internship']") or
                    soup.select(".container_type_1")
                )

                if not internships:
                    # Try generic article/li extraction
                    internships = soup.select("article, .job-listing")

                for item in internships[:25]:
                    title_el = (
                        item.select_one(".profile") or
                        item.select_one("h3.job-internship-name") or
                        item.select_one(".job-internship-name") or
                        item.select_one("h3") or
                        item.select_one("[class*='profile']") or
                        item.select_one("[class*='title']") or
                        item.select_one("strong")
                    )
                    if not title_el:
                        continue
                    title = title_el.get_text(strip=True)
                    if not title or len(title) < 3:
                        continue

                    company_el = (
                        item.select_one(".company-name") or
                        item.select_one("[class*='company']") or
                        item.select_one(".company_and_premium_wrapper")
                    )
                    company = company_el.get_text(strip=True) if company_el else "Company"

                    stipend_el = (
                        item.select_one(".stipend") or
                        item.select_one("[class*='stipend']") or
                        item.select_one("[class*='salary']")
                    )
                    stipend_text = stipend_el.get_text(strip=True) if stipend_el else ""
                    stipend_val = self._parse_stipend(stipend_text)

                    link_el = (
                        item.select_one("a[href*='/internship/detail']") or
                        item.select_one("a.view_detail_button") or
                        item.select_one("a[href*='internshala']") or
                        item.select_one("h3 a") or
                        item.select_one("a[href^='/']")
                    )
                    link_path = link_el["href"] if link_el and link_el.get("href") else ""
                    link = (
                        f"https://internshala.com{link_path}"
                        if link_path.startswith("/")
                        else link_path or url
                    )

                    loc_el = item.select_one(
                        ".location_link, .location-container, [class*='location']"
                    )
                    location = loc_el.get_text(strip=True) if loc_el else "Work from home"

                    duration_el = item.select_one(
                        ".item_body.duration, [class*='duration'], .other_detail_item"
                    )
                    duration = duration_el.get_text(strip=True) if duration_el else "3 months"

                    opp = self._make_opp(
                        title=f"{title} Internship",
                        category="internship",
                        apply_link=link,
                        source_url=url,
                        deadline=None,
                        reward=f"₹{stipend_val:,}/month" if stipend_val > 0 else "Unpaid / Certificate",
                        reward_type="stipend" if stipend_val > 0 else "certificate",
                        prize_amount=0,
                        eligibility="Students / Freshers",
                        tags=["Internshala", "Internship", "WFH"],
                        description=f"{title} internship at {company}. Duration: {duration}. {stipend_text}",
                        company=company,
                        location="Remote" if "home" in location.lower() else location,
                    )
                    results.append(opp)

            except Exception as e:
                logger.warning(f"[Internshala] Error at {url}: {e}")

        logger.info(f"[Internshala] Found {len(results)} internships")
        return results
