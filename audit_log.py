"""
Audit log — tracks all AI actions performed in the app.
Stored in memory and optionally saved to data/audit_log.json.
"""

import json
import os
from datetime import datetime

_LOG: list[dict] = []
_LOG_FILE = os.path.join(os.path.dirname(__file__), "data", "audit_log.json")


def log_action(action: str, model_id: str = None, category: str = None,
               input_summary: str = "", output_summary: str = "",
               data_sources: list = None):
    """Record an AI action."""
    entry = {
        "timestamp":      datetime.now().isoformat(),
        "action":         action,
        "model_id":       model_id or "default",
        "category":       category or "",
        "input_summary":  input_summary[:200],
        "output_summary": output_summary[:200],
        "data_sources":   data_sources or [],
    }
    _LOG.append(entry)
    # Auto-save
    try:
        os.makedirs(os.path.dirname(_LOG_FILE), exist_ok=True)
        with open(_LOG_FILE, "w") as f:
            json.dump(_LOG, f, indent=2)
    except Exception:
        pass
    return entry


def get_log() -> list[dict]:
    """Return the full audit log."""
    return list(_LOG)


def load_log():
    """Load audit log from disk if it exists."""
    global _LOG
    if os.path.exists(_LOG_FILE):
        try:
            with open(_LOG_FILE, "r") as f:
                _LOG = json.load(f)
        except Exception:
            _LOG = []


# Load on import
load_log()
