import random
import re
import time
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

from config import SCRAPERAPI_KEY

# User agents to rotate
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:119.0) Gecko/20100101 Firefox/119.0",
]

DEFAULT_HEADERS = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
}


def get_random_headers() -> dict:
    """Get random user agent headers"""
    headers = DEFAULT_HEADERS.copy()
    headers["User-Agent"] = random.choice(USER_AGENTS)
    return headers


def detect_source(url: str) -> str:
    """Detect which e-commerce site a URL belongs to"""
    domain = urlparse(url).netloc.lower()
    if "amazon" in domain:
        return "amazon"
    elif "flipkart" in domain:
        return "flipkart"
    elif "myntra" in domain:
        return "myntra"
    elif "ajio" in domain:
        return "ajio"
    else:
        return "unknown"


def extract_product_id(url: str) -> str | None:
    """Extract product ID from URL based on source"""
    source = detect_source(url)

    if source == "amazon":
        match = re.search(r"/dp/([A-Z0-9]{10})", url)
        if match:
            return match.group(1)
        match = re.search(r"/gp/product/([A-Z0-9]{10})", url)
        if match:
            return match.group(1)
    elif source == "flipkart":
        match = re.search(r"/p/([a-zA-Z0-9]+)", url)
        if match:
            return match.group(1)

    return None


def fetch_with_scraperapi(url: str) -> requests.Response | None:
    """Fetch URL using ScraperAPI as proxy"""
    if not SCRAPERAPI_KEY:
        return None
    try:
        api_url = (
            f"https://api.scraperapi.com/?api_key={SCRAPERAPI_KEY}&url={requests.utils.quote(url, safe='')}&render=true"
        )
        response = requests.get(api_url, timeout=30)
        if response.status_code == 200:
            return response
    except Exception:
        pass
    return None


def fetch_page(url: str) -> requests.Response | None:
    """Fetch a webpage with retry logic"""
    # First try direct request
    for _attempt in range(2):
        try:
            headers = get_random_headers()
            response = requests.get(url, headers=headers, timeout=20)
            if (
                response.status_code == 200
                and "captcha" not in response.url.lower()
                and "sorry" not in response.url.lower()
            ):
                return response
        except Exception:
            pass
        time.sleep(random.uniform(1, 3))

    # Fall back to ScraperAPI
    return fetch_with_scraperapi(url)


def parse_price(text: str) -> float | None:
    """Extract price from HTML text, handling various formats"""
    if not text:
        return None

    # Remove currency symbols and commas
    cleaned = (
        text.replace("₹", "")
        .replace("Rs.", "")
        .replace("₹", "")
        .replace(",", "")
        .replace("INR", "")
        .replace(" ", "")
        .strip()
    )

    # Match patterns like 74999, 72,999.00, 74999.99
    match = re.search(r"(\d+(?:\.\d{1,2})?)", cleaned)
    if match:
        try:
            return float(match.group(1))
        except ValueError:
            return None
    return None


def scrape_amazon(url: str) -> dict:
    """Scrape product info from Amazon India"""
    result = {"name": None, "price": None, "image_url": None, "success": False, "error": None}
    response = fetch_page(url)

    if not response:
        result["error"] = "Failed to fetch page"
        return result

    soup = BeautifulSoup(response.text, "html.parser")

    # Product title
    title_elem = soup.select_one("#productTitle")
    if title_elem:
        result["name"] = title_elem.get_text(strip=True)

    # Price - try multiple selectors
    price = None
    price_selectors = [
        "span.a-price-whole",
        "span.a-price > span.a-offscreen",
        "span#priceblock_ourprice",
        "span#priceblock_dealprice",
        "span.a-price.a-text-price > span.a-offscreen",
        "span.a-price.a-text-price.a-text-secondary > span.a-offscreen",
    ]
    for selector in price_selectors:
        elem = soup.select_one(selector)
        if elem:
            price = parse_price(elem.get_text())
            if price:
                break

    if not price:
        # Try meta og:price
        meta = soup.find("meta", {"property": "og:price:amount"})
        if meta and meta.get("content"):
            price = parse_price(meta["content"])

    result["price"] = price

    # Image
    img_elem = soup.select_one("#landingImage")
    if img_elem:
        result["image_url"] = img_elem.get("data-old-hires") or img_elem.get("src")
    else:
        img_elem = soup.find("meta", {"property": "og:image"})
        if img_elem:
            result["image_url"] = img_elem.get("content")

    result["success"] = result["price"] is not None
    if not result["success"]:
        result["error"] = "Could not extract price (may be blocked by Amazon)"

    return result


def scrape_flipkart(url: str) -> dict:
    """Scrape product info from Flipkart"""
    result = {"name": None, "price": None, "image_url": None, "success": False, "error": None}
    response = fetch_page(url)

    if not response:
        result["error"] = "Failed to fetch page"
        return result

    soup = BeautifulSoup(response.text, "html.parser")

    # Product title
    title_elem = soup.select_one("span.VU-ZEz")
    if title_elem:
        result["name"] = title_elem.get_text(strip=True)

    # Price
    price_elem = soup.select_one("div.Nx9bqj")
    if price_elem:
        result["price"] = parse_price(price_elem.get_text())

    # Alternative selectors
    if not result["price"]:
        price_selectors = [
            "div._30jeq3._1_WHN1",
            "span._30jeq3._16Jk6d",
            "div.yKWBG",
            "_4b5Khy",
        ]
        for selector in price_selectors:
            elem = soup.select_one(selector)
            if elem:
                result["price"] = parse_price(elem.get_text())
                if result["price"]:
                    break

    # Image
    img_elem = soup.find("meta", {"property": "og:image"})
    if img_elem:
        result["image_url"] = img_elem.get("content")

    result["success"] = result["price"] is not None
    if not result["success"]:
        result["error"] = "Could not extract price (may be blocked by Flipkart)"

    return result


def scrape_product(url: str) -> dict:
    """Main entry point - scrape any supported product URL"""
    source = detect_source(url)

    if source == "amazon":
        result = scrape_amazon(url)
    elif source == "flipkart":
        result = scrape_flipkart(url)
    else:
        result = {
            "name": None,
            "price": None,
            "image_url": None,
            "success": False,
            "error": "Unsupported website. Only Amazon.in and Flipkart are supported.",
        }

    result["source"] = source
    result["url"] = url
    result["product_id"] = extract_product_id(url)

    if result["name"] is None:
        parsed = urlparse(url)
        result["name"] = parsed.netloc.replace("www.", "")

    return result


def generate_search_urls(product_url: str) -> list[str]:
    """Generate alternative URLs to try for a product"""
    source = detect_source(product_url)
    product_id = extract_product_id(product_url)
    urls = []

    if source == "amazon" and product_id:
        urls.append(f"https://www.amazon.in/dp/{product_id}")
        urls.append(f"https://www.amazon.in/gp/product/{product_id}")
        urls.append(f"https://www.amazon.in/dp/{product_id}?psc=1")

    return urls if urls else [product_url]


def check_price_drop(current_price: float, previous_price: float) -> tuple[bool, float]:
    """Check if price has dropped significantly"""
    if not previous_price or not current_price:
        return False, 0.0

    drop_percent = ((previous_price - current_price) / previous_price) * 100
    return drop_percent > 3.0, drop_percent
