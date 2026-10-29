"""
Instagram Scraper — uses instaloader to pull posts from verified college/company accounts.
No login required for public accounts. For hashtag search, optional login improves results.
"""
import re
import logging
import hashlib
from datetime import datetime, timedelta
from .base_scraper import BaseScraper

logger = logging.getLogger(__name__)

# ── Target accounts (public profiles — no auth needed) ────────────────────────

COLLEGE_ACCOUNTS = [
    "iitbombay", "iitmadraslive", "iitroorkee_official", "iitkanpur",
    "iit.kharagpur", "iiithyderabad", "manit_bhopal", "nit.trichy",
    "vit.vellore", "manipalinstitute", "srmuniversity",
    "amityuniversity", "bits_pilani_official", "dtu_delhi",
]

COMPANY_ACCOUNTS = [
    "googleindia", "microsoftindia", "amazondev", "flipkartcareers",
    "infosys", "wipro", "tata.tcs", "freshworks_inc",
    "zoho", "phonepe_official", "swiggy", "zomato",
    "byju.s", "unacademy", "razorpay", "cred_club",
]

HACKATHON_ACCOUNTS = [
    "unstopworld", "devfolio", "hackerearth",
    "hackerrank_official", "mlhacks", "gdsc_india",
    "githubindia", "awsindia", "googledevs",
]

ALL_ACCOUNTS = COLLEGE_ACCOUNTS + COMPANY_ACCOUNTS + HACKATHON_ACCOUNTS

OPPORTUNITY_KEYWORDS = [
    "hackathon", "internship", "scholarship", "hiring", "apply now",
    "registration open", "last date", "deadline", "cash prize",
    "stipend", "opportunity", "challenge", "competition", "contest",
    "buildathon", "datathon", "workshop", "bootcamp", "fellowship",
    "recruit", "job opening", "career", "campus hiring",
]

MAX_POST_AGE_DAYS = 30   # Only posts from last 30 days
MAX_POSTS_PER_ACCOUNT = 10


class InstagramScraper(BaseScraper):
    SOURCE_NAME = "Instagram"
    BASE_URL = "https://www.instagram.com"

    def __init__(self, ig_username=None, ig_password=None):
        super().__init__()
        self.ig_username = ig_username
        self.ig_password = ig_password
        self._loader = None

    def _get_loader(self):
        if self._loader:
            return self._loader
        try:
            import instaloader
            L = instaloader.Instaloader(
                quiet=True,
                download_pictures=False,
                download_videos=False,
                download_video_thumbnails=False,
                download_geotags=False,
                download_comments=False,
                save_metadata=False,
                compress_json=False,
            )
            # Login if credentials provided
            if self.ig_username and self.ig_password:
                try:
                    L.login(self.ig_username, self.ig_password)
                    logger.info("[Instagram] Logged in successfully")
                except Exception as e:
                    logger.warning(f"[Instagram] Login failed (continuing without auth): {e}")
            self._loader = L
            return L
        except ImportError:
            logger.error("[Instagram] instaloader not installed")
            return None

    def _is_opportunity_post(self, caption: str) -> bool:
        if not caption:
            return False
        caption_lower = caption.lower()
        return any(kw in caption_lower for kw in OPPORTUNITY_KEYWORDS)

    def _parse_caption(self, caption: str, account: str, post_url: str) -> dict | None:
        """Extract opportunity data from Instagram caption using regex + AI."""
        if not caption or not self._is_opportunity_post(caption):
            return None

        caption_lower = caption.lower()

        # Determine category
        if any(k in caption_lower for k in ["hackathon", "buildathon", "datathon", "challenge", "contest", "competition"]):
            category = "hackathon"
        elif any(k in caption_lower for k in ["internship", "intern ", "stipend", "hiring intern"]):
            category = "internship"
        elif any(k in caption_lower for k in ["scholarship", "fellowship", "grant", "financial aid"]):
            category = "scholarship"
        elif any(k in caption_lower for k in ["workshop", "bootcamp", "webinar", "seminar", "training"]):
            category = "workshop"
        elif any(k in caption_lower for k in ["job", "hiring", "recruit", "opening", "vacancy"]):
            category = "job"
        else:
            category = "hackathon"

        # Extract prize/reward
        prize_amount = 0
        reward = ""
        reward_type = "certificate"
        prize_patterns = [
            (r"(?:prize|reward|cash|win)[^\n]*?(?:₹|rs\.?|inr)\s*([\d,]+)\s*(?:lakh|l\b)", 100000),
            (r"(?:₹|rs\.?|inr)\s*([\d,]+)\s*(?:lakh|l\b)", 100000),
            (r"(?:₹|rs\.?|inr)\s*([\d,]+)\s*(?:k\b|thousand)", 1000),
            (r"(?:₹|rs\.?|inr)\s*([\d,]+)", 1),
            (r"\$([\d,]+)\s*(?:k|thousand)", 83000),
            (r"\$([\d,]+)", 83),
        ]
        for pattern, multiplier in prize_patterns:
            m = re.search(pattern, caption, re.IGNORECASE)
            if m:
                prize_amount = int(m.group(1).replace(",", "")) * multiplier
                reward = m.group(0).strip()
                reward_type = "cash"
                break

        if not reward:
            if any(k in caption_lower for k in ["stipend", "salary", "ctc", "lpa"]):
                reward_type = "stipend"
                reward = "Paid Internship"
            elif any(k in caption_lower for k in ["free", "no cost", "complimentary"]):
                reward_type = "free"
                reward = "Free"
            else:
                reward = "Certificate"
                reward_type = "certificate"

        # Extract deadline
        deadline = None
        dl_patterns = [
            r"(?:deadline|last date|apply by|register by|closes?)\s*[:\-]?\s*(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4})",
            r"(\d{1,2})\s*(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\w*\s*(\d{4}|\d{2})?",
        ]
        for pat in dl_patterns:
            m = re.search(pat, caption, re.IGNORECASE)
            if m:
                try:
                    raw = m.group(0)
                    for fmt in ["%d/%m/%Y", "%d-%m-%Y", "%d.%m.%Y", "%d/%m/%y"]:
                        try:
                            d = datetime.strptime(raw.split(":")[1].strip() if ":" in raw else raw, fmt)
                            deadline = d.strftime("%Y-%m-%d")
                            break
                        except Exception:
                            continue
                except Exception:
                    pass
                break

        # Extract links from caption (URLs)
        link_pattern = r"https?://[^\s\)\]>\"']+|linktr\.ee/\S+"
        links = re.findall(link_pattern, caption)
        apply_link = links[0] if links else f"https://www.instagram.com/{account}"

        # Extract hashtags as tags
        hashtags = re.findall(r"#(\w+)", caption)
        tags = [h for h in hashtags if h.lower() not in ["hackathon", "internship"] and len(h) > 2][:5]
        tags = ["Instagram", account.replace("_", " ").title()] + tags[:4]

        # Extract title from first line of caption
        first_line = caption.strip().split("\n")[0][:80]
        title = first_line if len(first_line) > 10 else f"{category.title()} from @{account}"
        title = re.sub(r"^[#\s]+", "", title).strip()[:100]

        if not title or len(title) < 8:
            return None

        return self._make_opp(
            title=title,
            category=category,
            apply_link=apply_link,
            source_url=post_url,
            deadline=deadline,
            reward=reward,
            reward_type=reward_type,
            prize_amount=prize_amount,
            eligibility="Students (via Instagram)",
            tags=list(dict.fromkeys(tags)),
            description=caption[:400],
            company=f"@{account}",
            location="Remote",
        )

    def _scrape_account(self, account: str) -> list[dict]:
        import instaloader
        results = []
        L = self._get_loader()
        if not L:
            return results
        try:
            profile = instaloader.Profile.from_username(L.context, account)
            cutoff = datetime.now() - timedelta(days=MAX_POST_AGE_DAYS)
            count = 0
            for post in profile.get_posts():
                if count >= MAX_POSTS_PER_ACCOUNT:
                    break
                if post.date_local < cutoff:
                    break
                count += 1
                post_url = f"https://www.instagram.com/p/{post.shortcode}/"
                caption = post.caption or ""
                opp = self._parse_caption(caption, account, post_url)
                if opp:
                    results.append(opp)
        except instaloader.exceptions.ProfileNotExistsException:
            logger.debug(f"[Instagram] Account @{account} not found, skipping")
        except instaloader.exceptions.ConnectionException as e:
            logger.warning(f"[Instagram] Connection error for @{account}: {e}")
        except Exception as e:
            logger.error(f"[Instagram] Error scraping @{account}: {e}")
        return results

    def _scrape_hashtags(self, tags: list[str]) -> list[dict]:
        """Scrape recent posts by hashtag (requires login for best results)."""
        import instaloader
        results = []
        L = self._get_loader()
        if not L:
            return results
        if not self.ig_username:
            logger.debug("[Instagram] Skipping hashtag scrape (no login)")
            return results
        for tag in tags:
            try:
                hashtag = instaloader.Hashtag.from_name(L.context, tag)
                cutoff = datetime.now() - timedelta(days=14)
                count = 0
                for post in hashtag.get_recent_posts():
                    if count >= 8:
                        break
                    if post.date_local < cutoff:
                        break
                    count += 1
                    post_url = f"https://www.instagram.com/p/{post.shortcode}/"
                    opp = self._parse_caption(post.caption or "", f"#{tag}", post_url)
                    if opp:
                        opp["tags"] = [tag.title(), "Instagram", "Social"] + opp.get("tags", [])[:3]
                        results.append(opp)
            except Exception as e:
                logger.warning(f"[Instagram] Hashtag #{tag} error: {e}")
        return results

    def scrape(self) -> list[dict]:
        results = []
        import time
        for account in ALL_ACCOUNTS:
            posts = self._scrape_account(account)
            results.extend(posts)
            if posts:
                logger.info(f"[Instagram] @{account}: {len(posts)} opportunities found")
            time.sleep(2)  # Rate limiting between accounts

        # Hashtag scraping (needs login)
        hashtag_results = self._scrape_hashtags(["hackathon2026", "internship2026", "techfest"])
        results.extend(hashtag_results)

        logger.info(f"[Instagram] Total: {len(results)} opportunities parsed")
        return results
