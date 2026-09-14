"""Tests for the ML prediction engine (predictor.py)."""

import random
from datetime import datetime, timedelta

from predictor import (
    PricePredictionEngine,
    analyze_product,
    determine_recommendation,
    get_savings_estimate,
)


def build_mock_history(days: int = 45, start_price: float = 80000.0, seed: int = 42) -> list:
    """Build a synthetic price history with a realistic pattern:
    15 days stable -> 10 days falling -> 10 days rising -> 10 days falling."""
    random.seed(seed)
    history = []
    price = start_price
    base = datetime.now() - timedelta(days=days)

    for i in range(days):
        if i < 15:
            price += random.uniform(-200, 300)
        elif i < 25:
            price -= random.uniform(500, 1500)
        elif i < 35:
            price += random.uniform(200, 800)
        else:
            price -= random.uniform(100, 600)

        history.append(
            {
                "scraped_at": (base + timedelta(days=i)).isoformat(),
                "price": round(price, 2),
            }
        )
    return history


# ==================== Feature extraction ====================


class TestFeatureExtraction:
    def test_features_shape_matches_rows(self):
        engine = PricePredictionEngine()
        history = build_mock_history(days=30)
        data = engine._prepare_data(history)
        assert data is not None
        features = engine._extract_features(data["scraped_at"])
        assert len(features) == len(data)

    def test_festive_season_flag(self):
        """October/November should be flagged as festive season."""
        engine = PricePredictionEngine()
        import pandas as pd

        dates = pd.Series(pd.to_datetime(["2026-11-05", "2026-05-05"]))
        features = engine._extract_features(dates)
        assert int(features["festive_season"].iloc[0]) == 1
        assert int(features["festive_season"].iloc[1]) == 0


# ==================== Training ====================


class TestTraining:
    def test_train_with_sufficient_data(self):
        engine = PricePredictionEngine()
        assert engine.train(build_mock_history(days=45)) is True
        assert engine._trained is True

    def test_train_with_insufficient_data(self):
        engine = PricePredictionEngine()
        # 3 data points < MIN_DATA_POINTS_FOR_PREDICTION
        assert engine.train(build_mock_history(days=3)) is False
        assert engine._trained is False

    def test_predict_future_price(self):
        engine = PricePredictionEngine()
        engine.train(build_mock_history(days=45))
        predicted, band = engine.predict_price(datetime.now() + timedelta(days=7))
        assert predicted is not None
        assert predicted > 0
        assert band is not None and band > 0

    def test_predict_lowest_returns_trend(self):
        engine = PricePredictionEngine()
        history = build_mock_history(days=45)
        engine.train(history)
        result = engine.predict_lowest(history, days_ahead=30)
        assert "predicted_low" in result
        assert "predicted_low_date" in result
        assert len(result["trend"]) > 0


# ==================== Recommendation logic ====================


class TestRecommendation:
    def test_buy_now_when_below_predicted_low(self):
        rec, _ = determine_recommendation(
            current_price=50000,
            predicted_low=55000,
            predicted_low_date=datetime.now() + timedelta(days=10),
            confidence=80,
        )
        assert rec == "BUY_NOW"

    def test_buy_now_when_savings_minimal(self):
        rec, _ = determine_recommendation(
            current_price=50000,
            predicted_low=49000,
            predicted_low_date=datetime.now() + timedelta(days=10),
            confidence=80,
        )
        assert rec == "BUY_NOW"

    def test_wait_when_big_drop_is_close(self):
        rec, _ = determine_recommendation(
            current_price=80000,
            predicted_low=64000,  # 20% savings
            predicted_low_date=datetime.now() + timedelta(days=7),
            confidence=75,
        )
        assert rec == "WAIT"

    def test_no_data_when_values_missing(self):
        rec, _ = determine_recommendation(None, None, None, 0)
        assert rec == "NO_DATA"


# ==================== End-to-end analysis ====================


class TestAnalysis:
    def test_analyze_product_success(self):
        analysis = analyze_product(
            build_mock_history(days=60),
            product_name="iPhone 15 Test",
        )
        assert analysis["status"] == "ANALYZED"
        assert analysis["recommendation"] in ("BUY_NOW", "WAIT")
        assert 0 <= analysis["confidence"] <= 100
        assert analysis["predicted_low"] > 0
        assert analysis["current_price"] > 0

    def test_analyze_product_insufficient_data(self):
        analysis = analyze_product(build_mock_history(days=3))
        assert analysis["status"] == "NO_DATA"

    def test_savings_estimate(self):
        analysis = analyze_product(build_mock_history(days=60))
        if analysis["status"] == "ANALYZED":
            savings = get_savings_estimate(analysis)
            # savings = current - predicted_low; may be negative if predicted_low > current
            assert isinstance(savings["savings"], float)
            assert isinstance(savings["savings_percent"], float)
        # Should not crash even without analysis
        assert get_savings_estimate({"status": "NO_DATA"})["savings"] == 0
