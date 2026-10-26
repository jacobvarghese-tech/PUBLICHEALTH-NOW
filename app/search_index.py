from __future__ import annotations
from pathlib import Path
import duckdb
import pandas as pd
LABELS = ('NPI', 'Name', 'City', 'State', 'ZIP', 'Specialty', 'Gender', 'Year')
FROM_CSV = {'NPI': 'npi', 'Name': 'name', 'City': 'city', 'State': 'state', 'ZIP': 'zip', 'Specialty': 'provider_type', 'Gender': 'nppes_provider_gender', 'Year': 'year'}

def open_db(path: 'Path', read_only: 'bool' = False) -> 'duckdb.DuckDBPyConnection':
    path.parent.mkdir(parents=True, exist_ok=True)
    return duckdb.connect(str(path), read_only=read_only)

def has_years(conn: 'duckdb.DuckDBPyConnection', years: 'tuple[int, ...]') -> 'bool':
    names = {row[0] for row in conn.execute('SHOW TABLES').fetchall()}
    if 'rows' not in names:
        return False
    found = {int(year) for (year,) in conn.execute('SELECT DISTINCT year_key FROM rows').fetchall()}
    return set(years).issubset(found)

def make_tables(conn: 'duckdb.DuckDBPyConnection', numeric: 'tuple[str, ...]') -> 'None':
    cols = ', '.join((f'"{name}" VARCHAR' for name in [*LABELS, *numeric]))
    conn.execute('DROP TABLE IF EXISTS rows')
    conn.execute('DROP TABLE IF EXISTS scores')
    conn.execute(f'CREATE TABLE rows ({cols}, year_key VARCHAR, name_key VARCHAR, city_key VARCHAR, npi_key VARCHAR)')
    conn.execute('CREATE TABLE scores (year_key VARCHAR, npi VARCHAR, score DOUBLE, PRIMARY KEY (year_key, npi))')

def load_year(conn: 'duckdb.DuckDBPyConnection', year: 'int', csv_path: 'Path', numeric: 'tuple[str, ...]') -> 'int':
    wanted = list(FROM_CSV.values()) + list(numeric)
    frame = pd.read_csv(csv_path, dtype=str, keep_default_na=False, encoding='utf-8', usecols=wanted)
    frame = frame.rename(columns={src: name for name, src in FROM_CSV.items()})
    frame['year_key'] = str(year)
    frame['name_key'] = frame['Name'].str.lower()
    frame['city_key'] = frame['City'].str.lower()
    frame['npi_key'] = frame['NPI'].str.strip()
    ordered = [*LABELS, *numeric, 'year_key', 'name_key', 'city_key', 'npi_key']
    frame = frame[ordered]
    conn.register('year_frame', frame)
    quoted = ', '.join((f'"{name}"' for name in ordered))
    conn.execute(f'INSERT INTO rows ({quoted}) SELECT {quoted} FROM year_frame')
    conn.unregister('year_frame')
    return len(frame)

def _row(item: 'tuple', numeric: 'tuple[str, ...]') -> 'dict':
    fields = *LABELS, *numeric
    if len(item) < len(fields):
        raise ValueError(f'row has {len(item)} values, expected {len(fields)}')
    return {fields[i]: item[i] for i in range(len(fields))}

def lookup(conn: 'duckdb.DuckDBPyConnection', year: 'int', npi: 'str', numeric: 'tuple[str, ...]') -> 'dict | None':
    found = conn.execute('SELECT * FROM rows WHERE year_key = ? AND npi_key = ?', [str(year), npi.strip()]).fetchone()
    if found is None:
        return
    return _row(found, numeric)

def find_rows(conn: 'duckdb.DuckDBPyConnection', year: 'int', query: 'str', numeric: 'tuple[str, ...]', limit: 'int | None'=None) -> 'tuple[list[dict], int]':
    needle = (query or '').strip().lower()
    if needle == '':
        return [], 0
    if needle.isdigit() and len(needle) == 10:
        hit = lookup(conn, year, needle, numeric)
        return [hit] if hit else [], 1 if hit else 0
    like = f'%{needle}%'
    city_total = conn.execute('SELECT COUNT(*) FROM rows WHERE year_key = ? AND city_key LIKE ?', [str(year), like]).fetchone()[0]
    if city_total:
        sql = 'SELECT * FROM rows WHERE year_key = ? AND city_key LIKE ? ORDER BY city_key, name_key'
        params = [str(year), like]
        if limit is not None:
            sql += ' LIMIT ?'
            params.append(limit)
        rows = [_row(item, numeric) for item in conn.execute(sql, params).fetchall()]
        return rows, int(city_total)
    name_limit = 20 if limit is None else limit
    found = conn.execute('SELECT * FROM rows WHERE year_key = ? AND (name_key LIKE ? OR npi_key LIKE ?) ORDER BY name_key LIMIT ?', [str(year), like, like, name_limit]).fetchall()
    rows = [_row(item, numeric) for item in found]
    return rows, len(rows)

def count_rows(conn: 'duckdb.DuckDBPyConnection', year: 'int') -> 'int':
    return int(conn.execute('SELECT COUNT(*) FROM rows WHERE year_key = ?', [str(year)]).fetchone()[0])

def count_scores(conn: 'duckdb.DuckDBPyConnection', year: 'int') -> 'int':
    return int(conn.execute('SELECT COUNT(*) FROM scores WHERE year_key = ?', [str(year)]).fetchone()[0])

def clear_scores(conn: 'duckdb.DuckDBPyConnection', year: 'int') -> 'None':
    conn.execute('DELETE FROM scores WHERE year_key = ?', [str(year)])

def add_scores(conn: 'duckdb.DuckDBPyConnection', batch: 'list[tuple[str, str, float]]') -> 'None':
    conn.executemany('INSERT INTO scores (year_key, npi, score) VALUES (?, ?, ?)', batch)

def list_scores(conn: 'duckdb.DuckDBPyConnection', year: 'int') -> 'list[float]':
    rows = conn.execute('SELECT score FROM scores WHERE year_key = ? ORDER BY npi', [str(year)]).fetchall()
    return [float(row[0]) for row in rows]

def scores_for(conn: 'duckdb.DuckDBPyConnection', year: 'int', npis: 'list[str]') -> 'dict[str, float]':
    cleaned = [npi.strip() for npi in npis if npi if npi.strip()]
    if not cleaned:
        return {}
    placeholders = ', '.join(('?' for _ in cleaned))
    found = conn.execute(f'SELECT npi, score FROM scores WHERE year_key = ? AND npi IN ({placeholders})', [str(year), *cleaned]).fetchall()
    return {str(npi): float(score) for npi, score in found}

def score_for(conn: 'duckdb.DuckDBPyConnection', year: 'int', npi: 'str') -> 'float | None':
    found = conn.execute('SELECT score FROM scores WHERE year_key = ? AND npi = ?', [str(year), npi.strip()]).fetchone()
    if found is None:
        return
    return float(found[0])

def missing_npis(conn: 'duckdb.DuckDBPyConnection', year: 'int', limit: 'int'=2000) -> 'list[str]':
    rows = conn.execute('\n        SELECT r.npi_key\n        FROM rows r\n        ANTI JOIN scores s ON s.year_key = r.year_key AND s.npi = r.npi_key\n        WHERE r.year_key = ?\n        ORDER BY r.npi_key\n        LIMIT ?\n        ', [str(year), limit]).fetchall()
    return [row[0] for row in rows]

def rows_for_npis(conn: 'duckdb.DuckDBPyConnection', year: 'int', npis: 'list[str]', numeric: 'tuple[str, ...]') -> 'list[dict]':
    if not npis:
        return []
    placeholders = ', '.join(('?' for _ in npis))
    found = conn.execute(f'SELECT * FROM rows WHERE year_key = ? AND npi_key IN ({placeholders})', [str(year), *npis]).fetchall()
    return [_row(item, numeric) for item in found]

def iter_rows(conn: 'duckdb.DuckDBPyConnection', year: 'int', numeric: 'tuple[str, ...]', size: 'int'=5000):
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM rows WHERE year_key = ? ORDER BY npi_key', [str(year)])
    while True:
        chunk = cursor.fetchmany(size)
        if not chunk:
            return
        yield [_row(item, numeric) for item in chunk]

