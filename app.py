import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from typing import Optional, Dict, List

# Internal modules
from auth import init_session_state, require_auth, sign_out, get_current_user
from database import (
    create_product,
    get_product_by_url,
    track_product,
    get_user_tracks,
    add_price_history,
    get_price_history,
    get_latest_price,
    get_prediction,
    remove_user_track,
    get_user_stats,
    update_user_track
)
from scraper import scrape_product, detect_source
from predictor import analyze_product, get_savings_estimate
from charts import (
    create_price_chart,
    create_savings_gauge,
    create_recommendation_card,
    create_product_card,
    create_savings_summary_chart
)
from scheduler import start_scheduler, get_scheduler_status
import config

# ==================== PAGE CONFIG ====================

st.set_page_config(
    page_title="AI Price Predictor",
    page_icon="🔮",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==================== CUSTOM CSS ====================

CUSTOM_CSS = """
<style>
/* Global */
.stApp {
    background: #0E1117;
}
.block-container {
    padding-top: 2rem;
    padding-bottom: 3rem;
    max-width: 1200px;
}

/* Headers */
h1, h2, h3 {
    color: #FFFFFF !important;
    font-weight: 600 !important;
}

/* Sidebar */
[data-testid="stSidebar"] {
    background: #151820;
    border-right: 1px solid #2A2D3E;
}
[data-testid="stSidebar"] h1 {
    font-size: 1.2rem;
    padding-bottom: 1rem;
    border-bottom: 1px solid #2A2D3E;
}

/* Buttons */
.stButton > button {
    border-radius: 8px;
    font-weight: 600;
    transition: all 0.2s;
}
.stButton > button:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(255,107,107,0.2);
}

/* Inputs */
.stTextInput > div > div > input {
    border-radius: 8px;
    border: 1px solid #2A2D3E;
    background: #1E2130;
    color: #FFFFFF;
}
.stNumberInput > div > div > input {
    border-radius: 8px;
    border: 1px solid #2A2D3E;
    background: #1E2130;
    color: #FFFFFF;
}

/* Tabs */
.stTabs [data-baseweb="tab-list"] {
    gap: 8px;
}
.stTabs [data-baseweb="tab"] {
    border-radius: 8px;
    padding: 6px 16px;
    background: #1E2130;
}

/* Metrics */
[data-testid="stMetric"] {
    background: #1E2130;
    border-radius: 12px;
    padding: 16px;
    border: 1px solid #2A2D3E;
}
[data-testid="stMetric"] label {
    color: #888888;
}
[data-testid="stMetricValue"] {
    color: #FFFFFF;
    font-size: 1.6rem;
    font-weight: 700;
}

/* Expander */
[data-testid="stExpander"] {
    background: #1E2130;
    border-radius: 12px;
    border: 1px solid #2A2D3E;
}

/* Custom classes */
.buy-now { color: #2ECC71 !important; }
.wait { color: #F39C12 !important; }

@keyframes pulse {
    0% { transform: scale(1); }
    50% { transform: scale(1.05); }
    100% { transform: scale(1); }
}
.buy-now-pulse {
    animation: pulse 2s infinite;
    display: inline-block;
}
</style>
"""

st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# ==================== UTILITY FUNCTIONS ====================

def format_price(price: float) -> str:
    """Format price with Indian rupee symbol"""
    return f"₹{price:,.0f}"


def get_rec_emoji(rec: str) -> str:
    if rec == "BUY_NOW":
        return "🟢"
    elif rec == "WAIT":
        return "🟡"
    return "⚪"


def get_rec_color(rec: str) -> str:
    if rec == "BUY_NOW":
        return "#2ECC71"
    elif rec == "WAIT":
        return "#F39C12"
    return "#888888"


def safe_date(value) -> datetime:
    """Convert various date formats to datetime"""
    if value is None:
        return datetime.now()
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except Exception:
        return datetime.now()


# ==================== PAGE RENDERERS ====================

def render_header():
    """Render header with app title and user info"""
    col1, col2 = st.columns([4, 1])
    with col1:
        st.markdown(
            '<h1 style="font-size: 2.2rem;">🔮 AI Price Predictor</h1>',
            unsafe_allow_html=True
        )
        st.markdown(
            '<p style="color: #888888; margin-top: -15px;">'
            'The smartest way to know <b>when to buy</b>.</p>',
            unsafe_allow_html=True
        )
    with col2:
        user = get_current_user()
        if user:
            email = user.get("email", "")
            st.markdown(
                f'<p style="text-align: right; color: #888888;">'
                f'👤 {email}<br><small>Last check: {datetime.now().strftime("%H:%M")}</small></p>',
                unsafe_allow_html=True
            )


def render_dashboard():
    """Render the main dashboard showing user's tracked products"""
    st.markdown("## 📊 Your Dashboard")
    user = get_current_user()
    if not user:
        return

    # Get user's tracked products
    tracks = get_user_tracks(user["id"])
    stats = get_user_stats(user["id"])

    # Show stats row
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("📦 Tracked Products", stats["total_tracked"])
    with col2:
        st.metric("🟢 Buy Now", stats["buy_now_count"])
    with col3:
        st.metric("🟡 Waiting", stats["wait_count"])

    st.markdown("---")

    if not tracks:
        st.markdown(
            """
            <div style="background:#1E2130; border:1px dashed #2A2D3E; border-radius:12px; padding:40px; text-align:center; margin-top:20px;">
                <div style="font-size:48px;">📭</div>
                <h3 style="color:#FFFFFF;">No products tracked yet</h3>
                <p style="color:#888888;">Add a product URL to start predicting the best time to buy!</p>
                <div style="margin-top:20px;">
                    <a href="#" style="background:#FF6B6B; color:white; padding:12px 24px; border-radius:8px; text-decoration:none; font-weight:600;">
                        ← Add Your First Product
                    </a>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )
    else:
        # Process each tracked product
        for track in tracks:
            product = track.get("products")
            if not product:
                continue

            # Get latest prediction
            prediction = get_prediction(product["id"])
            latest = get_latest_price(product["id"])
            current_price = latest["price"] if latest else None

            analysis = None
            if prediction:
                analysis = {
                    "status": "ANALYZED",
                    "current_price": current_price or prediction.get("current_price"),
                    "predicted_low": prediction.get("predicted_low"),
                    "predicted_low_date": prediction.get("predicted_date"),
                    "confidence": prediction.get("confidence", 0),
                    "recommendation": prediction.get("recommendation", "NO_DATA"),
                    "reasoning": prediction.get("reasoning", "")
                }

            # Render product card
            card_html = create_product_card({
                "name": product.get("name", "Product"),
                "url": product.get("url", ""),
                "image_url": product.get("image_url", "")
            }, analysis)

            st.markdown(card_html, unsafe_allow_html=True)

            # Product actions
            col1, col2, col3, col4 = st.columns([1, 1, 1, 4])
            with col1:
                if st.button("📈 View", key=f"view_{product['id']}", use_container_width=True):
                    st.session_state["selected_product_id"] = product["id"]
                    st.session_state["current_page"] = "📈 Product Details"
                    st.rerun()
            with col2:
                alert_status = "🔕" if track.get("alert_enabled") == False else "🔔"
                if st.button(f"{alert_status} Alerts", key=f"alert_{product['id']}", use_container_width=True):
                    new_status = not (track.get("alert_enabled", True))
                    update_user_track(track["id"], alert_enabled=new_status)
                    st.rerun()
            with col3:
                if st.button("🗑️ Remove", key=f"remove_{product['id']}", use_container_width=True):
                    remove_user_track(user["id"], product["id"])
                    st.rerun()
            with col4:
                if latest:
                    st.markdown(
                        f'<p style="text-align:right; color:#888888; font-size:12px;">'
                        f'Updated: {safe_date(latest["scraped_at"]).strftime("%b %d, %Y %H:%M")}</p>',
                        unsafe_allow_html=True
                    )


def render_add_product():
    """Render the add product page"""
    st.markdown("## ➕ Track a New Product")
    user = get_current_user()
    if not user:
        return

    st.markdown(
        '<p style="color:#888888;">Paste an <b>Amazon.in</b> or <b>Flipkart</b> product URL below.</p>',
        unsafe_allow_html=True
    )

    with st.form("add_product_form"):
        url = st.text_input(
            "🔗 Product URL",
            placeholder="https://www.amazon.in/dp/B0CHX3QCBS or https://www.flipkart.com/..."
        )
        target_price = st.number_input(
            "🎯 Target Price (optional)",
            min_value=1.0, max_value=10000000.0,
            step=1000.0,
            placeholder="Enter your target price"
        )
        alert_email_default = True
        col1, col2 = st.columns(2)
        with col1:
            email_alert = st.checkbox("📧 Email alerts", value=alert_email_default)
        with col2:
            telegram_alert = st.checkbox("📱 Telegram alerts", value=False)

        submitted = st.form_submit_button("🚀 Track This Product", type="primary", use_container_width=True)

    if submitted:
        if not url or not url.startswith("http"):
            st.error("Please enter a valid URL (starting with http:// or https://)")
            return

        source = detect_source(url)
        if source not in ["amazon", "flipkart"]:
            st.warning("⚠️ Only Amazon.in and Flipkart URLs are currently supported.")
            return

        with st.spinner("🔍 Fetching product info..."):
            result = scrape_product(url)

        if not result["success"]:
            st.warning(
                f"⚠️ {result.get('error', 'Could not scrape the product.')}\n\n"
                f"Available sources: Amazon.in, Flipkart"
            )
            st.info("💡 Tip: Try copying the URL directly from the product page.")
            return

        # Check if product already exists
        existing_product = get_product_by_url(url)
        if existing_product:
            product_id = existing_product["id"]
            st.info("✅ Product already exists in our database!")
        else:
            # Create new product
            product = create_product(
                url=url,
                name=result["name"],
                image_url=result.get("image_url"),
                category=result.get("source")
            )
            if not product:
                st.error("Failed to save product. Please try again.")
                return
            product_id = product["id"]

            # Add initial price
            add_price_history(
                product_id=product_id,
                price=result["price"],
                source=result.get("source")
            )
            st.success(f"✅ Product added! First price recorded: **{format_price(result['price'])}**")

        # Track product for user
        st.session_state["pending_track_target"] = target_price if target_price else None
        track_product(
            user_id=user["id"],
            product_id=product_id,
            target_price=target_price if target_price else None,
            alert_enabled=True,
            alert_email=email_alert,
            alert_telegram=telegram_alert,
            telegram_chat_id=st.session_state.get("telegram_chat_id")
        )

        st.success("🎉 Product added to your tracking list!")
        st.balloons()

        # Auto-analyze and show result
        history = get_price_history(product_id, days=365)
        with st.spinner("🧠 Running AI analysis..."):
            analysis = analyze_product(history, result["name"])

        if analysis.get("status") == "ANALYZED":
            st.markdown("### 🧠 AI Analysis")
            st.markdown(
                create_recommendation_card(
                    analysis["recommendation"],
                    analysis["confidence"]
                ),
                unsafe_allow_html=True
            )
            st.markdown(f"💡 {analysis.get('reasoning', '')}")

            # Show price chart
            fig = create_price_chart(
                history,
                predictions=analysis.get("trend", []),
                product_name=result["name"]
            )
            st.plotly_chart(fig, use_container_width=True)

            # Show prediction info
            col1, col2 = st.columns(2)
            with col1:
                st.markdown(
                    f'<div style="background:#1E2130; border-radius:12px; padding:16px; border:1px solid #2A2D3E;">'
                    f'<b style="color:#FFFFFF;">🎯 Predicted Low</b><br><br>'
                    f'<span style="font-size:24px; font-weight:700; color:#2ECC71;">{format_price(analysis["predicted_low"])}</span>'
                    f'</div>',
                    unsafe_allow_html=True
                )
            with col2:
                st.markdown(
                    f'<div style="background:#1E2130; border-radius:12px; padding:16px; border:1px solid #2A2D3E;">'
                    f'<b style="color:#FFFFFF;">📅 Predicted Date</b><br><br>'
                    f'<span style="font-size:18px; color:#FFFFFF;">{safe_date(analysis.get("predicted_low_date")).strftime("%B %d, %Y")}</span>'
                    f'</div>',
                    unsafe_allow_html=True
                )

            # Save prediction to DB
            from database import save_prediction
            save_prediction(
                product_id=product_id,
                predicted_low=analysis["predicted_low"],
                current_price=analysis["current_price"],
                confidence=analysis["confidence"],
                recommendation=analysis["recommendation"],
                predicted_date=analysis.get("predicted_low_date"),
                reasoning=analysis.get("reasoning", "")
            )


def render_product_details():
    """Render detailed product view with charts"""
    user = get_current_user()
    if not user:
        return

    # Get selected product
    product_id = st.session_state.get("selected_product_id")

    if not product_id:
        st.info("Select a product from your dashboard to see details.")
        return

    from database import get_product_by_id
    product = get_product_by_id(product_id)
    if not product:
        st.error("Product not found.")
        return

    # Back button
    if st.button("← Back to Dashboard"):
        st.session_state["selected_product_id"] = None
        st.session_state["current_page"] = "📊 Dashboard"
        st.rerun()

    st.markdown(f"## 📈 {product.get('name', 'Product')}")

    # Product info row
    col1, col2 = st.columns([3, 1])
    with col1:
        if product.get("image_url"):
            try:
                st.image(product["image_url"], width=120)
            except Exception:
                pass
        source_label = "Amazon" if detect_source(product["url"]) == "amazon" else "Flipkart"
        st.markdown(
            f'<a href="{product["url"]}" target="_blank" '
            f'style="color:#3498DB; text-decoration:none;">🔗 View on {source_label} →</a>',
            unsafe_allow_html=True
        )
    with col2:
        # Latest price summary
        latest = get_latest_price(product_id)
        if latest:
            st.metric("💰 Current Price", format_price(latest["price"]))

    # Fetch data
    history = get_price_history(product_id, days=365)
    prediction = get_prediction(product_id)

    if not history:
        st.info("No price data yet. Check back after the first scheduled update.")
        return

    # Analyze
    with st.spinner("🧠 Analyzing price patterns..."):
        analysis = analyze_product(history, product.get("name"))

    if analysis.get("status") == "ANALYZED":
        # Recommendation card
        st.markdown(
            create_recommendation_card(analysis["recommendation"], analysis["confidence"]),
            unsafe_allow_html=True
        )
        st.markdown(f"💡 **Reasoning:** {analysis.get('reasoning', '')}")

        # Price chart with predictions
        st.markdown("### 📉 Price History & Prediction")
        fig = create_price_chart(history, analysis.get("trend", []), product.get("name", "Product"))
        st.plotly_chart(fig, use_container_width=True)

        # Stats columns
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("🎯 Current", format_price(analysis["current_price"]))
        with col2:
            st.metric("📉 Predicted Low", format_price(analysis["predicted_low"]),
                      delta=f"-{format_price(analysis['current_price'] - analysis['predicted_low'])}")
        with col3:
            savings = get_savings_estimate(analysis)
            st.metric("💸 Potential Savings", format_price(savings["savings"]),
                      delta=f"{savings['savings_percent']:.1f}%")
        with col4:
            st.metric("🎯 Best Buy Date",
                      safe_date(analysis.get("predicted_low_date")).strftime("%b %d"))

    else:
        st.info(analysis.get("message", "Not enough data yet."))

    # Expanded data table
    with st.expander("📋 Full Price History"):
        df = pd.DataFrame(history)
        if not df.empty:
            df["scraped_at"] = pd.to_datetime(df["scraped_at"])
            df = df[["scraped_at", "price", "source"]].copy()
            df.columns = ["Date", "Price (₹)", "Source"]
            df["Date"] = df["Date"].dt.strftime("%Y-%m-%d %H:%M")
            df["Price (₹)"] = df["Price (₹)"].astype(float).round(2)
            st.dataframe(df.sort_values("Date", ascending=False), use_container_width=True)


def render_alerts_settings():
    """Render alert settings page"""
    st.markdown("## ⚙️ Alert Settings")
    user = get_current_user()
    if not user:
        return

    # Telegram setup
    st.markdown("### 📱 Get Telegram Alerts")
    st.markdown(
        '<p style="color:#888888;">Get instant alerts on your phone when prices drop. '
        'Setup once and never miss a deal!</p>',
        unsafe_allow_html=True
    )

    col1, col2 = st.columns([2, 1])
    with col1:
        telegram_id = st.text_input(
            "Telegram Chat ID",
            placeholder="e.g. 123456789 (get it from @userinfobot on Telegram)",
            value=st.session_state.get("telegram_chat_id", "")
        )
    with col2:
        st.markdown("")
        if st.button("💾 Save Telegram ID", use_container_width=True):
            st.session_state["telegram_chat_id"] = telegram_id
            st.success("✅ Telegram ID saved! Enable it for individual products.")

    st.markdown("### 📧 Email Alerts")
    email = user.get("email", "")
    st.info(f"Email alerts will be sent to: {email}")

    # How it works
    st.markdown("---")
    st.markdown("### 🤔 How Does It Work?")
    st.markdown(
        """
        <div style="background:#1E2130; border:1px solid #2A2D3E; border-radius:12px; padding:20px; margin-top:10px;">
        <ol style="color:#AAAAAA; font-size:15px; line-height:2;">
            <li><b style="color:#FFFFFF;">Track</b> — Add Amazon/Flipkart product URLs to your dashboard</li>
            <li><b style="color:#FFFFFF;">Monitor</b> — We check prices every 6 hours</li>
            <li><b style="color:#FFFFFF;">Analyze</b> — AI finds patterns and predicts future price drops</li>
            <li><b style="color:#FFFFFF;">Alert</b> — Get notified when it's time to buy</li>
        </ol>
        </div>
        """,
        unsafe_allow_html=True
    )

    # Frequency info
    st.markdown("---")
    col1, col2 = st.columns(2)
    with col1:
        st.info("🔄 **Price checks:** Every 6 hours")
    with col2:
        sos_status = get_scheduler_status()
        status_text = "🟢 Running" if sos_status["running"] else "🔴 Not running"
        st.info(f"⚡ **Scheduler:** {status_text}")


def render_sidebar():
    """Render the sidebar with navigation"""
    with st.sidebar:
        st.markdown(
            '<h1 style="padding-bottom:1rem; border-bottom:1px solid #2A2D3E;">🔮 <span style="font-size:0.8em;">AI Price Predictor</span></h1>',
            unsafe_allow_html=True
        )

        # Navigation options
        options = ["📊 Dashboard", "➕ Add Product"]
        if st.session_state.get("selected_product_id"):
            options.append("📈 Product Details")
        options.append("⚙️ Alert Settings")
        options.append("ℹ️ About")

        current_page = st.session_state.get("current_page", "📊 Dashboard")

        # Find default index
        default_idx = 0
        if current_page in options:
            default_idx = options.index(current_page)

        selected = st.radio(
            "Navigation",
            options,
            label_visibility="collapsed",
            index=default_idx
        )
        st.session_state["current_page"] = selected

        st.markdown("---")

        user = get_current_user()
        if user:
            st.markdown(f"👤 **{user.get('email', 'User')}**")

            # Show quick stats in sidebar
            stats = get_user_stats(user["id"])
            col1, col2 = st.columns(2)
            with col1:
                st.markdown(
                    f'<div style="background:#1E2130; border-radius:8px; padding:8px; text-align:center;">'
                    f'<span style="font-size:20px; font-weight:700; color:#FFFFFF;">{stats["total_tracked"]}</span><br>'
                    f'<span style="font-size:11px; color:#888;">TRACKED</span></div>',
                    unsafe_allow_html=True
                )
            with col2:
                st.markdown(
                    f'<div style="background:#1E2130; border-radius:8px; padding:8px; text-align:center;">'
                    f'<span style="font-size:20px; font-weight:700; color:#2ECC71;">{stats["buy_now_count"]}</span><br>'
                    f'<span style="font-size:11px; color:#888;">BUY NOW</span></div>',
                    unsafe_allow_html=True
                )

            st.markdown("")
            if st.button("🚪 Logout", use_container_width=True):
                sign_out()
                st.rerun()
        else:
            st.markdown("Not logged in")


def render_about():
    """Render the about page"""
    st.markdown("## ℹ️ About AI Price Predictor")

    st.markdown(
        """
        <div style="background:#1E2130; border:1px solid #2A2D3E; border-radius:12px; padding:24px; margin-top:10px;">
        <h3 style="color:#FFFFFF;">🔮 The smartest way to buy online</h3>
        <p style="color:#AAAAAA; line-height:1.8;">
        <b>AI Price Predictor</b> tracks product prices and uses machine learning to predict
        the best time to buy. No more waiting forever or buying too early!
        </p>

        <h3 style="color:#FFFFFF;">✨ Features</h3>
        <ul style="color:#AAAAAA; line-height:2;">
            <li>📊 Track unlimited products from Amazon & Flipkart</li>
            <li>🧠 AI predicts future price drops with confidence scores</li>
            <li>🔔 Real-time alerts when prices drop or hit your target</li>
            <li>📈 Interactive price history charts</li>
            <li>👤 Personalized dashboard for every user</li>
        </ul>

        <h3 style="color:#FFFFFF;">🔧 Technology</h3>
        <p style="color:#AAAAAA;">
        Python • Streamlit • Supabase • scikit-learn • Plotly • APScheduler
        </p>

        <h3 style="color:#FFFFFF;">📌 Disclaimer</h3>
        <p style="color:#888888; font-size:13px;">
        Predictions are based on historical price patterns and are not guaranteed.
        Prices shown may not reflect the exact current price on the retailer's website.
        Always verify before purchasing.
        </p>
        </div>
        """,
        unsafe_allow_html=True
    )

    st.markdown("---")
    st.markdown(
        '<p style="text-align:center; color:#666666; font-size:12px;">'
        'Made with ❤️ using Streamlit • Free forever</p>',
        unsafe_allow_html=True
    )


# ==================== MAIN APP ====================

def main():
    """Main application entry point"""
    # Initialize session state
    init_session_state()

    # Start background scheduler (best effort)
    start_scheduler()

    # Check auth
    if not require_auth():
        return

    # Render sidebar
    render_sidebar()

    # Update selected page after navigation
    current_page = st.session_state.get("current_page", "📊 Dashboard")

    if "📊 Dashboard" in current_page:
        render_header()
        render_dashboard()
    elif "➕ Add" in current_page:
        render_header()
        render_add_product()
    elif "📈 Product Detail" in current_page:
        render_product_details()
    elif "⚙️" in current_page:
        render_header()
        render_alerts_settings()
    elif "ℹ️" in current_page:
        render_header()
        render_about()
    else:
        render_header()
        render_dashboard()


if __name__ == "__main__":
    main()