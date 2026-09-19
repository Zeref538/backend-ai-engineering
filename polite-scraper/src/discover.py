"""Find the book pages by following the site's own links, never by guessing URLs."""
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from fetcher import fetch

START = "https://books.toscrape.com/catalogue/page-1.html"
MAX_PAGES = 3  # the scope I wrote down in the README: first three catalogue pages


def discover():
    """Walk up to MAX_PAGES catalogue pages, collecting book links in order."""
    url, pages, seen, links = START, 0, set(), []

    while url and pages < MAX_PAGES:
        html = fetch(url)
        if html is None:
            break
        pages += 1
        soup = BeautifulSoup(html, "html.parser")

        for a in soup.select("article.product_pod h3 a"):
            # urljoin, not string gluing: "../foo.html" has to resolve against
            # the page it was found on, and gluing silently produces nonsense.
            link = urljoin(url, a["href"])
            if link not in seen:
                seen.add(link)
                links.append({"url": link, "source_page": url})

        nxt = soup.select_one("li.next a")
        url = urljoin(url, nxt["href"]) if nxt else None

    return pages, links


if __name__ == "__main__":
    pages, links = discover()
    print(f"catalogue_pages={pages}")
    print(f"discovered={len(links)}")
    print(f"unique_urls={len({l['url'] for l in links})}")
