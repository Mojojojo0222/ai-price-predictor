from supabase import create_client, Client
from config import SUPABASE_URL, SUPABASE_KEY
from datetime import datetime, timedelta
from typing import Optional, List, Dict
import json

# Lazy Supabase client initialization (so app works before real credentials)
_client: Optional[Client] = None


def get_client() -> Client:
    """Lazily create and return the Supabase client"""
    global _client
    if _client is None:
        _client = create_client(SUPABASE_URL, SUPABASE_KEY)
    return _client


def get_supabase() -> Client:
    """Alias for get_client() to keep existing function bodies unchanged"""
    return get_client()


# ==================== PRODUCTS ====================

def create_product(url: str, name: str, image_url: str = None, category: str = None) -> Dict:
    """Create a new product record"""
    data = {
        "url": url,
        "name": name,
        "image_url": image_url,
        "category": category
    }
    result = get_supabase().table("products").insert(data).execute()
    return result.data[0] if result.data else None


def get_product_by_url(url: str) -> Optional[Dict]:
    """Get product by URL"""
    result = get_supabase().table("products").select("*").eq("url", url).execute()
    return result.data[0] if result.data else None


def get_product_by_id(product_id: str) -> Optional[Dict]:
    """Get product by ID"""
    result = get_supabase().table("products").select("*").eq("id", product_id).execute()
    return result.data[0] if result.data else None


def search_products(query: str) -> List[Dict]:
    """Search products by name"""
    result = get_supabase().table("products").select("*").ilike("name", f"%{query}%").execute()
    return result.data if result.data else []


# ==================== PRICE HISTORY ====================

def add_price_history(product_id: str, price: float, currency: str = "INR", source: str = None) -> Dict:
    """Add a price record"""
    data = {
        "product_id": product_id,
        "price": price,
        "currency": currency,
        "source": source
    }
    result = get_supabase().table("price_history").insert(data).execute()
    return result.data[0] if result.data else None


def get_price_history(product_id: str, days: int = 90) -> List[Dict]:
    """Get price history for a product"""
    cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()
    result = get_supabase().table("price_history") \
        .select("*") \
        .eq("product_id", product_id) \
        .gte("scraped_at", cutoff_date) \
        .order("scraped_at", ascending=True) \
        .execute()
    return result.data if result.data else []


def get_latest_price(product_id: str) -> Optional[Dict]:
    """Get the most recent price for a product"""
    result = get_supabase().table("price_history") \
        .select("*") \
        .eq("product_id", product_id) \
        .order("scraped_at", ascending=False) \
        .limit(1) \
        .execute()
    return result.data[0] if result.data else None


def get_lowest_price(product_id: str) -> Optional[Dict]:
    """Get the lowest price ever recorded"""
    result = get_supabase().table("price_history") \
        .select("*") \
        .eq("product_id", product_id) \
        .order("price", ascending=True) \
        .limit(1) \
        .execute()
    return result.data[0] if result.data else None


# ==================== USER TRACKS ====================

def track_product(user_id: str, product_id: str, target_price: float = None,
                  alert_enabled: bool = True, alert_email: bool = True,
                  alert_telegram: bool = False, telegram_chat_id: str = None) -> Dict:
    """Track a product for a user"""
    data = {
        "user_id": user_id,
        "product_id": product_id,
        "target_price": target_price,
        "alert_enabled": alert_enabled,
        "alert_email": alert_email,
        "alert_telegram": alert_telegram,
        "telegram_chat_id": telegram_chat_id
    }
    result = get_supabase().table("user_tracks").insert(data).execute()
    return result.data[0] if result.data else None


def get_user_tracks(user_id: str) -> List[Dict]:
    """Get all products tracked by a user"""
    result = get_supabase().table("user_tracks") \
        .select("*, products(*)") \
        .eq("user_id", user_id) \
        .order("created_at", ascending=False) \
        .execute()
    return result.data if result.data else []


def get_user_track(user_id: str, product_id: str) -> Optional[Dict]:
    """Get a specific user track"""
    result = get_supabase().table("user_tracks") \
        .select("*") \
        .eq("user_id", user_id) \
        .eq("product_id", product_id) \
        .execute()
    return result.data[0] if result.data else None


def update_user_track(track_id: str, **kwargs) -> Dict:
    """Update user track settings"""
    result = get_supabase().table("user_tracks") \
        .update(kwargs) \
        .eq("id", track_id) \
        .execute()
    return result.data[0] if result.data else None


def remove_user_track(user_id: str, product_id: str) -> bool:
    """Remove a product from user's tracking list"""
    result = get_supabase().table("user_tracks") \
        .delete() \
        .eq("user_id", user_id) \
        .eq("product_id", product_id) \
        .execute()
    return True


def get_all_tracked_products() -> List[Dict]:
    """Get all tracked products (for scheduler)"""
    result = get_supabase().table("user_tracks") \
        .select("*, products(*)") \
        .eq("alert_enabled", True) \
        .execute()
    return result.data if result.data else []


# ==================== PREDICTIONS ====================

def save_prediction(product_id: str, predicted_low: float, current_price: float,
                    confidence: float, recommendation: str, predicted_date: str,
                    reasoning: str = None) -> Dict:
    """Save or update prediction for a product"""
    # Check if prediction exists
    existing = get_supabase().table("predictions") \
        .select("id") \
        .eq("product_id", product_id) \
        .execute()

    data = {
        "product_id": product_id,
        "predicted_low": predicted_low,
        "current_price": current_price,
        "confidence": confidence,
        "recommendation": recommendation,
        "predicted_date": predicted_date,
        "reasoning": reasoning
    }

    if existing.data:
        # Update existing
        result = get_supabase().table("predictions") \
            .update(data) \
            .eq("product_id", product_id) \
            .execute()
    else:
        # Insert new
        result = get_supabase().table("predictions").insert(data).execute()

    return result.data[0] if result.data else None


def get_prediction(product_id: str) -> Optional[Dict]:
    """Get latest prediction for a product"""
    result = get_supabase().table("predictions") \
        .select("*") \
        .eq("product_id", product_id) \
        .order("created_at", ascending=False) \
        .limit(1) \
        .execute()
    return result.data[0] if result.data else None


def get_all_products_needing_check() -> List[Dict]:
    """Get products that need price check (for scheduler)"""
    cutoff_time = (datetime.now() - timedelta(hours=6)).isoformat()
    result = get_supabase().table("price_history") \
        .select("product_id, products(*)") \
        .lt("scraped_at", cutoff_time) \
        .execute()

    # Get unique product IDs
    product_ids = list(set([item["product_id"] for item in result.data]))
    return product_ids


# ==================== HELPER FUNCTIONS ====================

def get_user_stats(user_id: str) -> Dict:
    """Get user statistics"""
    tracks = get_user_tracks(user_id)
    products = [t["products"] for t in tracks if t.get("products")]

    # Get all price histories for user's products
    total_savings = 0
    buy_now_count = 0
    wait_count = 0

    for track in tracks:
        prediction = get_prediction(track["product_id"])
        if prediction:
            if prediction["recommendation"] == "BUY_NOW":
                buy_now_count += 1
            elif prediction["recommendation"] == "WAIT":
                wait_count += 1

    return {
        "total_tracked": len(tracks),
        "buy_now_count": buy_now_count,
        "wait_count": wait_count,
        "products": products
    }
