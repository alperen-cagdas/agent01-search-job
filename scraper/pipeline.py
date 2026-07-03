import datetime
import json
import logging
import pathlib

from .config import load_profile, REPO_ROOT
from .scoring import score_and_filter
from .source_indeed import fetch_indeed
from .source_kariyer import fetch_kariyer

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
log = logging.getLogger(__name__)

DATA_DIR = REPO_ROOT / "data"
HISTORY_DIR = DATA_DIR / "history"
LATEST_PATH = DATA_DIR / "latest.json"


def run() -> dict:
    profile = load_profile()
    sources_status = {}
    all_jobs = []

    for name, fetch_fn in (("kariyer.net", fetch_kariyer), ("indeed", fetch_indeed)):
        try:
            jobs = fetch_fn(profile)
            sources_status[name] = "ok" if jobs else "failed"
            all_jobs.extend(jobs)
            log.info("%s: fetched %d raw listings", name, len(jobs))
        except Exception as e:
            log.error("%s: source failed entirely: %s", name, e)
            sources_status[name] = "failed"

    scored_jobs = score_and_filter(all_jobs, profile)
    log.info("scoring: %d listings passed threshold out of %d fetched", len(scored_jobs), len(all_jobs))

    generated_at = datetime.datetime.now(datetime.timezone.utc).isoformat()
    output = {
        "generated_at": generated_at,
        "sources_status": sources_status,
        "jobs": [j.to_dict() for j in scored_jobs],
    }

    HISTORY_DIR.mkdir(parents=True, exist_ok=True)
    today = datetime.date.today().isoformat()
    history_path = HISTORY_DIR / f"{today}.json"
    history_path.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")

    any_source_ok = any(status == "ok" for status in sources_status.values())
    if any_source_ok:
        LATEST_PATH.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
        log.info("wrote %s", LATEST_PATH)
    else:
        log.warning("all sources failed — leaving latest.json untouched, site keeps showing last good data")

    return output


if __name__ == "__main__":
    run()
