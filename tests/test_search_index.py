from __future__ import annotations
import tempfile
import unittest
from pathlib import Path
from app.search_index import (add_scores, find_rows, list_scores, load_year, lookup, make_tables, open_db, score_for)
NUMERIC = ('line_srvc_cnt_mean',)

def _csv(folder: 'Path') -> 'Path':
    path = folder / '2024.csv'
    path.write_text('\n'.join(['provider_type,npi,nppes_provider_gender,year,name,city,state,zip,line_srvc_cnt_mean', 'Clinical Laboratory,1124725817,,2024,Prince Laboratories,Deerfield Beach,FL,33441,12', 'Internal Medicine,1999999999,M,2024,Ada Example,Deerfield,FL,33442,3']), encoding='utf-8')
    return path

class SearchIndexTest(unittest.TestCase):
    def test_city_query_keeps_the_longer_city(self) -> 'None':
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            conn = open_db(folder / 'search.duckdb')
            make_tables(conn, NUMERIC)
            load_year(conn, 2024, _csv(folder), NUMERIC)
            rows, total = find_rows(conn, 2024, 'deerfield', NUMERIC)
            self.assertEqual(total, 2)
            self.assertEqual({row['City'] for row in rows}, {'Deerfield Beach', 'Deerfield'})
            prince = lookup(conn, 2024, '1124725817', NUMERIC)
            self.assertEqual(prince['Name'], 'Prince Laboratories')
            self.assertEqual(prince['line_srvc_cnt_mean'], '12')
            self.assertEqual(find_rows(conn, 2024, '  ', NUMERIC), ([], 0))
            conn.close()

    def test_score_table_round_trip(self) -> 'None':
        with tempfile.TemporaryDirectory() as tmp:
            conn = open_db(Path(tmp) / 'search.duckdb')
            make_tables(conn, NUMERIC)
            add_scores(conn, [('2024', '1124725817', 0.25)])
            self.assertEqual(score_for(conn, 2024, '1124725817'), 0.25)
            self.assertEqual(list_scores(conn, 2024), [0.25])
            conn.close()
        if __name__ == '__main__':
            unittest.main()


