"""Tests for the price scraper module (scraper.py).

These tests exercise the pure/offline logic (URL handling, price parsing,
price-drop detection). Live network scraping is intentionally NOT tested
in CI to avoid flaky external dependencies.
"""

import pytest

from scraper import (
    check_price_drop,
    detect_source,
    extract_product_id,
    generate_search_urls,
    parse_price,
)

# ==================== Source detection ====================


class TestDetectSource:
    def test_amazon(self):
        assert detect_source("https://www.amazon.in/dp/B0CHX3QCBS") == "amazon"

    def test_amazon_with_query_params(self):
        assert detect_source("https://www.amazon.in/dp/B0CHX3QCBS?tag=abc&psc=1") == "amazon"

    def test_flipkart(self):
        assert detect_source("https://www.flipkart.com/some-product/p/itmabc123") == "flipkart"

    def test_unknown_site(self):
        assert detect_source("https://example.com/product/123") == "unknown"

    def test_case_insensitive(self):
        assert detect_source("https://WWW.AMAZON.IN/dp/B0CHX3QCBS") == "amazon"


# ==================== Product ID extraction ====================


class TestExtractProductId:
    def test_amazon_dp(self):
        assert extract_product_id("https://www.amazon.in/dp/B0CHX3QCBS") == "B0CHX3QCBS"

    def test_amazon_gp_product(self):
        assert extract_product_id("https://www.amazon.in/gp/product/B0CHX3QCBS") == "B0CHX3QCBS"

    def test_flipkart(self):
        assert extract_product_id("https://www.flipkart.com/xyz/p/itmabc123") == "itmabc123"

    def test_no_id(self):
        assert extract_product_id("https://example.com/product/123") is None


# ==================== Price parsing ====================


class TestParsePrice:
    @pytest.mark.parametrize(
        "raw,expected",
        [
            ("₹74,999", 74999.0),
            ("Rs. 72,999.50", 72999.5),
            ("61,999", 61999.0),
            ("₹ 12,499.99", 12499.99),
            ("$1,299", 1299.0),  # handles non-INR symbols
            ("INR 20,000 INR", 20000.0),
        ],
    )
    def test_valid_prices(self, raw, expected):
        assert parse_price(raw) == expected

    def test_none_returns_none(self):
        assert parse_price(None) is None

    def test_empty_string_returns_none(self):
        assert parse_price("") is None

    def test_gibberish_returns_none(self):
        assert parse_price("No price available") is None


# ==================== Price drop detection ====================


class TestCheckPriceDrop:
    def test_drop_above_threshold(self):
        dropped, pct = check_price_drop(54000, 60000)
        assert dropped is True
        assert pct == 10.0

    def test_drop_below_threshold(self):
        dropped, pct = check_price_drop(58800, 60000)
        assert dropped is False
        assert pct == 2.0

    def test_missing_previous_price(self):
        dropped, pct = check_price_drop(54000, None)
        assert dropped is False
        assert pct == 0.0

    def test_missing_current_price(self):
        dropped, pct = check_price_drop(None, 60000)
        assert dropped is False
        assert pct == 0.0


# ==================== Search URL generation ====================


class TestGenerateSearchUrls:
    def test_amazon_urls(self):
        urls = generate_search_urls("https://www.amazon.in/dp/B0CHX3QCBS")
        assert len(urls) >= 1
        assert any("dp/B0CHX3QCBS" in u for u in urls)

    def test_unknown_url_passthrough(self):
        urls = generate_search_urls("https://example.com/thing")
        assert urls == ["https://example.com/thing"]
