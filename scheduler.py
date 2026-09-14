import threading
import time
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from typing import Optional, Dict

from scraper import scrape_product, check_price_drop
from predictor import analyze_product
from alerts import dispatch_price_alert
from database import (
    get_all_tracked_products,
    add_price_history,
    get_price_history,
    save_prediction,
    get_latest_price
)
from config import SCRAPE_INTERVAL_HOURS

# Global scheduler instance
_scheduler: Optional[BackgroundScheduler] = None
_lock = threading.Lock()


def check_and_alert_for_user_track(track: Dict) -> None:
    """Check price and send alerts for a single user-product track"""
    try:
        product = track.get("products")
        if not product or not product.get("url"):
            return

        user = track.get("user", {})
        url = product["url"]

        # Scrape current price
        result = scrape_product(url)
        if not result.get("success"):
            return

        current_price = result["price"]
        product_id = product["id"]

        # Get previous price
        prev_record = get_latest_price(product_id)
        old_price = prev_record["price"] if prev_record else None

        # Store new price
        add_price_history(
            product_id=product_id,
            price=current_price,
            source=result.get("source", "unknown")
        )

        # Get full price history for prediction
        history = get_price_history(product_id, days=90)

        # Run analysis
        analysis = analyze_product(history, product.get("name"))

        if analysis.get("status") == "ANALYZED":
            # Save prediction
            save_prediction(
                product_id=product_id,
                predicted_low=analysis["predicted_low"],
                current_price=current_price,
                confidence=analysis["confidence"],
                recommendation=analysis["recommendation"],
                predicted_date=analysis.get("predicted_low_date", datetime.now().isoformat()),
                reasoning=analysis.get("reasoning", "")
            )

        # Check if we should send alerts
        if old_price and current_price:
            dropped, drop_pct = check_price_drop(current_price, old_price)

            target_reached = (
                track.get("target_price") and
                current_price <= float(track["target_price"])
            )

            if dropped or target_reached:
                dispatch_price_alert(
                    user=user,
                    track=track,
                    product_data=product,
                    old_price=old_price,
                    new_price=current_price,
                    drop_percent=drop_pct,
                    prediction=analysis,
                    target_reached=target_reached
                )

    except Exception as e:
        pass  # Silently fail - will retry next interval


def run_price_checks() -> None:
    """Main scheduler job: check all tracked products"""
    try:
        tracks = get_all_tracked_products()
        for track in tracks:
            check_and_alert_for_user_track(track)
            time.sleep(2)  # Rate limiting
    except Exception as e:
        pass


def get_scheduler() -> BackgroundScheduler:
    """Get or create the global scheduler instance"""
    global _scheduler

    with _lock:
        if _scheduler is None or _scheduler.state == "shutdown":
            _scheduler = BackgroundScheduler(
                job_defaults={"coalesce": True, "max_instances": 1}
            )
            _scheduler.add_job(
                run_price_checks,
                "interval",
                hours=SCRAPE_INTERVAL_HOURS,
                id="price_check",
                name="Periodic Price Check",
                replace_existing=True
            )
        return _scheduler


def start_scheduler() -> None:
    """Start the background scheduler"""
    scheduler = get_scheduler()
    if not scheduler.running:
        try:
            scheduler.start()
        except Exception:
            pass


def stop_scheduler() -> None:
    """Stop the background scheduler"""
    global _scheduler
    with _lock:
        if _scheduler and _scheduler.running:
            try:
                _scheduler.shutdown(wait=False)
            except Exception:
                pass
            _scheduler = None


def get_scheduler_status() -> Dict:
    """Get scheduler status info"""
    scheduler = get_scheduler()
    jobs = []
    for job in scheduler.get_jobs():
        jobs.append({
            "id": job.id,
            "name": job.name,
            "next_run": str(job.next_run_time) if job.next_run_time else "Not scheduled"
        })

    return {
        "running": scheduler.running,
        "jobs": jobs,
        "interval_hours": SCRAPE_INTERVAL_HOURS
    }