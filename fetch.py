#!/usr/bin/env python3
import json
import os
import time
from typing import Any, Dict, List

import requests

API_URL = "https://www.sans.org/api/algolia"
INDEX_NAME = "webinar_single_startDateTimestamp_asc"

DATA_FILE = "data.json"  # canonical webinar data (no user state)

# --- CySA+ keyword mapping -----------------------------------------------

CYSA_KEYWORD_MAP = {
    # --- Domain 1: Security Operations (Monitoring, Hunting, Threat Intel) ---
    "siem": "Security Operations – SIEM & Log Analysis (CySA+ D1)",
    "splunk": "Security Operations – SIEM & Log Analysis (CySA+ D1)",
    "qradar": "Security Operations – SIEM & Log Analysis (CySA+ D1)",
    "log analysis": "Security Operations – SIEM & Log Analysis (CySA+ D1)",
    "log monitoring": "Security Operations – SIEM & Log Analysis (CySA+ D1)",
    "log analytics": "Security Operations – SIEM & Log Analysis (CySA+ D1)",
    "syslog": "Security Operations – SIEM & Log Analysis (CySA+ D1)",
    "edr": "Security Operations – Endpoint Detection & Response (CySA+ D1)",
    "xdr": "Security Operations – Endpoint Detection & Response (CySA+ D1)",
    "endpoint detection": "Security Operations – Endpoint Detection & Response (CySA+ D1)",
    "endpoint security": "Security Operations – Endpoint Detection & Response (CySA+ D1)",
    "ngav": "Security Operations – Endpoint Detection & Response (CySA+ D1)",
    "soar": "Security Operations – Automation & Orchestration (CySA+ D1)",
    "automation": "Security Operations – Automation & Orchestration (CySA+ D1)",
    "orchestration": "Security Operations – Automation & Orchestration (CySA+ D1)",
    "playbook automation": "Security Operations – Automation & Orchestration (CySA+ D1)",
    "threat hunting": "Security Operations – Threat Hunting (CySA+ D1)",
    "hunt team": "Security Operations – Threat Hunting (CySA+ D1)",
    "proactive hunting": "Security Operations – Threat Hunting (CySA+ D1)",
    "threat intelligence": "Security Operations – Threat Intelligence (CySA+ D1)",
    "threat intel": "Security Operations – Threat Intelligence (CySA+ D1)",
    "ioc": "Security Operations – Threat Intelligence (CySA+ D1)",
    "indicator of compromise": "Security Operations – Threat Intelligence (CySA+ D1)",
    "mitre att&ck": "Security Operations – Threat Intelligence (CySA+ D1)",
    "tactics, techniques, and procedures": "Security Operations – Threat Intelligence (CySA+ D1)",
    "ttp": "Security Operations – Threat Intelligence (CySA+ D1)",
    "apt ": "Security Operations – Threat Intelligence (CySA+ D1)",  # note trailing space
    "ids": "Security Operations – Network Monitoring (CySA+ D1)",
    "ips": "Security Operations – Network Monitoring (CySA+ D1)",
    "ndr": "Security Operations – Network Monitoring (CySA+ D1)",
    "zeek": "Security Operations – Network Monitoring (CySA+ D1)",
    "suricata": "Security Operations – Network Monitoring (CySA+ D1)",
    "snort": "Security Operations – Network Monitoring (CySA+ D1)",
    "network detection": "Security Operations – Network Monitoring (CySA+ D1)",
    "zero trust": "Security Operations – Zero Trust & Access Controls (CySA+ D1)",
    "ztna": "Security Operations – Zero Trust & Access Controls (CySA+ D1)",
    "sase": "Security Operations – Zero Trust & Access Controls (CySA+ D1)",
    "least privilege": "Security Operations – Zero Trust & Access Controls (CySA+ D1)",
    "phishing": "Security Operations – Email & User-Focused Threats (CySA+ D1)",
    "spearphishing": "Security Operations – Email & User-Focused Threats (CySA+ D1)",
    "business email compromise": "Security Operations – Email & User-Focused Threats (CySA+ D1)",
    "bec": "Security Operations – Email & User-Focused Threats (CySA+ D1)",
    # --- Domain 2: Vulnerability Management ----------------------------------
    "vulnerability management": "Vulnerability Management – Program & Process (CySA+ D2)",
    "vulnerability assessment": "Vulnerability Management – Program & Process (CySA+ D2)",
    "vulnerability scanning": "Vulnerability Management – Scanning & Tools (CySA+ D2)",
    "scan tuning": "Vulnerability Management – Scanning & Tools (CySA+ D2)",
    "nessus": "Vulnerability Management – Scanning & Tools (CySA+ D2)",
    "openvas": "Vulnerability Management – Scanning & Tools (CySA+ D2)",
    "qualys": "Vulnerability Management – Scanning & Tools (CySA+ D2)",
    "burp suite": "Vulnerability Management – Web & App Security (CySA+ D2)",
    "appscan": "Vulnerability Management – Web & App Security (CySA+ D2)",
    "attack surface management": "Vulnerability Management – Attack Surface Management (CySA+ D2)",
    "external attack surface": "Vulnerability Management – Attack Surface Management (CySA+ D2)",
    "asset discovery": "Vulnerability Management – Asset Discovery (CySA+ D2)",
    "cvss": "Vulnerability Management – Prioritization & Scoring (CySA+ D2)",
    "cve": "Vulnerability Management – Prioritization & Scoring (CySA+ D2)",
    "exploitability": "Vulnerability Management – Prioritization & Scoring (CySA+ D2)",
    "zero-day": "Vulnerability Management – Prioritization & Scoring (CySA+ D2)",
    "patch management": "Vulnerability Management – Remediation & Hardening (CySA+ D2)",
    "patching": "Vulnerability Management – Remediation & Hardening (CySA+ D2)",
    "configuration management": "Vulnerability Management – Remediation & Hardening (CySA+ D2)",
    "hardening": "Vulnerability Management – Remediation & Hardening (CySA+ D2)",
    "baseline configuration": "Vulnerability Management – Remediation & Hardening (CySA+ D2)",
    "owasp top 10": "Vulnerability Management – Web & App Security (CySA+ D2)",
    "xss": "Vulnerability Management – Web & App Security (CySA+ D2)",
    "cross-site scripting": "Vulnerability Management – Web & App Security (CySA+ D2)",
    "sql injection": "Vulnerability Management – Web & App Security (CySA+ D2)",
    "sqli": "Vulnerability Management – Web & App Security (CySA+ D2)",
    "command injection": "Vulnerability Management – Web & App Security (CySA+ D2)",
    "directory traversal": "Vulnerability Management – Web & App Security (CySA+ D2)",
    "csrf": "Vulnerability Management – Web & App Security (CySA+ D2)",
    "cross-site request forgery": "Vulnerability Management – Web & App Security (CySA+ D2)",
    "rce": "Vulnerability Management – Web & App Security (CySA+ D2)",
    "remote code execution": "Vulnerability Management – Web & App Security (CySA+ D2)",
    "container security": "Vulnerability Management – Cloud & Container (CySA+ D2)",
    "docker": "Vulnerability Management – Cloud & Container (CySA+ D2)",
    "kubernetes": "Vulnerability Management – Cloud & Container (CySA+ D2)",
    "k8s": "Vulnerability Management – Cloud & Container (CySA+ D2)",
    "iac": "Vulnerability Management – Cloud & Container (CySA+ D2)",
    "cloud misconfiguration": "Vulnerability Management – Cloud & Container (CySA+ D2)",
    "threat modeling": "Vulnerability Management – Threat Modeling & SDLC (CySA+ D2)",
    "sdlc": "Vulnerability Management – Threat Modeling & SDLC (CySA+ D2)",
    "secure coding": "Vulnerability Management – Threat Modeling & SDLC (CySA+ D2)",
    # reuse from your original map
    "phishing": "Threat & Vulnerability Management (CySA+ D2)",
    "vulnerability": "Vulnerability Management – General (CySA+ D2)",
    "attack": "Threat & Vulnerability Management (CySA+ D2)",
    # --- Domain 3: Incident Response & Management ----------------------------
    "incident response": "Incident Response – Process & Playbooks (CySA+ D3)",
    "ir playbook": "Incident Response – Process & Playbooks (CySA+ D3)",
    "playbooks": "Incident Response – Process & Playbooks (CySA+ D3)",
    "tabletop": "Incident Response – Exercises & Readiness (CySA+ D3)",
    "ttx": "Incident Response – Exercises & Readiness (CySA+ D3)",
    "forensic": "Incident Response – Digital Forensics (CySA+ D3)",
    "forensics": "Incident Response – Digital Forensics (CySA+ D3)",
    "dfir": "Incident Response – Digital Forensics (CySA+ D3)",
    "memory analysis": "Incident Response – Digital Forensics (CySA+ D3)",
    "timeline analysis": "Incident Response – Digital Forensics (CySA+ D3)",
    "kill chain": "Incident Response – Attack Methodologies (CySA+ D3)",
    "cyber kill chain": "Incident Response – Attack Methodologies (CySA+ D3)",
    "diamond model": "Incident Response – Attack Methodologies (CySA+ D3)",
    "mitre att&ck framework": "Incident Response – Attack Methodologies (CySA+ D3)",
    "ransomware": "Incident Response – Malware & Ransomware (CySA+ D3)",
    "malware": "Incident Response – Malware & Ransomware (CySA+ D3)",
    "command and control": "Incident Response – Malware & Ransomware (CySA+ D3)",
    "c2 channel": "Incident Response – Malware & Ransomware (CySA+ D3)",
    "containment": "Incident Response – Containment & Recovery (CySA+ D3)",
    "eradication": "Incident Response – Containment & Recovery (CySA+ D3)",
    "recovery": "Incident Response – Containment & Recovery (CySA+ D3)",
    "lessons learned": "Incident Response – Post-Incident (CySA+ D3)",
    "post-incident": "Incident Response – Post-Incident (CySA+ D3)",
    # --- Domain 4: Reporting & Communication --------------------------------
    "metrics": "Reporting & Communication – Metrics & KPIs (CySA+ D4)",
    "kpi": "Reporting & Communication – Metrics & KPIs (CySA+ D4)",
    "dashboard": "Reporting & Communication – Metrics & KPIs (CySA+ D4)",
    "analytics": "Reporting & Communication – Metrics & KPIs (CySA+ D4)",
    "compliance": "Reporting & Communication – Compliance & Governance (CySA+ D4)",
    "audit": "Reporting & Communication – Compliance & Governance (CySA+ D4)",
    "pci": "Reporting & Communication – Compliance & Governance (CySA+ D4)",
    "hipaa": "Reporting & Communication – Compliance & Governance (CySA+ D4)",
    "sox": "Reporting & Communication – Compliance & Governance (CySA+ D4)",
    "gdpr": "Reporting & Communication – Compliance & Governance (CySA+ D4)",
    "policy": "Reporting & Communication – Compliance & Governance (CySA+ D4)",
    "risk register": "Reporting & Communication – Risk Reporting (CySA+ D4)",
    "risk management": "Reporting & Communication – Risk Reporting (CySA+ D4)",
    "residual risk": "Reporting & Communication – Risk Reporting (CySA+ D4)",
    "inherent risk": "Reporting & Communication – Risk Reporting (CySA+ D4)",
    "executive": "Reporting & Communication – Stakeholder Communication (CySA+ D4)",
    "board": "Reporting & Communication – Stakeholder Communication (CySA+ D4)",
    "stakeholder": "Reporting & Communication – Stakeholder Communication (CySA+ D4)",
    "briefing": "Reporting & Communication – Stakeholder Communication (CySA+ D4)",
}


def save_data(webinars: List[Dict[str, Any]]) -> None:
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump({"webinars": webinars}, f, indent=2, ensure_ascii=False)


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
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36",
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


def compute_duration_bucket(hours: float) -> int:
    """
    Duration bucket:
      0 => < 1 hour
      1 => [1, 2)
      2 => [2, 3)
      etc.
    """
    if hours < 1.0:
        return 0
    return int(hours)  # floor: 1h-1.99 => 1, 2h-2.99 => 2, etc.


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


def map_cysa_tags(title: str, description: str = "") -> list[str]:
    """
    Generate CySA+ tags from title/description using CYSA_KEYWORD_MAP.
    Simple substring match; tune keywords if it gets too noisy.
    """
    text = f"{title or ''} {description or ''}".lower()
    tags = set()

    for kw, tag in CYSA_KEYWORD_MAP.items():
        if kw in text:
            tags.add(tag)

    # Stable order for UI
    return sorted(tags)


def main() -> None:
    now_ts = int(time.time())
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

            title = (hit.get("title") or "").strip()
            description = hit.get("description") or ""
            cysa_tags = map_cysa_tags(title, description)

            duration_bucket = compute_duration_bucket(duration_hours)

            record = {
                "objectID": hit.get("objectID"),
                "webcastId": hit.get("webcastId"),
                "title": title,
                "url": "https://www.sans.org" + (hit.get("url") or ""),
                "description": description,
                "startDate": hit.get("startDate"),
                "startTime": hit.get("startTime"),
                "endDate": hit.get("endDate"),
                "endTime": hit.get("endTime"),
                "duration_hours": duration_hours,
                "duration_label": format_duration_label(duration_hours),
                "duration_bucket": duration_bucket,  # 0=<1h, 1≈1h, 2≈2h, etc.
                "type": hit.get("type"),
                "focusAreas": hit.get("facets", {}).get("focusArea", []),
                "language": hit.get("language", []),
                "createdAt": hit.get("createdAt"),
                "createdAtTimestamp": hit.get("createdAtTimestamp"),
                "updatedAt": hit.get("updatedAt"),
                "updatedAtTimestamp": hit.get("updatedAtTimestamp"),
                "cysa_tags": cysa_tags,
            }

            webinars.append(record)

        page += 1
        if page >= nb_pages:
            break

    save_data(webinars)
    print(f"Saved {len(webinars)} webinars to {DATA_FILE}")


if __name__ == "__main__":
    main()
