#!/usr/bin/env python3
# fetch_webinars.py

import json
import os
import time
from typing import Any, Dict, List

import requests

API_URL = "https://www.sans.org/api/algolia"
INDEX_NAME = "webinar_single_startDateTimestamp_asc"
STATE_FILE = "state.json"


def load_existing_state() -> Dict[str, Any]:
    if not os.path.exists(STATE_FILE):
        return {"webinars": []}

    with open(STATE_FILE, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return {"webinars": []}


def save_state(state: Dict[str, Any]) -> None:
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2, ensure_ascii=False)


def build_payload(page: int, archived_before_ts: int) -> Dict[str, Any]:
    """
    Archived = endDateTimestamp < now.
    """
    return {
        "requests": [
            {
                "indexName": INDEX_NAME,
                "params": {
                    "facetFilters": [["facets.language:English"]],
                    "facets": ["facets.focusArea", "facets.language"],
                    "highlightPostTag": "__/ais-highlight__",
                    "highlightPreTag": "__ais-highlight__",
                    "hitsPerPage": 100,
                    "maxValuesPerFacet": 10,
                    "numericFilters": [f"endDateTimestamp<{archived_before_ts}"],
                    "page": page,
                    "query": "",
                },
            }
        ]
    }


def fetch_page(
    session: requests.Session, page: int, archived_before_ts: int
) -> Dict[str, Any]:
    payload = build_payload(page, archived_before_ts)

    headers = {
        "accept": "*/*",
        "content-type": "application/json",
        "origin": "https://www.sans.org",
        "referer": "https://www.sans.org/webcasts",
        "user-agent": "Mozilla/5.0 (compatible; sans-archive-scraper/1.0)",
    }

    resp = session.post(API_URL, json=payload, headers=headers, timeout=20)
    resp.raise_for_status()
    return resp.json()


def compute_duration_hours(hit: Dict[str, Any]) -> float | None:
    start_ts = hit.get("startDateTimestamp")
    end_ts = hit.get("endDateTimestamp")

    try:
        if isinstance(start_ts, str):
            start_ts = int(start_ts)
        if isinstance(end_ts, str):
            end_ts = int(end_ts)
    except (TypeError, ValueError):
        return None

    if not isinstance(start_ts, (int, float)) or not isinstance(end_ts, (int, float)):
        return None

    duration_seconds = end_ts - start_ts
    if duration_seconds <= 0:
        return None

    return duration_seconds / 3600.0


def format_duration_label(hours: float) -> str:
    total_minutes = int(round(hours * 60))
    h = total_minutes // 60
    m = total_minutes % 60
    parts = []
    if h:
        parts.append(f"{h}h")
    if m or not parts:
        parts.append(f"{m}m")
    return " ".join(parts)


def map_cysa_tags(title: str) -> List[str]:
    """
    Very rough keyword mapping to CySA+ domains / ideas.
    You can tweak this mapping as you see patterns.
    """
    title_lower = title.lower()
    tags: List[str] = []

    keyword_map = {
        "siem": "Threat & Security Monitoring (CySA+)",
        "detection": "Threat Detection (CySA+)",
        "endpoint": "Endpoint Threat Management (CySA+)",
        "incident": "Incident Response (CySA+)",
        "response": "Incident Response (CySA+)",
        "forensic": "Digital Forensics (CySA+)",
        "threat": "Threat Intelligence (CySA+)",
        "cloud": "Cloud Security (CySA+)",
        "survey": "Governance / Metrics (CySA+)",
        "phishing": "Threat & Vulnerability Management (CySA+)",
        "vulnerability": "Vulnerability Management (CySA+)",
        "attack": "Threat Management (CySA+)",
    }

    for kw, tag in keyword_map.items():
        if kw in title_lower and tag not in tags:
            tags.append(tag)

    return tags


def main() -> None:
    now_ts = int(time.time())

    existing_state = load_existing_state()
    existing_by_id = {
        w.get("objectID"): w
        for w in existing_state.get("webinars", [])
        if w.get("objectID")
    }

    session = requests.Session()

    page = 0
    webinars: List[Dict[str, Any]] = []

    while True:
        data = fetch_page(session, page, now_ts)
        results = data.get("results", [])
        if not results:
            break

        result0 = results[0]
        hits = result0.get("hits", [])
        nb_pages = result0.get("nbPages", page + 1)

        if not hits:
            break

        for hit in hits:
            duration_hours = compute_duration_hours(hit)
            if duration_hours is None:
                continue

            # You can filter duration range here if you only care about 1–3h
            # but for now, store everything and let the UI filter/sort.
            object_id = hit.get("objectID")
            prev = existing_by_id.get(object_id, {})

            title = (hit.get("title") or "").strip()
            cysa_tags = map_cysa_tags(title)

            record = {
                "objectID": object_id,
                "webcastId": hit.get("webcastId"),
                "title": title,
                "url": "https://www.sans.org" + (hit.get("url") or ""),
                "startDate": hit.get("startDate"),
                "startTime": hit.get("startTime"),
                "endDate": hit.get("endDate"),
                "endTime": hit.get("endTime"),
                "duration_hours": duration_hours,
                "duration_label": format_duration_label(duration_hours),
                "duration_bucket": int(round(duration_hours)),  # 1h, 2h, 3h, etc.
                "type": hit.get("type"),
                "focusAreas": hit.get("facets", {}).get("focusArea", []),
                "language": hit.get("language", []),
                "cysa_tags": cysa_tags,
                # Preserve watched flag if we already had this webinar
                "watched": bool(prev.get("watched", False)),
            }

            webinars.append(record)

        page += 1
        if page >= nb_pages:
            break

    state = {"webinars": webinars}
    save_state(state)
    print(f"Saved {len(webinars)} webinars to {STATE_FILE}")


if __name__ == "__main__":
    main()
