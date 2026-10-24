"""Local server for Medicare Fraud Flagger.

Loads models/candidates/blend_357_247.joblib and scores a typed row. A
static file server cannot do that. Paper-rolled tables stay on the server.
Search by name, city, or NPI for 2018-2024 returns a percentile. The two
2024 demo labs and the about-page shares are HTTP responses from this program.
"""

from __future__ import annotations

import json
import sqlite3
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import joblib
import numpy as np
import pandas as pd

APP_DIR = Path(__file__).resolve().parent
REPO_ROOT = APP_DIR.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
if str(REPO_ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "scripts"))

from app.page_logic import (  # noqa: E402
    DEMO_NPIS,
    FEATURE_FIELDS,
    PAPER_NUMERIC,
    RESEMBLANCE,
    YEARS,
    format_percentile,
    is_blank,
    is_incomplete,
    missing_features,
    percentile_result,
)
MODEL_PATH = REPO_ROOT / "models" / "candidates" / "blend_357_247.joblib"
SHARE_PATH = REPO_ROOT / "models" / "model_island_db.json"
HELD_TOP_1 = "26/48"
HELD_TOP_5 = "26/48"
ROLLED_DIR = REPO_ROOT / "data" / "paper_rolled"
INDEX_PATH = APP_DIR / "data" / "search.sqlite"
ZIP_PATH = APP_DIR / "data" / "zip_latlon.json"
READ_COLUMNS = (
    "NPI",
    "Name",
    "City",
    "State",
    "ZIP",
    "Specialty",
    "Gender",
    "Year",
    *PAPER_NUMERIC,
)
SOURCE_COLUMNS = {
    "NPI": "npi",
    "Name": "name",
    "City": "city",
    "State": "state",
    "ZIP": "zip",
    "Specialty": "provider_type",
    "Gender": "nppes_provider_gender",
    "Year": "year",
}

_state: dict = {}
_local = threading.local()


def missing_files() -> list[str]:
    """Files a fresh clone does not have. DATA.md says where to download them."""
    missing = []
    if not MODEL_PATH.is_file():
        missing.append(str(MODEL_PATH.relative_to(REPO_ROOT)))
    for year in YEARS:
        path = ROLLED_DIR / f"{year}.csv"
        if not path.is_file():
            missing.append(str(path.relative_to(REPO_ROOT)))
    return missing


def load_model() -> tuple[object, list[str]]:
    """Load the saved blend. Both forests are inside that one file.

    save_blend.py wrote MaxRankBlend while that script was __main__. The
    class has to sit on this process's __main__ before joblib can read it.
    """
    import __main__

    from scripts.save_blend import MaxRankBlend

    setattr(__main__, "MaxRankBlend", MaxRankBlend)
    payload = joblib.load(MODEL_PATH)
    columns = list(payload.left.columns)
    return payload, columns


def load_zip_table() -> dict[str, list[float]]:
    if not ZIP_PATH.is_file():
        return {}
    return json.loads(ZIP_PATH.read_text(encoding="utf-8"))


def pin_for(row: dict, zips: dict[str, list[float]]) -> dict | None:
    """Place a pin from city, state, and ZIP. ZIP supplies the coordinates."""
    zipcode = str(row.get("ZIP") or "").strip()[:5]
    point = zips.get(zipcode)
    if point is None:
        return None
    return {
        "lat": point[0],
        "lon": point[1],
        "city": row.get("City") or "",
        "state": row.get("State") or "",
        "zip": zipcode,
        "npi": row.get("NPI") or "",
        "year": row.get("Year") or "",
    }


def blank_to_missing(value: object) -> float:
    """Leave a blank numeric feature missing. Do not fill it with zero."""
    if is_blank(value):
        return np.nan
    try:
        return float(str(value).strip())
    except ValueError:
        return np.nan


def paper_frame(row: dict) -> pd.DataFrame:
    """One typed row in the paper column names the forest was fit on."""
    data = {
        "provider_type": [str(row.get("Specialty") or "").strip()],
        "nppes_provider_gender": [str(row.get("Gender") or "").strip()],
        "npi": [str(row.get("NPI") or "")],
    }
    for name in PAPER_NUMERIC:
        value = row.get(name)
        data[name] = ["" if is_blank(value) else value]
    return pd.DataFrame(data)


def score_frame(model, frame: pd.DataFrame, columns: list[str]) -> np.ndarray:
    """Score rows with the same two-forest rank the blend uses on a year file."""
    left = model.left.score_frame(frame)
    right = model.right.score_frame(frame)
    return np.maximum(left, right)


def score_row(row: dict, model, columns: list[str]) -> float | None:
    """Score only when specialty, gender, and every paper summary are present."""
    if is_incomplete(row):
        return None
    frame = paper_frame(row)
    return float(score_frame(model, frame, columns)[0])


def row_payload(row: dict, zips: dict[str, list[float]]) -> dict:
    payload = {name: ("" if is_blank(row.get(name)) else str(row.get(name)).strip()) for name in READ_COLUMNS}
    payload["incomplete"] = is_incomplete(row)
    payload["missing"] = missing_features(row)
    payload["pin"] = pin_for(row, zips)
    payload["resemblance"] = RESEMBLANCE
    return payload


def _index_year(connection: sqlite3.Connection, year: int) -> None:
    path = ROLLED_DIR / f"{year}.csv"
    usecols = list(SOURCE_COLUMNS.values()) + list(PAPER_NUMERIC)
    frame = pd.read_csv(
        path,
        dtype=str,
        keep_default_na=False,
        encoding="utf-8",
        usecols=usecols,
    )
    frame = frame.rename(columns={source: name for name, source in SOURCE_COLUMNS.items()})
    frame["year_key"] = str(year)
    frame["name_key"] = frame["Name"].str.lower()
    frame["city_key"] = frame["City"].str.lower()
    frame["npi_key"] = frame["NPI"].str.strip()
    frame.to_sql("rows", connection, if_exists="append", index=False)


def ensure_index() -> None:
    """Build a search index under app/data. Does not write data/rolled/."""
    INDEX_PATH.parent.mkdir(parents=True, exist_ok=True)
    fresh = not INDEX_PATH.is_file() or INDEX_PATH.stat().st_size < 1000
    connection = sqlite3.connect(INDEX_PATH)
    connection.row_factory = sqlite3.Row
    if not fresh:
        count = connection.execute("SELECT COUNT(*) FROM rows").fetchone()[0]
        columns = {
            row[1]
            for row in connection.execute("PRAGMA table_info(rows)")
        }
        fresh = count < 1_000_000 or "Gender" not in columns or "line_srvc_cnt_mean" not in columns
    if fresh:
        connection.execute("DROP TABLE IF EXISTS rows")
        connection.execute("DROP TABLE IF EXISTS scores")
        _create_tables(connection)
        for year in YEARS:
            _index_year(connection, year)
            connection.commit()
        connection.execute("CREATE INDEX IF NOT EXISTS rows_npi ON rows(year_key, npi_key)")
        connection.execute("CREATE INDEX IF NOT EXISTS rows_city ON rows(year_key, city_key)")
        connection.commit()
    connection.close()
    _local.connection = None


def _create_tables(connection: sqlite3.Connection) -> None:
    columns = ", ".join(f'"{name}" TEXT' for name in READ_COLUMNS)
    connection.execute(
        f"CREATE TABLE rows ({columns}, year_key TEXT, name_key TEXT, city_key TEXT, npi_key TEXT)"
    )
    connection.execute(
        "CREATE TABLE scores (year_key TEXT, npi TEXT, score REAL, PRIMARY KEY (year_key, npi))"
    )


def connect() -> sqlite3.Connection:
    """One SQLite connection per thread. The index is read-only after boot."""
    connection = getattr(_local, "connection", None)
    if connection is None:
        connection = sqlite3.connect(INDEX_PATH)
        connection.row_factory = sqlite3.Row
        _local.connection = connection
    return connection


def lookup_row(year: int, npi: str) -> dict | None:
    connection = connect()
    found = connection.execute(
        "SELECT * FROM rows WHERE year_key = ? AND npi_key = ?",
        (str(year), npi.strip()),
    ).fetchone()
    if found is None:
        return None
    return {name: found[name] for name in READ_COLUMNS}


def search_year(year: int, query: str, limit: int | None = None) -> tuple[list[dict], int]:
    """Find stored rows by name, city, or NPI.

    A city query counts every stored row whose city contains the query.
    "Deerfield" includes Deerfield Beach. An exact shorter city must not
    hide a longer city that contains the same text. Name matches stay on
    a preview of 20 so a one-letter name search does not return the year.
    A caller may pass a smaller limit for a first paint. The count is the
    full city match, or the name preview length.
    """
    needle = (query or "").strip().lower()
    if needle == "":
        return [], 0
    connection = connect()
    if needle.isdigit() and len(needle) == 10:
        found = connection.execute(
            "SELECT * FROM rows WHERE year_key = ? AND npi_key = ?",
            (str(year), needle),
        ).fetchall()
        rows = [{name: item[name] for name in READ_COLUMNS} for item in found]
        return rows, len(rows)

    like = f"%{needle}%"
    city_total = connection.execute(
        "SELECT COUNT(*) FROM rows WHERE year_key = ? AND city_key LIKE ?",
        (str(year), like),
    ).fetchone()[0]
    if city_total:
        sql = """
            SELECT * FROM rows
            WHERE year_key = ? AND city_key LIKE ?
            ORDER BY city_key, name_key
        """
        params: tuple = (str(year), like)
        if limit is not None:
            sql += " LIMIT ?"
            params = (str(year), like, limit)
        city_rows = connection.execute(sql, params).fetchall()
        rows = [{name: item[name] for name in READ_COLUMNS} for item in city_rows]
        return rows, int(city_total)
    name_limit = 20 if limit is None else limit
    found = connection.execute(
        """
        SELECT * FROM rows
        WHERE year_key = ? AND (name_key LIKE ? OR npi_key LIKE ?)
        ORDER BY name_key
        LIMIT ?
        """,
        (str(year), like, like, name_limit),
    ).fetchall()
    rows = [{name: item[name] for name in READ_COLUMNS} for item in found]
    return rows, len(rows)


def ensure_year_scores() -> dict[str, list[float]]:
    """Score every 2018-2024 row once and keep the scores beside the search index."""
    connection = connect()
    model = _state["model"]
    columns = _state["columns"]
    stored: dict[str, list[float]] = {}
    for year in YEARS:
        expected = connection.execute(
            "SELECT COUNT(*) FROM rows WHERE year_key = ?",
            (str(year),),
        ).fetchone()[0]
        existing = connection.execute(
            "SELECT COUNT(*) FROM scores WHERE year_key = ?",
            (str(year),),
        ).fetchone()[0]
        if existing != expected or existing == 0:
            connection.execute("DELETE FROM scores WHERE year_key = ?", (str(year),))
            cursor = connection.execute(
                "SELECT * FROM rows WHERE year_key = ? ORDER BY npi_key",
                (str(year),),
            )
            batch: list[tuple[str, str, float]] = []
            while True:
                chunk = cursor.fetchmany(20000)
                if not chunk:
                    break
                records = [{name: item[name] for name in READ_COLUMNS} for item in chunk]
                frame = pd.DataFrame(
                    {
                        "provider_type": [row.get("Specialty") or "" for row in records],
                        "nppes_provider_gender": [row.get("Gender") or "" for row in records],
                        "npi": [row.get("NPI") or "" for row in records],
                        **{
                            name: [row.get(name) or "" for row in records]
                            for name in PAPER_NUMERIC
                        },
                    }
                )
                probabilities = score_frame(model, frame, columns)
                batch.extend(
                    (str(year), row["NPI"], float(score))
                    for row, score in zip(records, probabilities)
                )
                if len(batch) >= 20000:
                    connection.executemany(
                        "INSERT INTO scores (year_key, npi, score) VALUES (?, ?, ?)",
                        batch,
                    )
                    connection.commit()
                    batch.clear()
            if batch:
                connection.executemany(
                    "INSERT INTO scores (year_key, npi, score) VALUES (?, ?, ?)",
                    batch,
                )
                connection.commit()
        scores = [
            float(row[0])
            for row in connection.execute(
                "SELECT score FROM scores WHERE year_key = ? ORDER BY npi",
                (str(year),),
            )
        ]
        stored[str(year)] = scores
        print(f"scores year={year} rows={len(scores)}", flush=True)
    _state["scores"] = stored
    _state["scores_2024"] = stored.get("2024", [])
    return stored


def score_lookup(npi: str, year: int = 2024) -> float | None:
    connection = connect()
    found = connection.execute(
        "SELECT score FROM scores WHERE year_key = ? AND npi = ?",
        (str(year), npi.strip()),
    ).fetchone()
    if found is None:
        return None
    return float(found[0])


def _demo_html() -> str:
    """Put both 2024 percentiles in the served HTML, before any script runs."""
    parts = []
    for row in demo_payload():
        npi = row.get("npi") or row.get("NPI") or ""
        name = row.get("Name") or "Named lab"
        text = row.get("percentile_text") or "Percentile is not available."
        outside = " This result is outside the top 5%." if row.get("outside_top_5") else ""
        if outside and outside.strip() not in text:
            text = text + outside
        parts.append(
            f'<article class="demo-card" data-npi="{npi}">'
            f"<h3>{name} ({npi})</h3>"
            f"<p>{text} {RESEMBLANCE}</p>"
            "</article>"
        )
    return "".join(parts)


def attach_rank(payload: dict, year: int, npi: str) -> dict:
    """Add that year's stored forest percentile.

    A stored score is the score the page shows. It is not a typed row, so a
    blank gender does not mark the opened row incomplete or unscored.
    """
    score = score_lookup(npi, year)
    scores = _state["scores"].get(str(year), [])
    rank = percentile_result(score, scores)
    payload["score"] = score
    payload["percentile"] = rank["percentile"]
    payload["outside_top_5"] = rank["outside_top_5"]
    payload["percentile_text"] = format_percentile(rank, year)
    if score is not None:
        payload["stored_score"] = True
        payload["incomplete"] = False
    return payload


def forest_shares() -> dict:
    """Read the recorded 2024 counts from the blend ledger."""
    if not SHARE_PATH.is_file():
        return {"holdout_top_1": HELD_TOP_1, "holdout_top_5": HELD_TOP_5}
    payload = json.loads(SHARE_PATH.read_text(encoding="utf-8"))
    best = payload.get("best_confirm_top1")
    top1 = f"{best}/48" if best else HELD_TOP_1
    top5 = HELD_TOP_5
    for record in payload.get("candidates") or []:
        if record.get("spec") == payload.get("best_spec"):
            if record.get("confirm_top5"):
                top5 = f"{record['confirm_top5']}/48"
            break
    return {"holdout_top_1": top1, "holdout_top_5": top5}


def about_html() -> str:
    """Print the blend's recorded 2024 shares on the about page."""
    page = (APP_DIR / "about.html").read_text(encoding="utf-8")
    shares = forest_shares()
    top1 = shares.get("holdout_top_1") or HELD_TOP_1
    top5 = shares.get("holdout_top_5") or HELD_TOP_5
    sentence = (
        f"The saved blend's recorded 2024 top 1% count is {top1}, "
        f"and its recorded 2024 top 5% count is {top5}."
    )
    page = page.replace("<!--FOREST-SHARES-->", sentence)
    return page


def demo_payload() -> list[dict]:
    zips = _state["zips"]
    results = []
    for npi in DEMO_NPIS:
        row = lookup_row(2024, npi)
        if row is None:
            results.append({"npi": npi, "found": False, "resemblance": RESEMBLANCE})
            continue
        payload = row_payload(row, zips)
        payload["found"] = True
        attach_rank(payload, 2024, npi)
        results.append(payload)
    return results


def boot() -> None:
    missing = missing_files()
    if missing:
        lines = "\n".join(missing)
        raise SystemExit(
            "Missing files. DATA.md says where to download them.\n" + lines
        )
    model, columns = load_model()
    _state["model"] = model
    _state["columns"] = columns
    _state["zips"] = load_zip_table()
    ensure_index()
    ensure_year_scores()
    scored = sum(len(values) for values in _state["scores"].values())
    print(f"ready model={MODEL_PATH.name} scores={scored}", flush=True)


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt: str, *args) -> None:
        return

    def _send(self, status: int, body: bytes, content_type: str) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _json(self, payload: dict, status: int = 200) -> None:
        body = json.dumps(payload).encode("utf-8")
        self._send(status, body, "application/json; charset=utf-8")

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        path = parsed.path
        query = parse_qs(parsed.query)
        if path == "/favicon.ico":
            self._send(204, b"", "image/x-icon")
            return
        if path in ("/", "/index.html"):
            page = (APP_DIR / "index.html").read_text(encoding="utf-8")
            page = page.replace("<!--DEMOS-->", _demo_html())
            self._send(200, page.encode("utf-8"), "text/html; charset=utf-8")
            return
        if path == "/about.html":
            self._send(200, about_html().encode("utf-8"), "text/html; charset=utf-8")
            return
        if path.startswith("/static/"):
            target = (APP_DIR / path.removeprefix("/static/")).resolve()
            if APP_DIR.resolve() not in target.parents and target != APP_DIR.resolve():
                self._send(404, b"missing", "text/plain")
                return
            if not target.is_file():
                self._send(404, b"missing", "text/plain")
                return
            kind = "text/plain"
            if target.suffix == ".css":
                kind = "text/css"
            elif target.suffix == ".js":
                kind = "text/javascript"
            elif target.suffix == ".png":
                kind = "image/png"
            self._send(200, target.read_bytes(), kind)
            return
        if path == "/api/meta":
            self._json(
                {
                    "title": "Medicare Fraud Flagger",
                    "years": list(YEARS),
                    "features": list(FEATURE_FIELDS),
                    "resemblance": RESEMBLANCE,
                    "map_library": "Leaflet",
                }
            )
            return
        if path == "/api/demos":
            self._json({"rows": demo_payload(), "resemblance": RESEMBLANCE})
            return
        if path == "/api/search":
            year = int((query.get("year") or ["2024"])[0])
            text = (query.get("q") or [""])[0]
            raw_limit = (query.get("limit") or [""])[0]
            limit = int(raw_limit) if raw_limit.isdigit() else None
            found, total = search_year(year, text, limit)
            rows = []
            for row in found:
                payload = row_payload(row, _state["zips"])
                if str(year) in {str(item) for item in YEARS}:
                    attach_rank(payload, year, row.get("NPI") or "")
                rows.append(payload)
            self._json({"rows": rows, "total": total, "resemblance": RESEMBLANCE})
            return
        if path == "/api/row":
            year = int((query.get("year") or ["2024"])[0])
            npi = (query.get("npi") or [""])[0]
            row = lookup_row(year, npi)
            if row is None:
                self._json({"found": False, "resemblance": RESEMBLANCE}, status=404)
                return
            payload = row_payload(row, _state["zips"])
            payload["found"] = True
            if year in YEARS:
                attach_rank(payload, year, npi)
            self._json(payload)
            return
        self._send(404, b"missing", "text/plain")

    def do_POST(self) -> None:  # noqa: N802
        if urlparse(self.path).path != "/api/score":
            self._send(404, b"missing", "text/plain")
            return
        length = int(self.headers.get("Content-Length") or "0")
        raw = self.rfile.read(length)
        try:
            row = json.loads(raw.decode("utf-8") or "{}")
        except json.JSONDecodeError:
            self._json({"error": "bad json"}, status=400)
            return
        payload = row_payload(row, _state["zips"])
        payload["features"] = {
            name: None if is_blank(row.get(name)) else row.get(name)
            for name in FEATURE_FIELDS
        }
        if is_incomplete(row):
            payload["score"] = None
            payload["percentile"] = None
            payload["percentile_text"] = ""
            self._json(payload)
            return
        score = score_row(row, _state["model"], _state["columns"])
        rank = percentile_result(score, _state["scores"].get("2024", []))
        payload["score"] = score
        payload["percentile"] = rank["percentile"]
        payload["outside_top_5"] = rank["outside_top_5"]
        payload["percentile_text"] = format_percentile(rank, 2024)
        self._json(payload)


def make_server(host: str = "127.0.0.1", port: int = 8765) -> ThreadingHTTPServer:
    boot()
    return ThreadingHTTPServer((host, port), Handler)


def main() -> None:
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8765
    server = make_server(port=port)
    print(f"listening http://127.0.0.1:{port}/", flush=True)
    server.serve_forever()


if __name__ == "__main__":
    main()
