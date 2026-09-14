# AI Price Predictor - Project Context

## Overview
A personalized AI-powered price tracking and prediction web application. Users can track products, get price drop alerts, and receive AI-powered "buy now" or "wait" recommendations.

## Tech Stack
- **Frontend/Backend**: Streamlit (single app)
- **Database**: Supabase (PostgreSQL) - free tier
- **Auth**: Supabase Auth (Google OAuth) - free tier
- **Scraping**: requests + BeautifulSoup + ScraperAPI (free tier: 1000 req/month)
- **ML/AI**: scikit-learn (local, free)
- **Alerts**: Telegram Bot API (free) + Gmail SMTP (free)
- **Scheduler**: APScheduler (runs in-app)
- **Hosting**: Streamlit Cloud (free)

## Database Schema (Supabase)

### Tables
```sql
-- Users (auto-managed by Supabase Auth)
-- email, name, avatar stored in auth.users

-- products: Store tracked products
CREATE TABLE products (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  url TEXT NOT NULL,
  name TEXT,
  image_url TEXT,
  category TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- price_history: Historical prices
CREATE TABLE price_history (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  product_id UUID REFERENCES products(id) ON DELETE CASCADE,
  price DECIMAL(10,2) NOT NULL,
  currency TEXT DEFAULT 'INR',
  source TEXT,
  scraped_at TIMESTAMPTZ DEFAULT NOW()
);

-- user_tracks: Users' tracked products with preferences
CREATE TABLE user_tracks (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
  product_id UUID REFERENCES products(id) ON DELETE CASCADE,
  target_price DECIMAL(10,2),
  alert_enabled BOOLEAN DEFAULT TRUE,
  alert_email BOOLEAN DEFAULT TRUE,
  alert_telegram BOOLEAN DEFAULT FALSE,
  telegram_chat_id TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE(user_id, product_id)
);

-- predictions: AI predictions per product
CREATE TABLE predictions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  product_id UUID REFERENCES products(id) ON DELETE CASCADE,
  predicted_low DECIMAL(10,2),
  current_price DECIMAL(10,2),
  confidence DECIMAL(5,2),
  recommendation TEXT CHECK (recommendation IN ('BUY_NOW', 'WAIT', 'NO_DATA')),
  predicted_date DATE,
  reasoning TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW()
);
```

## Project Structure
```
price-predictor/
├── AGENTS.md              ← THIS FILE (project context)
├── PROGRESS.md            ← Task progress tracker
├── app.py                 ← Main Streamlit app (entry point)
├── config.py              ← Environment variables & config
├── database.py            ← Supabase CRUD operations
├── auth.py                ← Authentication logic
├── scraper.py             ← Price scraping module
├── predictor.py           ← ML prediction model
├── alerts.py              ← Telegram & Email alerts
├── scheduler.py           ← Background price checker
├── charts.py              ← Price history charts
├── requirements.txt       ← Python dependencies
├── .streamlit/
│   └── config.toml        ← Streamlit theme config
└── README.md              ← (not created unless asked)
```

## Key Decisions
1. Single Streamlit app (no separate FastAPI) - simpler deployment
2. Supabase for both DB and Auth - single service, easy setup
3. ScraperAPI free tier for 1000 scrapes/month
4. scikit-learn for ML (linear regression + time features)
5. Telegram for instant alerts (most reliable free option)
6. Gmail SMTP as backup alert channel

## How to Resume This Project
1. Read this file (AGENTS.md)
2. Read PROGRESS.md for current state
3. Check the existing code files
4. Continue from where progress left off

## Free Tier Limits to Track
- Supabase: 500MB DB, 50k monthly active users
- ScraperAPI: 1,000 requests/month
- Streamlit Cloud: Unlimited apps
- Telegram Bot: Unlimited messages
- Gmail SMTP: 500 emails/day
