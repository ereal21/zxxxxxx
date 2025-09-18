
import json, os, threading
from pathlib import Path

_CONSENT_FILE = Path(os.environ.get("CONSENT_FILE", "data/consent.json"))
_LOCK = threading.Lock()

def _ensure_file():
    if not _CONSENT_FILE.parent.exists():
        _CONSENT_FILE.parent.mkdir(parents=True, exist_ok=True)
    if not _CONSENT_FILE.exists():
        _CONSENT_FILE.write_text("[]")

def get_all():
    _ensure_file()
    try:
        return set(json.loads(_CONSENT_FILE.read_text()))
    except Exception:
        return set()

def is_opted_in(user_id: int) -> bool:
    return int(user_id) in get_all()

def opt_in(user_id: int) -> None:
    _ensure_file()
    with _LOCK:
        s = get_all()
        s.add(int(user_id))
        _CONSENT_FILE.write_text(json.dumps(sorted(s)))

def opt_out(user_id: int) -> None:
    _ensure_file()
    with _LOCK:
        s = get_all()
        if int(user_id) in s:
            s.remove(int(user_id))
        _CONSENT_FILE.write_text(json.dumps(sorted(s)))
