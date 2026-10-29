"""
LinkedIn Scraper — uses Selenium to scrape LinkedIn job/internship posts.
Requires: LinkedIn email + password for authentication.
Targets company job boards and searches for student-friendly roles.
Falls back to LinkedIn public search without login.
"""
import re
import time
import random
import logging
from datetime import datetime, timedelta
from .base_scraper import BaseScraper

logger = logging.getLogger(__name__)

# Company pages to monitor on LinkedIn
LINKEDIN_COMPANIES = [
    "google", "microsoft", "amazon", "flipkart", "infosys",
    "wipro", "tcs", "hcltech", "accenture", "ibm",
    "deloitte", "morgan-stanley", "goldman-sachs",
    "meesho", "razorpay", "phonepe", "zomato", "swiggy",
    "freshworks", "zoho", "hashedin", "juspay",
]

# LinkedIn job search URLs (public, no login needed for basic)
LINKEDIN_SEARCH_URLS = [
    "https://www.linkedin.com/jobs/search/?keywords=internship%20student%20India&f_E=1&f_JT=I&location=India",
    "https://www.linkedin.com/jobs/search/?keywords=hackathon%202026&location=India",
    "https://www.linkedin.com/jobs/search/?keywords=software%20intern%20fresher%20India&f_E=1&location=India",
    "https://www.linkedin.com/jobs/search/?keywords=data%20science%20intern%20India&f_E=1&location=India",
]

OPPORTUNITY_KEYWORDS = [
    "intern", "internship", "hackathon", "fresher", "entry level",
    "trainee", "graduate", "campus", "2026 batch", "scholarship",
    "challenge", "fellowship",
]


class LinkedInScraper(BaseScraper):
    SOURCE_NAME = "LinkedIn"
    BASE_URL = "https://www.linkedin.com"

    def __init__(self, email: str = None, password: str = None, headless: bool = True):
        super().__init__()
        self.email = email
        self.password = password
        self.headless = headless
        self._driver = None
        self._logged_in = False

    def _get_driver(self):
        if self._driver:
            return self._driver
        try:
            from selenium import webdriver
            from selenium.webdriver.chrome.options import Options
            from selenium.webdriver.chrome.service import Service
            from webdriver_manager.chrome import ChromeDriverManager

            opts = Options()
            if self.headless:
                opts.add_argument("--headless=new")
            opts.add_argument("--no-sandbox")
            opts.add_argument("--disable-dev-shm-usage")
            opts.add_argument("--disable-gpu")
            opts.add_argument("--disable-notifications")
            opts.add_argument("--window-size=1920,1080")
            opts.add_argument(f"--user-agent={random.choice(__import__('config').USER_AGENTS)}")
            # Disable automation detection
            opts.add_experimental_option("excludeSwitches", ["enable-automation"])
            opts.add_experimental_option("useAutomationExtension", False)
            opts.add_argument("--disable-blink-features=AutomationControlled")

            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=opts)
            driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            self._driver = driver
            return driver
        except Exception as e:
            logger.error(f"[LinkedIn] Failed to start Chrome driver: {e}")
            return None

    def _login(self) -> bool:
        """Login to LinkedIn with email/password."""
        if self._logged_in:
            return True
        if not self.email or not self.password:
            logger.info("[LinkedIn] No credentials — using public search only")
            return False

        driver = self._get_driver()
        if not driver:
            return False

        try:
            from selenium.webdriver.common.by import By
            from selenium.webdriver.support.ui import WebDriverWait
            from selenium.webdriver.support import expected_conditions as EC

            driver.get("https://www.linkedin.com/login")
            time.sleep(2)

            wait = WebDriverWait(driver, 10)
            email_field = wait.until(EC.presence_of_element_located((By.ID, "username")))
            email_field.clear()
            email_field.send_keys(self.email)
            time.sleep(0.5)

            pw_field = driver.find_element(By.ID, "password")
            pw_field.clear()
            pw_field.send_keys(self.password)
            time.sleep(0.5)

            driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
            time.sleep(3)

            if "feed" in driver.current_url or "mynetwork" in driver.current_url:
                self._logged_in = True
                logger.info("[LinkedIn] Logged in successfully")
                return True
            else:
                logger.warning(f"[LinkedIn] Login may have failed. URL: {driver.current_url}")
                return False
        except Exception as e:
            logger.error(f"[LinkedIn] Login error: {e}")
            return False

    def _parse_job_card(self, card, driver) -> dict | None:
        """Parse a LinkedIn job card element."""
        try:
            from selenium.webdriver.common.by import By

            title_el = card.find_elements(By.CSS_SELECTOR, ".base-search-card__title, h3.job-card-list__title, h3")
            company_el = card.find_elements(By.CSS_SELECTOR, ".base-search-card__subtitle, h4.job-card-container__company-name")
            location_el = card.find_elements(By.CSS_SELECTOR, ".job-search-card__location, span.job-card-container__metadata-item")
            link_el = card.find_elements(By.CSS_SELECTOR, "a.base-card__full-link, a.job-card-list__title")

            title = title_el[0].text.strip() if title_el else ""
            company = company_el[0].text.strip() if company_el else ""
            location = location_el[0].text.strip() if location_el else "India"
            link = link_el[0].get_attribute("href") if link_el else self.BASE_URL

            if not title:
                return None

            title_lower = title.lower()
            if not any(kw in title_lower for kw in OPPORTUNITY_KEYWORDS):
                return None

            # Category detection
            if any(k in title_lower for k in ["intern", "internship", "trainee"]):
                category = "internship"
            elif any(k in title_lower for k in ["hackathon", "challenge", "competition"]):
                category = "hackathon"
            elif any(k in title_lower for k in ["fellowship", "scholarship"]):
                category = "scholarship"
            else:
                category = "job"

            return self._make_opp(
                title=title,
                category=category,
                apply_link=link or self.BASE_URL,
                source_url=link or self.BASE_URL,
                deadline=None,
                reward="As per company standards",
                reward_type="stipend" if category in ["internship", "job"] else "certificate",
                prize_amount=0,
                eligibility="Freshers / Students (see LinkedIn for details)",
                tags=["LinkedIn", "Verified", company[:20].strip()],
                description=f"{title} at {company}. Location: {location}. Posted on LinkedIn.",
                company=company,
                location=location,
            )
        except Exception as e:
            logger.debug(f"[LinkedIn] Card parse error: {e}")
            return None

    def _scrape_search_url(self, url: str) -> list[dict]:
        driver = self._get_driver()
        if not driver:
            return []

        results = []
        try:
            from selenium.webdriver.common.by import By
            from selenium.webdriver.support.ui import WebDriverWait
            from selenium.webdriver.support import expected_conditions as EC

            driver.get(url)
            time.sleep(random.uniform(3, 5))

            # Scroll to load more results
            for _ in range(3):
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(1.5)

            # Parse job cards
            cards = driver.find_elements(By.CSS_SELECTOR,
                ".base-search-card, .job-search-card, li.jobs-search-results__list-item")

            if not cards:
                # Try logged-in selectors
                cards = driver.find_elements(By.CSS_SELECTOR,
                    "li.jobs-search__results-list li, .job-card-container")

            for card in cards[:15]:
                opp = self._parse_job_card(card, driver)
                if opp:
                    results.append(opp)

        except Exception as e:
            logger.error(f"[LinkedIn] Scrape error for {url[:50]}: {e}")
        return results

    def _scrape_with_requests(self) -> list[dict]:
        """Fast fallback: scrape LinkedIn public job search pages with requests."""
        from bs4 import BeautifulSoup
        results = []
        urls = [
            "https://www.linkedin.com/jobs/search/?keywords=internship+india+students&f_E=1&f_JT=I",
            "https://www.linkedin.com/jobs/search/?keywords=hackathon+2026+india",
        ]
        for url in urls:
            try:
                resp = self.get(url)
                soup = BeautifulSoup(resp.content, "lxml")
                cards = soup.select(".base-search-card, .job-search-card")
                for card in cards[:12]:
                    title_el = card.select_one(".base-search-card__title")
                    company_el = card.select_one(".base-search-card__subtitle")
                    loc_el = card.select_one(".job-search-card__location")
                    link_el = card.select_one("a.base-card__full-link")

                    title = title_el.get_text(strip=True) if title_el else ""
                    company = company_el.get_text(strip=True) if company_el else ""
                    location = loc_el.get_text(strip=True) if loc_el else "India"
                    link = link_el["href"] if link_el and link_el.get("href") else url

                    if not title or not any(kw in title.lower() for kw in OPPORTUNITY_KEYWORDS):
                        continue

                    category = "internship" if "intern" in title.lower() else "job"
                    opp = self._make_opp(
                        title=title,
                        category=category,
                        apply_link=link,
                        source_url=link,
                        reward="As per company standards",
                        reward_type="stipend",
                        eligibility="Freshers / Students",
                        tags=["LinkedIn", company[:20]],
                        description=f"{title} at {company}.",
                        company=company,
                        location=location,
                    )
                    results.append(opp)
            except Exception as e:
                logger.warning(f"[LinkedIn] Requests fallback error: {e}")
        return results

    def scrape(self) -> list[dict]:
        results = []

        # Try login if credentials provided
        if self.email and self.password:
            logged_in = self._login()
            if logged_in:
                for url in LINKEDIN_SEARCH_URLS[:3]:
                    results.extend(self._scrape_search_url(url))
                    time.sleep(random.uniform(2, 4))
            else:
                logger.warning("[LinkedIn] Login failed, falling back to public search")
                results = self._scrape_with_requests()
        else:
            # No credentials — use requests-based public scrape
            results = self._scrape_with_requests()

        # Quit driver
        if self._driver:
            try:
                self._driver.quit()
            except Exception:
                pass
            self._driver = None

        logger.info(f"[LinkedIn] Total: {len(results)} opportunities found")
        return results
