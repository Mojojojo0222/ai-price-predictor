from datetime import datetime, timedelta

import pandas as pd

# scikit-learn imports
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.model_selection import train_test_split

from config import MIN_DATA_POINTS_FOR_PREDICTION, PREDICTION_DAYS_AHEAD


class PricePredictionEngine:
    """ML-based price prediction and buy/wait recommendation engine"""

    def __init__(self):
        self.model = None
        self.mae = 0.0
        self.r2 = 0.0
        self._trained = False

    def _extract_features(self, dates: pd.Series) -> pd.DataFrame:
        """Extract temporal features from dates"""
        features = pd.DataFrame()
        features["day"] = dates.dt.day
        features["month"] = dates.dt.month
        features["day_of_week"] = dates.dt.dayofweek
        features["day_of_year"] = dates.dt.dayofyear
        features["week"] = dates.dt.isocalendar().week.astype(int)
        features["weekend"] = (dates.dt.dayofweek >= 5).astype(int)

        # Festival/holiday season flags (Indian context)
        features["festive_season"] = features["month"].isin([10, 11]).astype(int)  # Diwali season
        features["new_year_sale"] = features["month"].isin([1, 2]).astype(int)  # January sales
        features["great_sale"] = features["month"].isin([7, 8]).astype(int)  # July/August sales

        return features

    def _prepare_data(self, price_history: list[dict]) -> pd.DataFrame | None:
        """Convert price history to training data"""
        if not price_history or len(price_history) < MIN_DATA_POINTS_FOR_PREDICTION:
            return None

        data = pd.DataFrame(price_history)
        data["scraped_at"] = pd.to_datetime(data["scraped_at"])
        data["price"] = pd.to_numeric(data["price"], errors="coerce")
        data = data.dropna(subset=["price"])

        if len(data) < MIN_DATA_POINTS_FOR_PREDICTION:
            return None

        data = data.sort_values("scraped_at").drop_duplicates(subset=["scraped_at"])
        return data

    def train(self, price_history: list[dict]) -> bool:
        """Train the prediction model on price history"""
        data = self._prepare_data(price_history)
        if data is None:
            return False

        features = self._extract_features(data["scraped_at"])
        x = features.values
        y = data["price"].values

        # Use RandomForest for better accuracy with small datasets
        self.model = RandomForestRegressor(n_estimators=100, max_depth=5, min_samples_leaf=2, random_state=42)

        if len(data) >= 10:
            try:
                x_train, x_test, y_train, y_test = train_test_split(x, y, test_size=0.2, random_state=42, shuffle=False)
                self.model.fit(x_train, y_train)
                y_pred = self.model.predict(x_test)
                self.mae = mean_absolute_error(y_test, y_pred)
                self.r2 = r2_score(y_test, y_pred)
            except Exception:
                # Not enough data for split, train on all
                self.model.fit(x, y)
        else:
            self.model.fit(x, y)

        self._trained = True
        return True

    def predict_price(self, target_date: datetime) -> tuple[float | None, float | None]:
        """Predict price for a target date. Returns (predicted_price, confidence_band)"""
        if not self._trained or self.model is None:
            return None, None

        date_df = pd.DataFrame({"date": [target_date]})
        date_df["date"] = pd.to_datetime(date_df["date"])
        features = self._extract_features(date_df["date"])
        x = features.values

        prediction = self.model.predict(x)[0]

        # Confidence band based on MAE
        band = max(self.mae * 1.5, prediction * 0.03)  # At least 3% band
        return float(prediction), float(band)

    def predict_trend(self, price_history: list[dict], days_ahead: int = None) -> list[dict]:
        """Predict prices for the next N days"""
        if days_ahead is None:
            days_ahead = PREDICTION_DAYS_AHEAD

        if not self._trained:
            return []

        if not price_history:
            return []

        last_date = pd.to_datetime(price_history[-1]["scraped_at"])
        predictions = []

        for i in range(1, days_ahead + 1):
            target_date = last_date + timedelta(days=i)
            price, band = self.predict_price(target_date)
            if price:
                predictions.append({"date": target_date, "predicted_price": price, "confidence_band": band})

        return predictions

    def predict_lowest(self, price_history: list[dict], days_ahead: int = None) -> dict:
        """Find the predicted lowest price in the next N days"""
        if days_ahead is None:
            days_ahead = PREDICTION_DAYS_AHEAD

        trends = self.predict_trend(price_history, days_ahead)
        if not trends:
            return {}

        lowest = min(trends, key=lambda x: x["predicted_price"])
        return {
            "predicted_low": lowest["predicted_price"],
            "predicted_low_date": lowest["date"],
            "confidence_band": lowest["confidence_band"],
            "trend": trends,
        }


def determine_recommendation(
    current_price: float,
    predicted_low: float,
    predicted_low_date: datetime,
    confidence: float,
    historical_low: float = None,
) -> tuple[str, str]:
    """Determine buy/wait recommendation with reasoning"""
    if current_price is None or predicted_low is None:
        return "NO_DATA", "Not enough data to make a prediction yet."

    now = datetime.now()
    days_until_low = (predicted_low_date - now).days if predicted_low_date else 0

    savings = current_price - predicted_low
    savings_percent = (savings / current_price) * 100 if current_price > 0 else 0

    # Rules-based recommendation logic
    if savings_percent >= 10 and days_until_low <= 21 and confidence >= 60:
        reasoning = (
            f"Predicted to drop to ₹{predicted_low:,.0f} in about {days_until_low} days "
            f"(₹{savings:,.0f} / {savings_percent:.0f}% savings). "
            f"Confidence: {confidence:.0f}%. This drop is close enough to wait for."
        )
        return "WAIT", reasoning
    elif savings_percent >= 5 and days_until_low <= 45 and confidence >= 60:
        reasoning = (
            f"Expected to drop by {savings_percent:.0f}% (to ₹{predicted_low:,.0f}) "
            f"within ~{days_until_low} days. If you don't need it urgently, consider waiting."
        )
        return "WAIT", reasoning
    elif current_price <= predicted_low:
        reasoning = (
            f"Current price ($₹{current_price:,.0f}) is at or below the predicted low "
            f"(₹{predicted_low:,.0f}). This is a good time to buy!"
        )
        return "BUY_NOW", reasoning
    elif savings_percent < 3:
        reasoning = (
            f"Expected savings ({savings_percent:.1f}%) is minimal. "
            f"Current price ₹{current_price:,.0f} is close to the predicted low ₹{predicted_low:,.0f}."
        )
        return "BUY_NOW", reasoning
    else:
        reasoning = (
            f"Predicted low of ₹{predicted_low:,.0f} is {days_until_low} days away. Consider waiting if you can."
        )
        return "WAIT", reasoning


def analyze_product(price_history: list[dict], product_name: str = None) -> dict:
    """Full analysis pipeline: train, predict, recommend"""
    engine = PricePredictionEngine()

    if not engine.train(price_history):
        return {
            "status": "NO_DATA",
            "message": "Not enough price data yet. Try again after a few days of tracking.",
            "current_price": price_history[-1]["price"] if price_history else None,
            "trained": False,
        }

    current_price = price_history[-1]["price"]
    prediction = engine.predict_lowest(price_history)

    # Compute confidence (1 - normalized MAE)
    if engine.r2 > 0:
        confidence = max(30, min(95, 100 * engine.r2))
    else:
        confidence = max(30, min(70, 100 * (1 - (engine.mae / current_price))))

    optimal_payload = determine_recommendation(
        current_price=current_price,
        predicted_low=prediction["predicted_low"],
        predicted_low_date=prediction["predicted_low_date"],
        confidence=confidence,
        historical_low=min([p["price"] for p in price_history]) if price_history else None,
    )

    recommendation, reasoning = optimal_payload

    return {
        "status": "ANALYZED",
        "trained": True,
        "current_price": current_price,
        "predicted_low": prediction["predicted_low"],
        "predicted_low_date": prediction["predicted_low_date"].isoformat(),
        "confidence": confidence,
        "recommendation": recommendation,
        "reasoning": reasoning,
        "trend": prediction["trend"],
        "model_metrics": {"mae": engine.mae, "r2": engine.r2},
        "product_name": product_name,
    }


def get_savings_estimate(analysis: dict) -> dict:
    """Calculate potential savings from the analysis"""
    if analysis.get("status") != "ANALYZED":
        return {"savings": 0, "savings_percent": 0, "message": "No data"}

    current = analysis["current_price"]
    predicted_low = analysis["predicted_low"]
    savings = current - predicted_low
    savings_percent = (savings / current) * 100 if current > 0 else 0

    return {
        "savings": savings,
        "savings_percent": savings_percent,
        "message": f"Potential savings: ₹{savings:,.0f} ({savings_percent:.1f}%)",
    }
