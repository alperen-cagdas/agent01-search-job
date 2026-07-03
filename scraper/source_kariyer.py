"""kariyer.net scraper.

IMPORTANT: kariyer.net has no public API/RSS. This module scrapes only the
public, non-authenticated job-search result pages. The exact search URL
query parameter and the CSS selectors below were not verified against a
live page (this development environment's outbound network policy blocks
kariyer.net), so they are a best-effort starting point. Before relying on
this in production:

  1. Open a real search URL in a browser, e.g.
     https://www.kariyer.net/is-ilanlari?kw=endustriyel+tasarimci
  2. Confirm the query parameter name actually used, and inspect a job
     listing card's HTML to update CARD_SELECTOR / FIELD_SELECTORS below.
  3. Run `python -m scraper.pipeline` (or trigger the GitHub Actions
     workflow via workflow_dispatch, since it runs on GitHub's network,
     not this sandbox) and check the logs for
     "kariyer.net: 0 listings parsed" warnings.

The scraper is intentionally defensive: any failure here (wrong selector,
site markup change, network error) is caught and logged, never raised,
so the overall daily pipeline still publishes with Indeed results.
"""

import logging
import time
import urllib.parse

import requests
from bs4 import BeautifulSoup

from .schema import Job

log = logging.getLogger(__name__)

SEARCH_URL = "https://www.kariyer.net/is-ilanlari"
REQUEST_DELAY_SECONDS = 2
REQUEST_TIMEOUT_SECONDS = 15
# kariyer.net returns 403 to requests identifying as bots or coming from
# datacenter IPs; browser-like headers are the least-invasive workaround for
# this personal, once-daily, rate-limited use.
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
)
BROWSER_HEADERS = {
    "User-Agent": USER_AGENT,
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "tr-TR,tr;q=0.9,en;q=0.8",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
}

# Best-effort selectors — verify against the live site (see module docstring).
CARD_SELECTOR = "div.list-items, div.job-list-item, li.list-items"
TITLE_SELECTOR = "a.job-title, a.position-title, h2 a, h3 a"
COMPANY_SELECTOR = "a.company-name, span.company-name, div.company-name"
LOCATION_SELECTOR = "span.location, div.location, span.city"
DATE_SELECTOR = "span.date, div.date, time"


def _fetch_search_page(keyword: str) -> str | None:
    params = urllib.parse.urlencode({"kw": keyword})
    url = f"{SEARCH_URL}?{params}"
    try:
        resp = requests.get(url, headers=BROWSER_HEADERS, timeout=REQUEST_TIMEOUT_SECONDS)
        resp.raise_for_status()
        return resp.text
    except Exception as e:
        log.error("kariyer.net: request failed for keyword '%s': %s", keyword, e)
        return None


def _text_or_none(el):
    return el.get_text(strip=True) if el else None


def _parse_card(card, keyword: str) -> Job | None:
    try:
        title_el = card.select_one(TITLE_SELECTOR)
        title = _text_or_none(title_el)
        url = title_el.get("href") if title_el else None
        if url and url.startswith("/"):
            url = f"https://www.kariyer.net{url}"

        if not title or not url:
            return None

        company = _text_or_none(card.select_one(COMPANY_SELECTOR)) or "Unknown"
        location = _text_or_none(card.select_one(LOCATION_SELECTOR)) or "Unknown"
        posted_date = _text_or_none(card.select_one(DATE_SELECTOR))

        return Job(
            title=title,
            company=company,
            location=location,
            url=url,
            source="kariyer.net",
            posted_date=posted_date,
            description_snippet=title,
        )
    except Exception as e:
        log.warning("kariyer.net: failed to parse a listing card (keyword=%s): %s", keyword, e)
        return None


def fetch_kariyer(profile: dict) -> list[Job]:
    jobs: list[Job] = []
    seen_urls: set[str] = set()
    keywords = profile["role_keywords"]["primary"] + profile["role_keywords"]["secondary"]

    for keyword in keywords:
        html = _fetch_search_page(keyword)
        if html is None:
            time.sleep(REQUEST_DELAY_SECONDS)
            continue

        try:
            soup = BeautifulSoup(html, "html.parser")
            cards = soup.select(CARD_SELECTOR)
            if not cards:
                log.warning(
                    "kariyer.net: 0 listings parsed for keyword '%s' — "
                    "selectors may be outdated, see module docstring",
                    keyword,
                )
            for card in cards:
                job = _parse_card(card, keyword)
                if job and job.url not in seen_urls:
                    seen_urls.add(job.url)
                    jobs.append(job)
        except Exception as e:
            log.error("kariyer.net: failed to parse page for keyword '%s': %s", keyword, e)

        time.sleep(REQUEST_DELAY_SECONDS)

    return jobs
