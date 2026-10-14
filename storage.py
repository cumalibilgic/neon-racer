"""Kalıcı kayıt: tarayıcıda localStorage, bilgisayarda save.json. Platforma özgü kayıt kodu burada toplanır."""

import json
import os
import sys

WEB = sys.platform == "emscripten"
KEY = "neon-racer-save"
SAVE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "save.json")


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
        data = json.loads(raw) if raw else {}
        return data if isinstance(data, dict) else {}
    except Exception as error:
        # Bozuk ya da okunamayan kayıt oyunu durdurmamalı; sıfırdan başlanır
        print("Kayıt okunamadı:", error)
        return {}


def save(data):
    raw = json.dumps(data)
    try:
        if WEB:
            from platform import window
            window.localStorage.setItem(KEY, raw)
        else:
            with open(SAVE_PATH, "w", encoding="utf-8") as file:
                file.write(raw)
    except Exception as error:
        print("Kayıt yazılamadı:", error)
