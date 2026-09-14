<div align="center">

# 🔮 AI Price Predictor

### Smart, personalized "when to buy" forecasts for your favorite products

Track any Amazon/Flipkart product. Our ML engine predicts future price dips and tells you exactly **when to buy** — powered by scikit-learn, served entirely on free cloud infrastructure.

[![Python](https://img.shields.io/badge/Python-3.12-blue.svg?logo=python&logoColor=white)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.31-red.svg?logo=streamlit&logoColor=white)](https://streamlit.io/)
[![Supabase](https://img.shields.io/badge/Supabase-PostgresQL-green.svg?logo=supabase&logoColor=white)](https://supabase.com/)
[![scikit-learn](https://img.shields.io/badge/scikit--learn-RandomForest-orange.svg?logo=scikit-learn&logoColor=white)](https://scikit-learn.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](http://makeapullrequest.com)

**Stop guessing. Start saving.**

</div>

---

## 📖 Table of Contents

- [Why This Project](#-why-this-project)
- [Features](#-features)
- [How It Works](#-how-it-works)
- [Architecture](#-architecture)
- [Tech Stack](#-tech-stack)
- [Getting Started](#-getting-started)
  - [Prerequisites](#prerequisites)
  - [Local Setup](#local-setup)
  - [Database Setup](#database-setup)
  - [Running the App](#-running-the-app)
- [Project Structure](#-project-structure)
- [The AI/ML Engine](#-the-aiml-engine)
- [Alert System](#-alert-system)
- [Deployment](#-deployment)
- [Roadmap](#-roadmap)
- [Contributing](#-contributing)
- [License](#-license)

---

## 🎯 Why This Project

Online prices fluctuate constantly — a ₹75,000 phone could drop to ₹62,000 during a sale, or you might wait months for a discount that never comes. Existing price trackers just *log* prices; they never tell you *what to do*.

**AI Price Predictor isn't a tracker. It's a decision engine.**

> **Problem:** "Should I buy now or wait?"
> **Answer:** "Wait — predicted to drop 11% during the Diwali sale (confidence: 82%)."

It combines **time-series ML forecasting** with **rule-based recommendation logic** to produce a single, actionable answer for every tracked product — then alerts you the moment the price hits your target.

---

## ✨ Features

| Category | Capability |
|----------|-----------|
| 📦 **Product Tracking** | Unlimited products from Amazon.in & Flipkart |
| 🧠 **AI Forecasting** | RandomForest regression predicts price dips up to 30 days ahead |
| 🎯 **Buy / Wait Advice** | Clear recommendation + confidence score + plain-English reasoning |
| 🔔 **Real-time Alerts** | Telegram & Email when prices drop or hit your target price |
| 📈 **Interactive Analytics** | Plotly charts with prediction overlays, confidence bands & savings gauges |
| 👤 **Multi-user** | Personalized dashboards with Google OAuth / email sign-in |
| 🗓️ **Automatic Monitoring** | Background scheduler checks prices every 6 hours |
| 💸 **Zero Cost** | Runs entirely on free tiers (Streamlit Cloud + Supabase) |

---

## 🧠 How It Works

```
1. TRACK      Paste any Amazon/Flipkart URL → app scrapes the live price
              and stores it in a time-series history (price_history)

2. MONITOR    A background APScheduler job re-scrapes every 6 hours,
              building a rich price-history dataset per product

3. PREDICT    The ML engine extracts temporal features
              (day_of_week, month, festive-season flags)
              and trains a RandomForest regressor to forecast the next 30 days

4. DECIDE     Rule engine converts the forecast into an actionable
              verdict: BUY_NOW 🟢 / WAIT 🟡 / NO_DATA ⚪
              with a confidence score & human-readable reasoning

5. ALERT      When the price drops >3% (or hits your target),
              you get an instant Telegram/Email notification
```

---

## 🏗️ Architecture

```
┌─────────────────────────── STREAMLIT APP (app.py) ───────────────────────────┐
│                                                                              │
│   ┌────────────┐  ┌─────────────┐  ┌───────────────┐  ┌──────────────────┐  │
│   │ Dashboard  │  │ Add Product │  │ Product View  │  │ Alert Settings   │  │
│   │ (cards)    │  │ (URL input) │  │ (charts+ML)   │  │ (Telegram/Email) │  │
│   └─────┬──────┘  └──────┬──────┘  └───────┬───────┘  └────────┬─────────┘  │
│         │                │                 │                    │            │
└─────────┼────────────────┼─────────────────┼────────────────────┼────────────┘
          │                │                 │                    │
          ▼                ▼                 ▼                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           APPLICATION LAYER                                  │
│  auth.py   → Supabase Auth (email + Google OAuth)                            │
│  scraper.py→ Amazon/Flipkart scrapers (UA rotation + ScraperAPI fallback)    │
│  predictor.py→ Feature engineering + RandomForest + Buy/Wait rule engine     │
│  alerts.py → Telegram Bot API + Gmail SMTP dispatcher                        │
│  scheduler.py→ APScheduler, price checks every 6h, triggers alerts           │
│  charts.py → Plotly visualizations + styled HTML components                  │
└───────────────────────────────┬─────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                                SUPABASE (free tier)                          │
│  ┌─────────────┐  ┌──────────────┐  ┌──────────────┐  ┌─────────────────┐   │
│  │  products   │  │ price_history │  │ user_tracks  │  │  predictions    │   │
│  └─────────────┘  └──────────────┘  └──────────────┘  └─────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 🧑‍💻 Tech Stack

| Layer        | Technology                                                                 |
|--------------|----------------------------------------------------------------------------|
| Frontend     | [Streamlit](https://streamlit.io/) — reactive, Python-native web apps       |
| Backend      | Python 3.12 — single-codebase app                                          |
| Database     | [Supabase](https://supabase.com/) — hosted PostgreSQL + Auth (free tier)    |
| ML / AI      | [scikit-learn](https://scikit-learn.org/) — RandomForestRegressor          |
| Data         | [pandas](https://pandas.pydata.org/) + [NumPy](https://numpy.org/)         |
| Charts       | [Plotly](https://plotly.com/python/) — interactive graphs                   |
| Scraping     | [BeautifulSoup](https://www.crummy.com/software/BeautifulSoup/) + requests |
| Scheduling   | [APScheduler](https://apscheduler.readthedocs.io/)                         |
| Alerts       | Telegram Bot API + Gmail SMTP                                              |
| Deployment   | [Streamlit Cloud](https://streamlit.io/cloud) (free) + GitHub Actions       |

---

## 🚀 Getting Started

### Prerequisites

- Python 3.12+
- A free [Supabase](https://supabase.com) account
- A free [GitHub](https://github.com) account
- *(Optional)* Telegram bot token via [@BotFather](https://t.me/BotFather)

### Local Setup

```bash
# 1. Clone
git clone https://github.com/Mojojojo0222/ai-price-predictor.git
cd ai-price-predictor

# 2. Virtual environment
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

# 3. Dependencies
pip install -r requirements.txt

# 4. Configure secrets
cp .env.example .env
# fill in SUPABASE_URL, SUPABASE_KEY, SUPABASE_SERVICE_KEY
```

### Database Setup

1. Create a project at [supabase.com](https://supabase.com)
2. Open **SQL Editor**
3. Paste the contents of [`supabase_schema.sql`](supabase_schema.sql) and run it
   — this creates all 4 tables, indexes, and Row-Level-Security policies
4. From **Settings → API**, copy:
   - `Project URL` → `SUPABASE_URL`
   - `anon public key` → `SUPABASE_KEY`
   - `service_role key` → `SUPABASE_SERVICE_KEY`

### 🏃 Running the App

```bash
streamlit run app.py
```

Open **http://localhost:8501** → sign up / log in → paste a product URL → get an instant AI verdict.

---

## 📁 Project Structure

```
ai-price-predictor/
├── app.py                  # Main Streamlit app (dashboard, add-product, charts, settings)
├── auth.py                 # Email + Google OAuth via Supabase Auth
├── database.py             # All CRUD operations (lazy Supabase client)
├── scraper.py              # Amazon/Flipkart scrapers, price parsing, UA rotation
├── predictor.py            # Feature engineering + RandomForest + Buy/Wait engine
├── alerts.py               # Telegram & Email alert dispatcher
├── scheduler.py            # APScheduler background price monitoring
├── charts.py               # Plotly visualizations + styled HTML components
├── config.py               # Centralised environment configuration
├── supabase_schema.sql     # Complete DB schema + RLS policies (1-click setup)
├── requirements.txt        # Pinned, tested dependency versions
├── .env.example            # Credentials template with setup instructions
└── .streamlit/
    └── config.toml         # Streamlit server + dark theme
```

---

## 🤖 The AI/ML Engine

### Feature Engineering

Each timestamp is transformed into a rich set of predictors:

```
day, month, day_of_week, day_of_year, week,
weekend (0/1),
festive_season  → Oct–Nov (Diwali/sale season)
new_year_sale   → Jan–Feb
great_sale      → Jul–Aug
```

### Model

```
RandomForestRegressor(
    n_estimators=100,
    max_depth=5,
    min_samples_leaf=2,
    random_state=42
)
```

The model is trained **per product** on its own `price_history` and forecasts the lowest predicted price over the next 30 days, including a confidence band.

### Decision Engine

| Condition | Verdict |
|-----------|---------|
| Predicted savings ≥ 10% within 21 days | 🟡 **WAIT** |
| Predicted savings ≥ 5% within 45 days | 🟡 **WAIT** |
| Current price ≤ predicted low | 🟢 **BUY NOW** |
| Expected savings < 3% | 🟢 **BUY NOW** |

Each verdict ships with a **confidence score** and **plain-English reasoning** so users understand *why*.

> ⚠️ *Predictions are probabilistic, not guarantees. Always sanity-check the live listing before paying.*

---

## 🔔 Alert System

| Trigger | Channel | Payload |
|---------|---------|---------|
| Price drop > 3% | 📧 Email / 📱 Telegram | old price → new price, drop % |
| Buy-now verdict | 📧 Email / 📱 Telegram | current price, predicted low, reasoning |
| Target price hit | 📱 Telegram | "Your target ₹X is reached" |
| New signup | 📧 Email | Welcome message + first steps |

---

## ☁️ Deployment (100% Free)

1. Push this repo to your GitHub account
2. Go to [share.streamlit.io](https://share.streamlit.io) → **New app**
3. Connect the repo and select `app.py`
4. Add your Supabase keys as **Streamlit Secrets**:

```toml
# .streamlit/secrets.toml (Streamlit Cloud dashboard)
SUPABASE_URL = "https://your-project.supabase.co"
SUPABASE_KEY = "your-anon-key"
SUPABASE_SERVICE_KEY = "your-service-role-key"
SCRAPERAPI_KEY = "optional"
TELEGRAM_BOT_TOKEN = "optional"
SMTP_EMAIL = "optional"
SMTP_PASSWORD = "optional"
APP_URL = "https://your-app.streamlit.app"
```

Deployment is automatic on every `git push` to `main`. ✨

---

## 🗺️ Roadmap

- [x] MVP — track, predict, alert, multi-user
- [ ] Google OAuth *proper* flow (PKCE redirect)
- [ ] Support more marketplaces (Myntra, Ajio, eBay)
- [ ] ARIMA / Prophet hybrid forecaster
- [ ] Seasonal-demand model using category aggregation
- [ ] Mobile push notifications (OneSignal)
- [ ] Price-drop leaderboard / community deals
- [ ] Dark/light theme toggle

---

## 🤝 Contributing

Contributions make the open-source community amazing. Any contribution is **greatly appreciated**.

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 📄 License

Distributed under the **MIT License**. See [`LICENSE`](LICENSE) for more information.

---

<div align="center">

**Built with ❤️ and zero budget — proof that great engineering doesn't need expensive infrastructure.**

</div>