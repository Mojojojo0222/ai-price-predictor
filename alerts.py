import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import requests

from config import APP_NAME, APP_URL, SMTP_EMAIL, SMTP_PASSWORD, TELEGRAM_BOT_TOKEN

# ==================== TELEGRAM ====================


def send_telegram_message(chat_id: str, message: str) -> bool:
    """Send a message to a Telegram chat"""
    if not TELEGRAM_BOT_TOKEN or not chat_id:
        return False

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": chat_id, "text": message, "parse_mode": "HTML"}

    try:
        response = requests.post(url, json=payload, timeout=10)
        return response.status_code == 200
    except Exception:
        return False


def send_price_drop_alert_telegram(
    chat_id: str, product_name: str, old_price: float, new_price: float, drop_percent: float, product_url: str
) -> bool:
    """Send price drop alert via Telegram"""
    message = (
        f"🔔 <b>{APP_NAME} - Price Drop Alert!</b>\n\n"
        f"📦 {product_name}\n"
        f"💰 Price dropped: <b>₹{old_price:,.0f}</b> → <b>₹{new_price:,.0f}</b>\n"
        f"📉 Drop: -{drop_percent:.1f}%\n\n"
        f"🚀 This may be a good time to buy!\n"
        f"🔗 <a href='{product_url}'>View Product</a>"
    )
    return send_telegram_message(chat_id, message)


def send_buy_now_alert_telegram(
    chat_id: str, product_name: str, current_price: float, prediction: dict, product_url: str
) -> bool:
    """Send buy-now recommendation via Telegram"""
    message = (
        f"🟢 <b>{APP_NAME} - BUY NOW!</b>\n\n"
        f"📦 {product_name}\n"
        f"💰 Current price: <b>₹{current_price:,.0f}</b>\n"
        f"🎯 Predicted low: ₹{prediction.get('predicted_low', 0):,.0f}\n"
        f"📅 Predicted date: {prediction.get('predicted_low_date', 'Unknown')}\n\n"
        f"💡 {prediction.get('reasoning', '')}\n\n"
        f"🔗 <a href='{product_url}'>Buy Now</a>"
    )
    return send_telegram_message(chat_id, message)


def send_target_price_alert_telegram(
    chat_id: str, product_name: str, current_price: float, target_price: float, product_url: str
) -> bool:
    """Send target price reached alert via Telegram"""
    message = (
        f"🎯 <b>{APP_NAME} - Target Reached!</b>\n\n"
        f"📦 {product_name}\n"
        f"💰 Product is at <b>₹{current_price:,.0f}</b>\n"
        f"🎯 ≤ your target of ₹{target_price:,.0f}!\n\n"
        f"🏃 This is the price you were waiting for!\n"
        f"🔗 <a href='{product_url}'>Buy Now</a>"
    )
    return send_telegram_message(chat_id, message)


# ==================== EMAIL ====================


def send_email(to_email: str, subject: str, html_body: str, plain_body: str = None) -> bool:
    """Send email via Gmail SMTP"""
    if not SMTP_EMAIL or not SMTP_PASSWORD or not to_email:
        return False

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = SMTP_EMAIL
    msg["To"] = to_email

    text_part = MIMEText(plain_body or "Check your price tracker!", "plain")
    html_part = MIMEText(html_body, "html")
    msg.attach(text_part)
    msg.attach(html_part)

    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(SMTP_EMAIL, SMTP_PASSWORD)
            server.send_message(msg)
        return True
    except Exception:
        return False


def send_price_drop_alert_email(
    user_email: str, product_data: dict, old_price: float, new_price: float, drop_percent: float
) -> bool:
    """Send price drop alert via email"""
    subject = f"🔔 Price Drop Alert: {product_data['name']}"
    html = f"""
    <html>
    <body style="font-family: Arial, sans-serif; background: #f5f5f5; padding: 20px;">
        <div style="max-width: 500px; margin: auto; background: white; border-radius: 12px; padding: 24px;">
            <h2 style="color: #FF6B6B; margin-top: 0;">🔔 Price Drop Alert!</h2>
            <h3 style="color: #333; margin-bottom: 5px;">{product_data["name"]}</h3>
            <p style="color: #888; font-size: 14px;">Price dropped from <b>₹{old_price:,.0f}</b> to
               <b style="color: #2ECC71;">₹{new_price:,.0f}</b> (📉 {drop_percent:.1f}%)</p>
            <div style="background: #f0fff0; border: 1px solid #2ECC71; border-radius: 8px; padding: 12px; margin: 15px 0;">
                🚀 <b>This may be a good time to buy!</b>
            </div>
            <a href="{product_data.get("url", APP_URL)}"
               style="display: inline-block; background: #FF6B6B; color: white; padding: 12px 20px;
                      border-radius: 8px; text-decoration: none; font-weight: bold;">
                View Product →
            </a>
            <p style="color: #aaa; font-size: 12px; margin-top: 20px;">Sent via {APP_NAME}</p>
        </div>
    </body>
    </html>
    """
    return send_email(user_email, subject, html)


def send_buy_now_alert_email(user_email: str, product_data: dict, current_price: float, prediction: dict) -> bool:
    """Send buy-now recommendation via email"""
    subject = f"🟢 BUY NOW: {product_data['name']} at ₹{current_price:,.0f}"
    html = f"""
    <html>
    <body style="font-family: Arial, sans-serif; background: #f5f5f5; padding: 20px;">
        <div style="max-width: 500px; margin: auto; background: white; border-radius: 12px; padding: 24px;">
            <h2 style="color: #2ECC71; margin-top: 0;">🟢 Great Time to Buy!</h2>
            <h3 style="color: #333; margin-bottom: 5px;">{product_data["name"]}</h3>
            <p>Current price: <b style="font-size: 18px; color: #FF6B6B;">₹{current_price:,.0f}</b></p>
            <p>Predicted low: ₹{prediction.get("predicted_low", 0):,.0f} on {prediction.get("predicted_low_date", "unknown")}</p>
            <p style="color: #555;">💡 {prediction.get("reasoning", "")}</p>
            <a href="{product_data.get("url", APP_URL)}"
               style="display: inline-block; background: #2ECC71; color: white; padding: 12px 20px;
                      border-radius: 8px; text-decoration: none; font-weight: bold;">
                Buy Now →
            </a>
            <p style="color: #aaa; font-size: 12px; margin-top: 20px;">Sent via {APP_NAME}</p>
        </div>
    </body>
    </html>
    """
    return send_email(user_email, subject, html)


def send_welcome_email(user_email: str, user_name: str = "there") -> bool:
    """Send welcome email to new user"""
    subject = f"Welcome to {APP_NAME}! 🎉"
    html = f"""
    <html>
    <body style="font-family: Arial, sans-serif; background: #f5f5f5; padding: 20px;">
        <div style="max-width: 500px; margin: auto; background: white; border-radius: 12px; padding: 24px;">
            <h2 style="color: #FF6B6B; margin-top: 0;">Welcome to {APP_NAME}! 🎉</h2>
            <p>Hi {user_name},</p>
            <p>Start tracking products and we'll tell you the best time to buy.</p>
            <div style="background: #f0f7ff; border: 1px solid #3498DB; border-radius: 8px; padding: 12px; margin: 15px 0;">
                💡 <b>Tip:</b> Add a product and set a target price. We'll alert you when it drops!
            </div>
            <a href="{APP_URL}"
               style="display: inline-block; background: #FF6B6B; color: white; padding: 12px 20px;
                      border-radius: 8px; text-decoration: none; font-weight: bold;">
                Go to Dashboard →
            </a>
            <p style="color: #aaa; font-size: 12px; margin-top: 20px;">Sent via {APP_NAME}</p>
        </div>
    </body>
    </html>
    """
    return send_email(user_email, subject, html)


# ==================== DISPATCHER ====================


def dispatch_price_alert(
    user: dict,
    track: dict,
    product_data: dict,
    old_price: float,
    new_price: float,
    drop_percent: float,
    prediction: dict = None,
    target_reached: bool = False,
) -> list[str]:
    """Dispatch alerts through all enabled channels. Returns list of successful channels."""
    channels_sent = []
    user_email = user.get("email", "")
    telegram_chat_id = track.get("telegram_chat_id")

    if not track.get("alert_enabled", True):
        return channels_sent

    # Email alerts
    if track.get("alert_email", True) and user_email:
        if target_reached and prediction or prediction:
            ok = send_buy_now_alert_email(user_email, product_data, new_price, prediction)
        else:
            ok = send_price_drop_alert_email(user_email, product_data, old_price, new_price, drop_percent)
        if ok:
            channels_sent.append("email")

    # Telegram alerts
    if track.get("alert_telegram", False) and telegram_chat_id:
        if target_reached and prediction:
            ok = send_target_price_alert_telegram(
                telegram_chat_id,
                product_data["name"],
                new_price,
                track.get("target_price", 0),
                product_data.get("url", ""),
            )
        elif prediction:
            ok = send_buy_now_alert_telegram(
                telegram_chat_id, product_data["name"], new_price, prediction, product_data.get("url", "")
            )
        else:
            ok = send_price_drop_alert_telegram(
                telegram_chat_id, product_data["name"], old_price, new_price, drop_percent, product_data.get("url", "")
            )
        if ok:
            channels_sent.append("telegram")

    return channels_sent
