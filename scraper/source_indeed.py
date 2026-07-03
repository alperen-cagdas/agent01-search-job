import logging
import re
import time
import urllib.parse
import xml.etree.ElementTree as ET

import requests

from .schema import Job

log = logging.getLogger(__name__)

RSS_BASE = "https://rss.indeed.com/rss"
REQUEST_DELAY_SECONDS = 1
REQUEST_TIMEOUT_SECONDS = 15
USER_AGENT = (
    "alperen-job-search-bot/1.0 "
    "(personal job-search project; contact: alperencagdas.id@gmail.com)"
)

# Indeed RSS titles are typically "<Job Title> - <Company> - <Location>".
TITLE_PATTERN = re.compile(r"^(?P<title>.+?)\s-\s(?P<company>.+?)\s-\s(?P<location>.+)$")


def _build_query_urls(profile: dict) -> list[str]:
    keywords = profile["role_keywords"]["primary"] + profile["role_keywords"]["secondary"]
    locations = profile["search_locations"]
    urls = []
    for kw in keywords:
        for loc in locations:
            params = urllib.parse.urlencode({"q": kw, "l": loc})
            urls.append(f"{RSS_BASE}?{params}")
    return urls


def _parse_item(item) -> Job | None:
    raw_title = (item.findtext("title") or "").strip()
    match = TITLE_PATTERN.match(raw_title)
    if match:
        title = match.group("title").strip()
        company = match.group("company").strip()
        location = match.group("location").strip()
    else:
        title = raw_title or "Unknown"
        company = "Unknown"
        location = "Unknown"

    url = (item.findtext("link") or "").strip()
    if not url:
        return None

    return Job(
        title=title,
        company=company,
        location=location,
        url=url,
        source="indeed",
        posted_date=(item.findtext("pubDate") or None),
        description_snippet=(item.findtext("description") or "").strip(),
    )


def fetch_indeed(profile: dict) -> list[Job]:
    jobs: list[Job] = []
    seen_urls: set[str] = set()
    headers = {"User-Agent": USER_AGENT}

    for url in _build_query_urls(profile):
        try:
            resp = requests.get(url, headers=headers, timeout=REQUEST_TIMEOUT_SECONDS)
            resp.raise_for_status()
            root = ET.fromstring(resp.content)
            items = root.findall("./channel/item")
            if not items:
                log.warning("indeed: empty feed for %s", url)
            for item in items:
                try:
                    job = _parse_item(item)
                    if job and job.url not in seen_urls:
                        seen_urls.add(job.url)
                        jobs.append(job)
                except Exception as e:
                    log.warning("indeed: failed to parse item: %s", e)
        except Exception as e:
            log.error("indeed: query failed for %s: %s", url, e)
        time.sleep(REQUEST_DELAY_SECONDS)

    return jobs
