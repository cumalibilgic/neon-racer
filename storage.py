"""Platform-specific persistence for the player's score and settings."""

import json
import os
import sys
import tempfile

WEB = sys.platform == "emscripten"
KEY = "neon-racer-save"
SAVE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "save.json")


def _normalise(data):
    """Keep unknown fields, but make fields consumed by the game safe to use."""
    if not isinstance(data, dict):
        return {}

    normalised = dict(data)
    score = data.get("high_score", 0)
    normalised["high_score"] = score if type(score) is int and score >= 0 else 0

    coins = data.get("total_coins", 0)
    normalised["total_coins"] = coins if type(coins) is int and coins >= 0 else 0

    muted = data.get("muted", False)
    normalised["muted"] = muted if isinstance(muted, bool) else False
    return normalised


def load():
    try:
        if WEB:
            from platform import window
            raw = window.localStorage.getItem(KEY)
        else:
            if not os.path.exists(SAVE_PATH):
                return {}
            with open(SAVE_PATH, encoding="utf-8") as file:
                raw = file.read()
        return _normalise(json.loads(raw)) if raw else {}
    except Exception as error:
        # A damaged or inaccessible save should never prevent the game from starting.
        print("Kayıt okunamadı:", error)
        return {}


def save(data):
    temporary_path = None
    try:
        raw = json.dumps(data)
        if WEB:
            from platform import window
            window.localStorage.setItem(KEY, raw)
            return

        directory = os.path.dirname(SAVE_PATH)
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", dir=directory,
            prefix=".save-", suffix=".tmp", delete=False,
        ) as file:
            temporary_path = file.name
            file.write(raw)
            file.flush()
            os.fsync(file.fileno())
        os.replace(temporary_path, SAVE_PATH)
        temporary_path = None
    except Exception as error:
        print("Kayıt yazılamadı:", error)
    finally:
        if temporary_path and os.path.exists(temporary_path):
            try:
                os.remove(temporary_path)
            except OSError:
                pass
