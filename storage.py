"""
Penyimpanan data sederhana pakai file JSON.
Menyimpan: daftar admin, owner, dan status online (last seen) tiap user.
"""

import json
import os
import time
from threading import Lock

DATA_FILE = os.path.join(os.path.dirname(__file__), "bot_data.json")
_lock = Lock()


def _default_data():
    return {"owner": None, "admins": [], "online": {}}


def _load():
    if not os.path.exists(DATA_FILE):
        return _default_data()
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return _default_data()


def _save(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def init_owner(owner_id: int):
    with _lock:
        data = _load()
        if data["owner"] is None:
            data["owner"] = owner_id
            if owner_id not in data["admins"]:
                data["admins"].append(owner_id)
            _save(data)


def is_owner(user_id: int) -> bool:
    data = _load()
    return data.get("owner") == user_id


def is_admin(user_id: int) -> bool:
    data = _load()
    return user_id == data.get("owner") or user_id in data.get("admins", [])


def add_admin(user_id: int) -> bool:
    with _lock:
        data = _load()
        if user_id in data["admins"]:
            return False
        data["admins"].append(user_id)
        _save(data)
        return True


def remove_admin(user_id: int) -> bool:
    with _lock:
        data = _load()
        if user_id == data.get("owner"):
            return False
        if user_id not in data["admins"]:
            return False
        data["admins"].remove(user_id)
        _save(data)
        return True


def list_admins() -> list:
    data = _load()
    return data.get("admins", [])


def touch_online(user_id: int, username: str = ""):
    with _lock:
        data = _load()
        data.setdefault("online", {})[str(user_id)] = {
            "last_seen": time.time(),
            "username": username or "",
        }
        _save(data)


def get_online(threshold_seconds: int = 300) -> list:
    data = _load()
    now = time.time()
    result = []
    for uid, info in data.get("online", {}).items():
        if now - info.get("last_seen", 0) <= threshold_seconds:
            result.append({"id": int(uid), "username": info.get("username", "")})
    return result
