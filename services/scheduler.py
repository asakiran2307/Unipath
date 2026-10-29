"""APScheduler-based background scrape scheduler — runs all scrapers every 4 hours."""
import logging
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from config import SCRAPE_INTERVAL_HOURS

logger = logging.getLogger(__name__)
_scheduler = None


def run_core_scrapers():
    """Run the 5 core web scrapers (no credentials needed)."""
    from scrapers import CORE_SCRAPERS
    from database import insert_opportunity, log_scrape
    from services.dedup_engine import deduplicate_list

    logger.info("Core scrape started...")
    for ScraperClass in CORE_SCRAPERS:
        scraper = ScraperClass()
        results, error = scraper.run()
        unique = deduplicate_list(results)
        new_count = 0
        dup_count = len(results) - len(unique)
        for opp in unique:
            _, is_new = insert_opportunity(opp)
            if is_new:
                new_count += 1
        log_scrape(
            source=scraper.SOURCE_NAME,
            status="success" if not error else "error",
            count_new=new_count,
            count_dup=dup_count,
            error=error,
        )
        logger.info(f"[{scraper.SOURCE_NAME}] +{new_count} new, {dup_count} duplicates skipped")
    logger.info("Core scrape complete.")


def run_social_scrapers():
    """Run Instagram and LinkedIn scrapers using stored credentials.
    NOTE: Twitter/X replaced by Google News RSS (now in run_core_scrapers).
    """
    from scrapers import SOCIAL_SCRAPER_MAP
    from database import (
        get_social_credentials, insert_opportunity,
        log_scrape, update_social_scrape_time,
    )
    from services.dedup_engine import deduplicate_list

    logger.info("Social media scrape started...")

    # ── Instagram (login required) ─────────────────────────────────────────────
    ig_config = get_social_credentials("instagram")
    ig_creds = ig_config.get("credentials", {})
    try:
        from scrapers.instagram_scraper import InstagramScraper
        scraper = InstagramScraper(
            ig_username=ig_creds.get("username"),
            ig_password=ig_creds.get("password"),
        )
        results, error = scraper.run()
        unique = deduplicate_list(results)
        new_count = sum(1 for opp in unique if insert_opportunity(opp)[1])
        log_scrape("Instagram", "success" if not error else "error",
                   new_count, len(results) - len(unique), error)
        update_social_scrape_time("instagram")
        logger.info(f"[Instagram] +{new_count} new opportunities")
    except Exception as e:
        log_scrape("Instagram", "error", 0, 0, str(e))
        logger.error(f"[Instagram] Scrape failed: {e}")

    # ── LinkedIn (works WITHOUT login via HTML scrape) ─────────────────────────
    li_config = get_social_credentials("linkedin")
    li_creds = li_config.get("credentials", {})
    try:
        from scrapers.linkedin_scraper import LinkedInScraper
        # Pass credentials only if configured; otherwise uses requests-based fallback
        scraper = LinkedInScraper(
            email=li_creds.get("email") or None,
            password=li_creds.get("password") or None,
            headless=True,
        )
        results, error = scraper.run()
        unique = deduplicate_list(results)
        new_count = sum(1 for opp in unique if insert_opportunity(opp)[1])
        log_scrape("LinkedIn", "success" if not error else "error",
                   new_count, len(results) - len(unique), error)
        update_social_scrape_time("linkedin")
        logger.info(f"[LinkedIn] +{new_count} new opportunities")
    except Exception as e:
        log_scrape("LinkedIn", "error", 0, 0, str(e))
        logger.error(f"[LinkedIn] Scrape failed: {e}")

    # Twitter/X → moved to Google News RSS in run_core_scrapers (no token needed)

    logger.info("Social media scrape complete.")


def run_all_scrapers():
    """Full scrape cycle: core + social."""
    run_core_scrapers()
    run_social_scrapers()


def start_scheduler():
    global _scheduler
    if _scheduler and _scheduler.running:
        return
    _scheduler = BackgroundScheduler(daemon=True)

    # Core scrapers every 4 hours
    _scheduler.add_job(
        run_core_scrapers,
        trigger=IntervalTrigger(hours=SCRAPE_INTERVAL_HOURS),
        id="core_scrape_job",
        name="Core Web Scrapers",
        replace_existing=True,
        misfire_grace_time=300,
    )

    # Social scrapers every 4 hours (offset by 30 min to stagger load)
    _scheduler.add_job(
        run_social_scrapers,
        trigger=IntervalTrigger(hours=SCRAPE_INTERVAL_HOURS, minutes=30),
        id="social_scrape_job",
        name="Social Media Scrapers",
        replace_existing=True,
        misfire_grace_time=300,
    )

    _scheduler.start()
    logger.info(f"Scheduler started: core every {SCRAPE_INTERVAL_HOURS}h, social every {SCRAPE_INTERVAL_HOURS}h+30m")


def stop_scheduler():
    global _scheduler
    if _scheduler and _scheduler.running:
        _scheduler.shutdown(wait=False)


def trigger_now():
    """Trigger full scrape immediately in background thread."""
    global _scheduler
    import threading
    t = threading.Thread(target=run_all_scrapers, daemon=True, name="manual-scrape")
    t.start()


def trigger_social_now():
    """Trigger only social scrapers immediately."""
    import threading
    t = threading.Thread(target=run_social_scrapers, daemon=True, name="social-scrape")
    t.start()


def trigger_core_now():
    """Trigger only core web scrapers immediately."""
    import threading
    t = threading.Thread(target=run_core_scrapers, daemon=True, name="core-scrape")
    t.start()
