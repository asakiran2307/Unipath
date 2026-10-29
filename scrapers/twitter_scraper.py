"""
Twitter/X Scraper — uses Tweepy v2 API to find recent hackathon/internship tweets.
Requires: Twitter API v2 Bearer Token (Free tier supported).
Filters to verified accounts and high-engagement posts from colleges/companies.
"""
import re
import logging
from datetime import datetime, timezone, timedelta
from .base_scraper import BaseScraper

logger = logging.getLogger(__name__)

SEARCH_QUERIES = [
    "#hackathon registration open -is:retweet lang:en",
    "#internship apply now India -is:retweet lang:en",
    "#scholarship students India 2026 -is:retweet lang:en",
    "hackathon cash prize registration India -is:retweet lang:en",
    "internship stipend India students apply -is:retweet lang:en",
    "#buildathon OR #datathon OR #codathon -is:retweet lang:en",
]

# Verified/trusted Twitter accounts to monitor directly
VERIFIED_ACCOUNTS = [
    "IITBombay", "IITMadras", "IITDelhi", "IITRoorkee", "IITKanpur",
    "IITKgp", "IIIT_H", "NITKarnataka",
    "unstopworld", "devfolio", "HackerEarth", "HackerRank", "MLH",
    "GoogleIndia", "MicrosoftIndia", "AmazonNews", "Infosys", "Wipro",
    "TCS", "NASSCOM", "AICTEIndia", "EduMinOfIndia",
]

OPPORTUNITY_KEYWORDS = [
    "hackathon", "register", "apply", "internship", "scholarship",
    "deadline", "prize", "hiring", "opportunity", "challenge",
    "competition", "contest", "fellowship", "stipend",
]


class TwitterScraper(BaseScraper):
    SOURCE_NAME = "Twitter/X"
    BASE_URL = "https://twitter.com"

    def __init__(self, bearer_token: str = None, api_key: str = None,
                 api_secret: str = None, access_token: str = None,
                 access_token_secret: str = None):
        super().__init__()
        self.bearer_token = bearer_token
        self.api_key = api_key
        self.api_secret = api_secret
        self.access_token = access_token
        self.access_token_secret = access_token_secret
        self._client = None

    def _get_client(self):
        if self._client:
            return self._client
        if not self.bearer_token:
            logger.warning("[Twitter] No Bearer Token configured — skipping")
            return None
        try:
            import tweepy
            self._client = tweepy.Client(
                bearer_token=self.bearer_token,
                consumer_key=self.api_key,
                consumer_secret=self.api_secret,
                access_token=self.access_token,
                access_token_secret=self.access_token_secret,
                wait_on_rate_limit=True,
            )
            logger.info("[Twitter] Client initialized")
            return self._client
        except ImportError:
            logger.error("[Twitter] tweepy not installed")
            return None
        except Exception as e:
            logger.error(f"[Twitter] Client init failed: {e}")
            return None

    def _is_opportunity_tweet(self, text: str) -> bool:
        text_lower = text.lower()
        return sum(1 for kw in OPPORTUNITY_KEYWORDS if kw in text_lower) >= 2

    def _parse_tweet(self, text: str, tweet_id: str, author_name: str = "") -> dict | None:
        if not self._is_opportunity_tweet(text):
            return None

        text_lower = text.lower()
        tweet_url = f"https://twitter.com/i/web/status/{tweet_id}"

        # Category
        if any(k in text_lower for k in ["hackathon", "buildathon", "datathon", "competition", "contest", "challenge"]):
            category = "hackathon"
        elif any(k in text_lower for k in ["internship", "intern ", "stipend"]):
            category = "internship"
        elif any(k in text_lower for k in ["scholarship", "fellowship"]):
            category = "scholarship"
        elif any(k in text_lower for k in ["workshop", "webinar", "bootcamp"]):
            category = "workshop"
        elif any(k in text_lower for k in ["hiring", "job", "opening", "vacancy"]):
            category = "job"
        else:
            category = "hackathon"

        # Prize
        prize_amount = 0
        reward_type = "certificate"
        reward = ""
        prize_m = re.search(r"(?:₹|rs\.?|inr|\$)\s*([\d,]+)\s*(?:lakh|l|k|thousand)?", text, re.IGNORECASE)
        if prize_m:
            amt_str = prize_m.group(1).replace(",", "")
            multiplier = 100000 if re.search(r"lakh|l\b", text, re.I) else (1000 if re.search(r"k\b|thousand", text, re.I) else 1)
            if "$" in prize_m.group(0):
                multiplier = max(multiplier, 83)
            prize_amount = int(amt_str) * multiplier
            reward = prize_m.group(0).strip()
            reward_type = "cash"

        if not reward:
            if re.search(r"stipend|salary|paid", text, re.I):
                reward_type = "stipend"
                reward = "Paid"
            else:
                reward = "Certificate / Swag"

        # Links in tweet
        links = re.findall(r"https?://[^\s\)\]>]+", text)
        apply_link = next((l for l in links if "twitter.com" not in l), tweet_url)

        # Deadline
        deadline = None
        dl_m = re.search(r"(\d{1,2})\s*(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\w*\s*(202\d)", text, re.I)
        if dl_m:
            try:
                deadline = datetime.strptime(f"{dl_m.group(1)} {dl_m.group(2)[:3]} {dl_m.group(3)}", "%d %b %Y").strftime("%Y-%m-%d")
            except Exception:
                pass

        # Build title from tweet first line
        first_line = text.strip().split("\n")[0][:90]
        title = re.sub(r"https?://\S+", "", first_line).strip()
        title = re.sub(r"^[#@\s]+", "", title).strip()[:90]
        if len(title) < 10:
            title = f"{category.title()} from @{author_name}"

        # Tags from hashtags
        hashtags = re.findall(r"#(\w+)", text)
        tags = ["Twitter/X", "Social Media"] + [h for h in hashtags if len(h) > 2][:4]

        return self._make_opp(
            title=title,
            category=category,
            apply_link=apply_link,
            source_url=tweet_url,
            deadline=deadline,
            reward=reward,
            reward_type=reward_type,
            prize_amount=prize_amount,
            eligibility="See tweet for eligibility details",
            tags=list(dict.fromkeys(tags)),
            description=text[:400],
            company=f"@{author_name}",
            location="Remote",
        )

    def _search_recent(self) -> list[dict]:
        import tweepy
        client = self._get_client()
        if not client:
            return []

        results = []
        seven_days_ago = datetime.now(timezone.utc) - timedelta(days=7)

        for query in SEARCH_QUERIES[:4]:  # Limit API calls
            try:
                tweets = client.search_recent_tweets(
                    query=query,
                    max_results=25,
                    tweet_fields=["created_at", "author_id", "public_metrics", "text"],
                    user_fields=["name", "username", "verified", "public_metrics"],
                    expansions=["author_id"],
                    start_time=seven_days_ago,
                )
                if not tweets.data:
                    continue

                # Build user map
                users = {u.id: u for u in (tweets.includes.get("users") or [])}

                for tweet in tweets.data:
                    author = users.get(tweet.author_id)
                    author_name = author.username if author else "unknown"
                    metrics = tweet.public_metrics or {}
                    # Filter: min engagement (likes + retweets >= 5)
                    if (metrics.get("like_count", 0) + metrics.get("retweet_count", 0)) < 3:
                        continue
                    opp = self._parse_tweet(tweet.text, str(tweet.id), author_name)
                    if opp:
                        results.append(opp)
            except tweepy.TooManyRequests:
                logger.warning("[Twitter] Rate limit hit, stopping search")
                break
            except Exception as e:
                logger.error(f"[Twitter] Search query failed: {e}")

        return results

    def _monitor_accounts(self) -> list[dict]:
        """Get recent tweets from specific verified accounts."""
        import tweepy
        client = self._get_client()
        if not client:
            return []

        results = []
        for username in VERIFIED_ACCOUNTS[:12]:  # Limit API calls
            try:
                user_resp = client.get_user(username=username)
                if not user_resp.data:
                    continue
                user_id = user_resp.data.id

                tweets = client.get_users_tweets(
                    id=user_id,
                    max_results=10,
                    tweet_fields=["created_at", "text"],
                    exclude=["retweets", "replies"],
                    start_time=datetime.now(timezone.utc) - timedelta(days=7),
                )
                if not tweets.data:
                    continue

                for tweet in tweets.data:
                    opp = self._parse_tweet(tweet.text, str(tweet.id), username)
                    if opp:
                        opp["source"] = f"Twitter/@{username}"
                        results.append(opp)
            except tweepy.TooManyRequests:
                logger.warning("[Twitter] Rate limit in account monitor")
                break
            except Exception as e:
                logger.debug(f"[Twitter] @{username} error: {e}")

        return results

    def scrape(self) -> list[dict]:
        client = self._get_client()
        if not client:
            return []

        results = self._search_recent()
        account_results = self._monitor_accounts()
        results.extend(account_results)
        logger.info(f"[Twitter] Total: {len(results)} opportunities found")
        return results
