"""Check the pages a judge will open. Edit only files in app/.

The contest package still needs a public video and a portal submit. This
check keeps the demo lines and the six written answers on the about page,
and confirms the local server can open the two named 2024 labs.
"""

from __future__ import annotations

import sys
import urllib.parse
import urllib.request
from pathlib import Path

APP_DIR = Path(__file__).resolve().parent
ABOUT = APP_DIR / "about.html"
HOME = APP_DIR / "index.html"
BASE = "http://127.0.0.1:8765"

REQUIRED = (
    "Medicare Fraud Flagger",
    "For the demo",
    "Written answers",
    "1124725817",
    "1639879034",
    "Grok",
    "Leaflet",
    "A high score is a resemblance, not a fraud finding.",
)


def missing_on_disk() -> list[str]:
    about = ABOUT.read_text(encoding="utf-8")
    home = HOME.read_text(encoding="utf-8")
    gaps = [token for token in REQUIRED if token not in about]
    if "Prince Laboratories" not in home or "Reliable Results Labs" not in home:
        gaps.append("home lab links")
    return gaps


def server_gaps() -> list[str]:
    gaps = []
    try:
        with urllib.request.urlopen(BASE + "/about.html", timeout=10) as response:
            page = response.read().decode("utf-8")
        gaps.extend(token for token in REQUIRED if token not in page)
        for npi in ("1124725817", "1639879034"):
            query = urllib.parse.urlencode({"year": "2024", "q": npi})
            with urllib.request.urlopen(BASE + "/api/search?" + query, timeout=30) as response:
                body = response.read().decode("utf-8")
            if npi not in body:
                gaps.append(npi)
    except OSError as error:
        gaps.append(f"server {error}")
    return gaps


def main() -> None:
    gaps = missing_on_disk() + server_gaps()
    if gaps:
        print("GAPS " + ", ".join(gaps), flush=True)
        sys.exit(1)
    print("READY about page and two 2024 labs", flush=True)


if __name__ == "__main__":
    main()
