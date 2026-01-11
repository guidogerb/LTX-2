from __future__ import annotations

import datetime


def now_iso() -> str:
    return (
        datetime.datetime.now(datetime.UTC)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "")
        + "Z"
    )
