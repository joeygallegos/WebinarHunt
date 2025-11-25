#!/usr/bin/env python3
# app.py

import json
import os
from typing import Any, Dict, List

from flask import Flask, jsonify, render_template, request

STATE_FILE = "state.json"

app = Flask(__name__)


def load_state() -> Dict[str, Any]:
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


@app.route("/")
def index():
    state = load_state()
    webinars: List[Dict[str, Any]] = state.get("webinars", [])

    # Default missing flags to False so the UI doesn't explode
    for w in webinars:
        if "watched" not in w:
            w["watched"] = False
        if "favorite" not in w:
            w["favorite"] = False

    # Sort server-side by duration bucket then title
    webinars_sorted = sorted(
        webinars,
        key=lambda w: (
            w.get("duration_bucket", 999),
            w.get("duration_hours", 999.0),
            (w.get("title") or "").lower(),
        ),
    )

    return render_template("index.html", webinars=webinars_sorted)


@app.route("/api/toggle-watched", methods=["POST"])
def toggle_watched():
    data = request.get_json(force=True, silent=True) or {}
    object_id = data.get("objectID")
    watched = data.get("watched")

    if object_id is None or watched is None:
        return jsonify({"ok": False, "error": "Missing objectID/watched"}), 400

    state = load_state()
    changed = False
    for w in state.get("webinars", []):
        if w.get("objectID") == object_id:
            w["watched"] = bool(watched)
            changed = True
            break

    if changed:
        save_state(state)
        return jsonify({"ok": True})
    else:
        return jsonify({"ok": False, "error": "Webinar not found"}), 404


@app.route("/api/toggle-favorite", methods=["POST"])
def toggle_favorite():
    data = request.get_json(force=True, silent=True) or {}
    object_id = data.get("objectID")
    favorite = data.get("favorite")

    if object_id is None or favorite is None:
        return jsonify({"ok": False, "error": "Missing objectID/favorite"}), 400

    state = load_state()
    changed = False
    for w in state.get("webinars", []):
        if w.get("objectID") == object_id:
            w["favorite"] = bool(favorite)
            changed = True
            break

    if changed:
        save_state(state)
        return jsonify({"ok": True})
    else:
        return jsonify({"ok": False, "error": "Webinar not found"}), 404


@app.route("/api/webinars")
def api_webinars():
    state = load_state()
    return jsonify(state.get("webinars", []))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8411)
