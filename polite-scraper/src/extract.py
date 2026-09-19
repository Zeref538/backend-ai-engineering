"""Turn one book page into a raw record: what the page said, nothing invented."""
from datetime import datetime, timezone

from bs4 import BeautifulSoup

RATING_WORDS = ("One", "Two", "Three", "Four", "Five")


def extract(html: str, url: str, source_page: str) -> dict:
    soup = BeautifulSoup(html, "html.parser")
    # Aim at the product area, not the whole document -- the page also has a
    # sidebar and a footer, and a loose selector happily grabs those instead.
    main = soup.select_one("article.product_page") or soup

    rating = None
    tag = main.select_one("p.star-rating")
    if tag:
        # The rating is a CSS class, e.g. class="star-rating Three".
        rating = next((c for c in tag.get("class", []) if c in RATING_WORDS), None)

    description = None
    heading = soup.select_one("#product_description")
    if heading:
        para = heading.find_next_sibling("p")
        if para:
            description = para.get_text(strip=True)

    return {
        "title": main.select_one("h1").get_text(strip=True) if main.select_one("h1") else None,
        "product_url": url,
        "price_text": el.get_text(strip=True) if (el := main.select_one("p.price_color")) else None,
        "availability_text": el.get_text(strip=True) if (el := main.select_one("p.instock.availability")) else None,
        "rating_text": rating,
        "description": description,          # genuinely absent on some books -> None
        "source_page": source_page,          # provenance: which listing page found it
        "fetched_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
