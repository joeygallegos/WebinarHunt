#!/usr/bin/env python3
# app.py

import json
import os
from typing import Any, Dict, List, Optional

from flask import Flask, jsonify, render_template, request

DATA_FILE = "data.json"  # canonical webinar data
STATE_FILE = "state.json"  # user state: watched/favorite keyed by webcastId

app = Flask(__name__)


# ---------- Helpers for data + state ------------------


def load_data() -> List[Dict[str, Any]]:
    if not os.path.exists(DATA_FILE):
        return []
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        try:
            payload = json.load(f)
        except json.JSONDecodeError:
            return []
    return payload.get("webinars", [])


def load_state() -> Dict[str, Dict[str, Any]]:
    """
    Returns:
        {
          "<webcastId>": {"watched": bool, "favorite": bool},
          ...
        }
    """
    if not os.path.exists(STATE_FILE):
        return {}

    with open(STATE_FILE, "r", encoding="utf-8") as f:
        try:
            state = json.load(f)
        except json.JSONDecodeError:
            return {}

    # Backward compat: if file has top-level "webcast_state", unwrap it
    if "webcast_state" in state and isinstance(state["webcast_state"], dict):
        return state["webcast_state"]

    if isinstance(state, dict):
        return state

    return {}


def save_state(state: Dict[str, Dict[str, Any]]) -> None:
    # Simple flat mapping keyed by webcastId
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2, ensure_ascii=False)


def build_objectid_to_webcastid_map(webinars: List[Dict[str, Any]]) -> Dict[str, str]:
    mapping: Dict[str, str] = {}
    for w in webinars:
        obj = w.get("objectID")
        wid = w.get("webcastId")
        if obj is None or wid is None:
            continue
        mapping[str(obj)] = str(wid)
    return mapping


def merge_data_and_state() -> List[Dict[str, Any]]:
    """
    Combines data.json with state.json. Returns a list of webinar dicts
    that the UI can safely consume (always has watched/favorite flags).
    """
    data_webinars = load_data()
    state = load_state()

    merged: List[Dict[str, Any]] = []

    for w in data_webinars:
        webcast_id_raw = w.get("webcastId")
        webcast_id: Optional[str] = None
        if webcast_id_raw is not None:
            webcast_id = str(webcast_id_raw)

        st = state.get(webcast_id, {}) if webcast_id else {}

        merged.append(
            {
                **w,
                "watched": bool(st.get("watched", False)),
                "favorite": bool(st.get("favorite", False)),
            }
        )

    return merged


def resolve_webcast_id(
    *,
    webinars: List[Dict[str, Any]],
    webcast_id: Optional[str],
    object_id: Optional[str]
) -> Optional[str]:
    """
    Prefer explicit webcastId.
    If only objectID is provided, map it to webcastId using data.json.
    """
    if webcast_id:
        return webcast_id

    if not object_id:
        return None

    # Build map objectID -> webcastId
    mapping = build_objectid_to_webcastid_map(webinars)
    return mapping.get(object_id)


# ---------- Routes ------------------


@app.route("/")
def index():
    # Combine data + state before rendering
    webinars = merge_data_and_state()

    # You can pre-sort here if you want, but the Alpine front-end already
    # does client-side sorting. This is just a reasonable default:
    webinars_sorted = sorted(
        webinars,
        key=lambda w: (
            int(w.get("duration_bucket", 999)),
            -int(w.get("createdAtTimestamp") or 0),  # newer first within bucket
            (w.get("title") or "").lower(),
        ),
    )

    return render_template("index.html", webinars=webinars_sorted)


@app.route("/api/webinars")
def api_webinars():
    webinars = merge_data_and_state()
    return jsonify(webinars)


@app.route("/api/toggle-watched", methods=["POST"])
def toggle_watched():
    payload = request.get_json(force=True, silent=True) or {}
    raw_webcast_id = payload.get("webcastId")
    raw_object_id = payload.get("objectID")
    watched = payload.get("watched")

    if watched is None:
        return jsonify({"ok": False, "error": "Missing watched flag"}), 400

    webinars = load_data()
    webcast_id = None
    if raw_webcast_id is not None:
        webcast_id = str(raw_webcast_id)
    else:
        # Allow old clients sending only objectID
        object_id = str(raw_object_id) if raw_object_id is not None else None
        webcast_id = resolve_webcast_id(
            webinars=webinars,
            webcast_id=None,
            object_id=object_id,
        )

    if not webcast_id:
        return jsonify({"ok": False, "error": "webcastId could not be resolved"}), 400

    state = load_state()
    st = state.get(webcast_id, {})
    st["watched"] = bool(watched)
    state[webcast_id] = st
    save_state(state)

    return jsonify({"ok": True})


@app.route("/api/toggle-favorite", methods=["POST"])
def toggle_favorite():
    payload = request.get_json(force=True, silent=True) or {}
    raw_webcast_id = payload.get("webcastId")
    raw_object_id = payload.get("objectID")
    favorite = payload.get("favorite")

    if favorite is None:
        return jsonify({"ok": False, "error": "Missing favorite flag"}), 400

    webinars = load_data()
    webcast_id = None
    if raw_webcast_id is not None:
        webcast_id = str(raw_webcast_id)
    else:
        object_id = str(raw_object_id) if raw_object_id is not None else None
        webcast_id = resolve_webcast_id(
            webinars=webinars,
            webcast_id=None,
            object_id=object_id,
        )

    if not webcast_id:
        return jsonify({"ok": False, "error": "webcastId could not be resolved"}), 400

    state = load_state()
    st = state.get(webcast_id, {})
    st["favorite"] = bool(favorite)
    state[webcast_id] = st
    save_state(state)

    return jsonify({"ok": True})


if __name__ == "__main__":
    # Dev server; in prod you use gunicorn: gunicorn -b 0.0.0.0:8411 'app:app'
    app.run(host="0.0.0.0", port=8411, debug=True)
