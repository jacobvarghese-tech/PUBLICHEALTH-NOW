


from __future__ import annotations

import json
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

from app.attachment import (
    clean_npi,
    clean_year,
    fields_from_attachment,
    parse_upload,
)
from app.extract import MISSING_KEY_MESSAGE
from app.search_index import find_rows, list_scores, lookup, open_db, score_for
from app.page_logic import (
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
SHARE_PATH = REPO_ROOT / "models" / "blend_shares.json"
HELD_TOP_1 = "26/48"
HELD_TOP_5 = "26/48"
ROLLED_DIR = REPO_ROOT / "data" / "paper_rolled"
INDEX_PATH = APP_DIR / "data" / "search.duckdb"
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

_state: dict = {}
_local = threading.local()


def missing_files() -> list[str]:
    
    missing = []
    if not MODEL_PATH.is_file():
        missing.append(str(MODEL_PATH.relative_to(REPO_ROOT)))
    for year in YEARS:
        path = ROLLED_DIR / f"{year}.csv"
        if not path.is_file():
            missing.append(str(path.relative_to(REPO_ROOT)))
    return missing


def load_model() -> tuple[object, list[str]]:


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
    
    if is_blank(value):
        return np.nan
    try:
        return float(str(value).strip())
    except ValueError:
        return np.nan


def paper_frame(row: dict) -> pd.DataFrame:
    
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
    
    left = model.left.score_frame(frame)
    right = model.right.score_frame(frame)
    return np.maximum(left, right)


def score_row(row: dict, model, columns: list[str]) -> float | None:
    
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


def connect():
    connection = getattr(_local, "connection", None)
    if connection is None:
        connection = open_db(INDEX_PATH)
        _local.connection = connection
    return connection


def ensure_index() -> None:
    if not INDEX_PATH.is_file():
        raise SystemExit(f"Missing search index: {INDEX_PATH}")
    connection = open_db(INDEX_PATH)
    years = {
        int(year)
        for (year,) in connection.execute("SELECT DISTINCT year_key FROM rows").fetchall()
    }
    connection.close()
    missing = [year for year in YEARS if year not in years]
    if missing:
        raise SystemExit(f"Search index is missing years: {missing}")
    _local.connection = None


def lookup_row(year: int, npi: str) -> dict | None:
    return lookup(connect(), year, npi.strip(), PAPER_NUMERIC)


def search_year(year: int, query: str, limit: int | None = None) -> tuple[list[dict], int]:
    return find_rows(connect(), year, query, PAPER_NUMERIC, limit)


def ensure_year_scores() -> dict[str, list[float]]:
    connection = connect()
    stored = {str(year): list_scores(connection, year) for year in YEARS}
    for year, scores in stored.items():
        print(f"scores year={year} rows={len(scores)}", flush=True)
    _state["scores"] = stored
    _state["scores_2024"] = stored.get("2024", [])
    return stored


def score_lookup(npi: str, year: int = 2024) -> float | None:
    return score_for(connect(), year, npi)


def _demo_html() -> str:
    
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


    score = score_lookup(npi, year)
    scores = _state["scores"].get(str(year), [])
    rank = percentile_result(score, scores)
    payload["score"] = score
    payload["percentile"] = rank["percentile"]
    payload["outside_top_1"] = rank["outside_top_1"]
    payload["outside_top_5"] = rank["outside_top_5"]
    payload["percentile_text"] = format_percentile(rank, year)
    if score is not None:
        payload["stored_score"] = True
        payload["incomplete"] = False
    return payload


def forest_shares() -> dict:
    
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
    
    page = (APP_DIR / "about.html").read_text(encoding="utf-8")
    shares = forest_shares()
    top1 = shares.get("holdout_top_1") or HELD_TOP_1
    top5 = shares.get("holdout_top_5") or HELD_TOP_5
    sentence = (
        f"The saved blend's recorded 2024 top 1% count is {top1}, "
        f"and its recorded 2024 top 5% count is {top5}."
    )
    page = page.replace("@@FOREST-SHARES@@", sentence)
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
            "Missing files. Put each named file in place, then start again.\n" + lines
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

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        path = parsed.path
        query = parse_qs(parsed.query)
        if path == "/favicon.ico":
            self._send(204, b"", "image/x-icon")
            return
        if path in ("/", "/index.html"):
            self._send(200, page_html("database.html", "database").encode("utf-8"), "text/html; charset=utf-8")
            return
        if path == "/model":
            self._send(200, page_html("model.html", "model").encode("utf-8"), "text/html; charset=utf-8")
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
            elif target.suffix == ".woff2":
                kind = "font/woff2"
            elif target.suffix == ".woff":
                kind = "font/woff"
            elif target.suffix == ".ttf":
                kind = "font/ttf"
            elif target.suffix == ".svg":
                kind = "image/svg+xml"
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

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        length = int(self.headers.get("Content-Length") or "0")
        raw = self.rfile.read(length)
        if parsed.path == "/api/attachment":
            self._attachment(self.headers.get("Content-Type") or "", raw, parse_qs(parsed.query))
            return
        if parsed.path != "/api/score":
            self._send(404, b"missing", "text/plain")
            return
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
        payload["outside_top_1"] = rank["outside_top_1"]
        payload["outside_top_5"] = rank["outside_top_5"]
        payload["percentile_text"] = format_percentile(rank, 2024)
        self._json(payload)

    def _attachment(self, content_type: str, raw: bytes, query: dict) -> None:
        try:
            filename, payload = parse_upload(content_type, raw)
            npi = clean_npi((query.get("npi") or [""])[0])
            year = clean_year((query.get("year") or [""])[0])
            fields = fields_from_attachment(filename, payload, npi, year)
        except ValueError as error:
            self._json({"error": str(error)}, status=400)
            return
        except RuntimeError as error:
            message = str(error)
            status = 503 if message == MISSING_KEY_MESSAGE else 502
            self._json({"error": message}, status=status)
            return
        except Exception:
            self._json({"error": "the attachment was not read"}, status=502)
            return
        missing = [name for name, value in fields.items() if value is None]
        self._json({"npi": npi, "year": year, "fields": fields, "missing": missing})


def page_html(fragment_name: str, current: str) -> str:
    shell = (APP_DIR / "shell.html").read_text(encoding="utf-8")
    fragment = (APP_DIR / fragment_name).read_text(encoding="utf-8")
    if current == "database":
        fragment = fragment.replace("<!--DEMOS-->", _demo_html())
    page = shell.replace("<!--PAGE-->", fragment)
    page = page.replace(f'data-page="{current}"', f'data-page="{current}" aria-current="page"')
    return page


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
