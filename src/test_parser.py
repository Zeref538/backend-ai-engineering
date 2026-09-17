"""Run: python src/test_parser.py

These run on fixed scraps of HTML, not on the live site, so they answer one
question only: does my parsing still do what I think it does? A site outage
can't make them fail, and a site redesign will.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from urllib.parse import urljoin  # noqa: E402

from extract import extract  # noqa: E402
from schema import Book, normalize  # noqa: E402

PAGE = """
<article class="product_page">
  <h1>  A Light in the Attic </h1>
  <p class="price_color">£51.77</p>
  <p class="instock availability">In stock (22 available)</p>
  <p class="star-rating Three"></p>
</article>
<div id="product_description"></div>
<p>It is a book.</p>
"""
URL = "https://books.toscrape.com/catalogue/a-light_1/index.html"


def raw(html=PAGE):
    return extract(html, URL, "https://books.toscrape.com/catalogue/page-1.html")


def test_price_becomes_a_number():
    assert normalize(raw())["price_gbp"] == 51.77


def test_rating_word_becomes_a_number():
    assert normalize(raw())["rating"] == 3


def test_whitespace_is_stripped_from_the_title():
    assert raw()["title"] == "A Light in the Attic"


def test_missing_description_is_none_not_invented():
    html = PAGE.replace('<div id="product_description"></div>', "").replace("<p>It is a book.</p>", "")
    assert raw(html)["description"] is None
    # ...and a record with no description is still valid.
    assert Book(**normalize(raw(html))).description is None


def test_relative_links_resolve_against_their_page():
    page = "https://books.toscrape.com/catalogue/page-2.html"
    assert urljoin(page, "../media/x.jpg") == "https://books.toscrape.com/media/x.jpg"
    assert urljoin(page, "a-light_1/index.html") == "https://books.toscrape.com/catalogue/a-light_1/index.html"


def test_a_malformed_page_is_rejected_not_stored():
    broken = "<html><body><h1>Error</h1></body></html>"
    try:
        Book(**normalize(raw(broken)))
    except Exception:
        return
    raise AssertionError("a page with no price should never validate")


def test_out_of_stock_is_read_from_the_text():
    html = PAGE.replace("In stock (22 available)", "Out of stock")
    assert normalize(raw(html))["in_stock"] is False
    assert normalize(raw())["in_stock"] is True


def test_duplicate_urls_collapse_to_one():
    records = [normalize(raw()), normalize(raw())]
    assert len({r["product_url"] for r in records}) == 1


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_"):
            fn()
            print("ok  ", name)
    print("all checks passed")
