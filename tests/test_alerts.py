"""Tests for the alert system (alerts.py).

Network calls (Telegram/SMTP) are never executed in tests; we
verify message construction and the dispatcher's channel gating logic.
"""

from unittest.mock import MagicMock, patch

import alerts
from alerts import (
    dispatch_price_alert,
    send_buy_now_alert_telegram,
    send_price_drop_alert_telegram,
)


class TestTelegramMessages:
    @patch("alerts.requests.post")
    @patch("alerts.TELEGRAM_BOT_TOKEN", "fake-token-for-testing")
    def test_price_drop_message_format(self, mock_post):
        mock_post.return_value = MagicMock(status_code=200)
        ok = send_price_drop_alert_telegram(
            chat_id="12345",
            product_name="iPhone 15",
            old_price=80000,
            new_price=70000,
            drop_percent=12.5,
            product_url="https://example.com",
        )
        assert ok is True
        # Verify the payload reached Telegram
        payload = mock_post.call_args.kwargs["json"]
        assert "iPhone 15" in payload["text"]
        assert "12.5" in payload["text"]
        assert payload["chat_id"] == "12345"

    @patch("alerts.requests.post")
    @patch("alerts.TELEGRAM_BOT_TOKEN", "fake-token-for-testing")
    def test_buy_now_message(self, mock_post):
        mock_post.return_value = MagicMock(status_code=200)
        ok = send_buy_now_alert_telegram(
            chat_id="12345",
            product_name="Sony Headphones",
            current_price=20000,
            prediction={"predicted_low": 17000, "predicted_low_date": "2026-12-01", "reasoning": "Seasonal low"},
            product_url="https://example.com",
        )
        assert ok is True
        payload = mock_post.call_args.kwargs["json"]
        assert "Sony Headphones" in payload["text"]
        assert "20,000" in payload["text"]  # formatted as ₹20,000

    @patch("alerts.requests.post")
    def test_telegram_failure_returns_false(self, mock_post):
        mock_post.side_effect = Exception("network error")
        ok = send_price_drop_alert_telegram("123", "P", 100, 90, 10, "url")
        assert ok is False

    def test_no_token_no_call(self):
        """Empty bot token must short-circuit without any HTTP call."""
        with patch.object(alerts, "TELEGRAM_BOT_TOKEN", ""), patch("alerts.requests.post") as mock_post:
            ok = alerts.send_telegram_message(chat_id="12345", message="test")
            assert ok is False
            mock_post.assert_not_called()

    def test_missing_chat_id_no_call(self):
        with patch("alerts.requests.post") as mock_post:
            ok = alerts.send_telegram_message(chat_id=None, message="test")
            assert ok is False
            mock_post.assert_not_called()


# ==================== Dispatcher ====================


class TestDispatch:
    USER = {"email": "test@example.com"}
    TRACK = {
        "alert_enabled": True,
        "alert_email": True,
        "alert_telegram": False,
        "telegram_chat_id": None,
        "target_price": None,
    }
    PRODUCT = {"name": "Test Product", "url": "https://example.com"}

    @patch("alerts.send_buy_now_alert_email")
    @patch("alerts.send_price_drop_alert_email")
    def test_email_channel_when_drop_but_no_prediction(self, mock_drop, mock_buy):
        mock_drop.return_value = True
        mock_buy.return_value = True
        channels = dispatch_price_alert(
            user=self.USER,
            track=self.TRACK,
            product_data=self.PRODUCT,
            old_price=100,
            new_price=90,
            drop_percent=10,
            prediction=None,
            target_reached=False,
        )
        assert "email" in channels
        mock_drop.assert_called_once()

    def test_all_channels_disabled(self):
        track = {**self.TRACK, "alert_email": False, "alert_telegram": False}
        with patch("alerts.send_price_drop_alert_email") as email, patch("alerts.send_price_drop_alert_telegram") as tg:
            channels = dispatch_price_alert(
                user=self.USER,
                track=track,
                product_data=self.PRODUCT,
                old_price=100,
                new_price=90,
                drop_percent=10,
                prediction=None,
                target_reached=False,
            )
            assert channels == []
            email.assert_not_called()
            tg.assert_not_called()

    def test_alert_disabled_skips_all(self):
        track = {**self.TRACK, "alert_enabled": False, "alert_email": True}
        with patch("alerts.send_price_drop_alert_email") as email:
            channels = dispatch_price_alert(
                user=self.USER,
                track=track,
                product_data=self.PRODUCT,
                old_price=100,
                new_price=90,
                drop_percent=10,
                prediction=None,
                target_reached=False,
            )
            assert channels == []
            email.assert_not_called()
