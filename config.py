import os

from dotenv import load_dotenv

load_dotenv()

# Supabase Configuration
SUPABASE_URL = os.getenv("SUPABASE_URL", "your-supabase-url")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "your-supabase-anon-key")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY", "your-supabase-service-role-key")

# ScraperAPI Configuration (free tier: 1000 req/month)
SCRAPERAPI_KEY = os.getenv("SCRAPERAPI_KEY", "")

# Telegram Bot Configuration
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")

# Gmail SMTP Configuration
SMTP_EMAIL = os.getenv("SMTP_EMAIL", "your-email@gmail.com")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "your-app-password")

# App Configuration
APP_NAME = "AI Price Predictor"
APP_URL = os.getenv("APP_URL", "http://localhost:8501")

# Scraper Settings
SCRAPE_INTERVAL_HOURS = 6
MAX_PRODUCTS_PER_USER = 50

# ML Settings
PREDICTION_DAYS_AHEAD = 30
MIN_DATA_POINTS_FOR_PREDICTION = 7
