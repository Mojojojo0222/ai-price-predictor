"""Tests for configuration module (config.py)."""

import config


def test_required_keys_present():
    """Every env var key must exist (even if empty) so the app never crashes on missing attrs."""
    for attr in [
        "SUPABASE_URL",
        "SUPABASE_KEY",
        "SUPABASE_SERVICE_KEY",
        "SCRAPERAPI_KEY",
        "TELEGRAM_BOT_TOKEN",
        "SMTP_EMAIL",
        "SMTP_PASSWORD",
        "APP_NAME",
        "APP_URL",
        "SCRAPE_INTERVAL_HOURS",
        "MAX_PRODUCTS_PER_USER",
        "PREDICTION_DAYS_AHEAD",
        "MIN_DATA_POINTS_FOR_PREDICTION",
    ]:
        assert hasattr(config, attr), f"missing config.{attr}"


def test_sensible_defaults():
    assert config.SCRAPE_INTERVAL_HOURS > 0
    assert config.MAX_PRODUCTS_PER_USER > 0
    assert config.PREDICTION_DAYS_AHEAD > 0
    assert config.MIN_DATA_POINTS_FOR_PREDICTION >= 3
    assert config.APP_NAME == "AI Price Predictor"
