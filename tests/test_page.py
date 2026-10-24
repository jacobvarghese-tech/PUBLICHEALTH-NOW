"""Shipped page helpers and the live server keep the step 7 contract."""

from __future__ import annotations

import json
import threading
import unittest
import urllib.parse
import urllib.request

from app.page_logic import (
    FEATURE_FIELDS,
    RESEMBLANCE,
    format_percentile,
    is_incomplete,
    missing_features,
    percentile_result,
    search_rows,
)


def _row(**overrides) -> dict:
    base = {name: "1" for name in FEATURE_FIELDS}
    base.update(
        {
            "NPI": "1111111111",
            "Name": "Prince Laboratories Limited Liability Company",
            "City": "Deerfield Beach",
            "State": "FL",
            "ZIP": "33441",
            "Year": "2024",
        }
    )
    base.update(overrides)
    return base


class PageLogicTest(unittest.TestCase):
    def test_blank_feature_stays_blank_and_marks_the_row_incomplete(self) -> None:
        row = _row(**{"line_srvc_cnt_mean": "", "Specialty": "Lab", "Gender": "F"})
        self.assertEqual(row["line_srvc_cnt_mean"], "")
        self.assertIn("line_srvc_cnt_mean", missing_features(row))
        self.assertTrue(is_incomplete(row))
        blank_gender = _row(Gender="")
        self.assertIn("Gender", missing_features(blank_gender))
        self.assertTrue(is_incomplete(blank_gender))
        stored = _row(Gender="", score=0.4, stored_score=True)
        self.assertEqual(stored["Gender"], "")
        self.assertIn("Gender", missing_features(stored))
        self.assertFalse(is_incomplete(stored))
        complete = _row()
        self.assertFalse(is_incomplete(complete))
        self.assertEqual(missing_features(complete), [])
        zero = _row(**{"Growth": "0"})
        self.assertFalse(is_incomplete(zero))

    def test_search_matches_name_city_or_npi(self) -> None:
        rows = [
            _row(NPI="1124725817", Name="Prince Laboratories Limited Liability Company", City="Deerfield Beach"),
            _row(NPI="1639879034", Name="Reliable Results Labs Inc", City="Deerfield Beach"),
            _row(NPI="9999999999", Name="Other Clinic", City="Miami"),
        ]
        by_name = search_rows(rows, "prince laboratories")
        self.assertEqual([row["NPI"] for row in by_name], ["1124725817"])
        by_city = search_rows(rows, "deerfield")
        self.assertEqual([row["NPI"] for row in by_city], ["1124725817", "1639879034"])
        by_npi = search_rows(rows, "1639879034")
        self.assertEqual([row["NPI"] for row in by_npi], ["1639879034"])
        self.assertEqual(search_rows(rows, "   "), [])

    def test_percentile_tie_at_cutoff_and_empty_year(self) -> None:
        scores = [0.1, 0.2, 0.3, 0.4, 0.5]
        low = percentile_result(0.1, scores)
        self.assertTrue(low["outside_top_5"])
        self.assertAlmostEqual(low["percentile"], 20.0)
        text = format_percentile(low)
        self.assertIn("outside the top 5%", text)
        self.assertIn("1/5", text)
        # Every score ties, so the 95th-percentile cutoff is that score.
        tied = percentile_result(0.5, [0.5, 0.5, 0.5, 0.5])
        self.assertFalse(tied["outside_top_5"])
        self.assertAlmostEqual(tied["percentile"], 100.0)
        empty = percentile_result(0.4, [])
        self.assertIsNone(empty["percentile"])
        self.assertIsNone(empty["outside_top_5"])
        self.assertIn("not available", format_percentile(empty))


def _page_files_present() -> bool:
    """The live page needs the saved blend and the rolled years. A clone does not."""
    from app.server import missing_files

    return not missing_files()


@unittest.skipUnless(
    _page_files_present(),
    "needs models/candidates/blend_357_247.joblib and data/paper_rolled/2018-2024.csv",
)
class CitySearchHttpTest(unittest.TestCase):
    """A city query must fill the form from a stored row past the first 20 names."""

    def test_deerfield_beach_returns_prince_laboratories(self) -> None:
        from app.server import Handler, boot
        from http.server import ThreadingHTTPServer

        boot()
        server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        port = server.server_address[1]
        try:
            url = (
                f"http://127.0.0.1:{port}/api/search?year=2024&q="
                + urllib.request.quote("Deerfield Beach")
            )
            with urllib.request.urlopen(url, timeout=600) as response:
                payload = json.loads(response.read().decode("utf-8"))
            row_url = f"http://127.0.0.1:{port}/api/row?year=2024&npi=1124725817"
            with urllib.request.urlopen(row_url, timeout=60) as response:
                opened = json.loads(response.read().decode("utf-8"))
        finally:
            server.shutdown()
            server.server_close()
        rows = payload["rows"]
        prince = [row for row in rows if row["NPI"] == "1124725817"]
        self.assertGreater(len(rows), 20)
        self.assertEqual(len(prince), 1)
        self.assertEqual(prince[0]["City"], "Deerfield Beach")
        self.assertEqual(prince[0]["Name"], "Prince Laboratories Limited Liability Company")
        self.assertEqual(opened["Specialty"], prince[0]["Specialty"])
        self.assertEqual(opened["line_srvc_cnt_mean"], prince[0]["line_srvc_cnt_mean"])
        self.assertIsInstance(opened["percentile"], float)
        self.assertFalse(opened["incomplete"])
        self.assertTrue(opened["stored_score"])
        self.assertIsInstance(opened["score"], float)
        self.assertEqual(
            prince[0]["resemblance"],
            "A high score is a resemblance, not a fraud finding.",
        )

    def test_partial_city_deerfield_includes_deerfield_beach(self) -> None:
        from app.server import Handler, boot
        from http.server import ThreadingHTTPServer

        boot()
        server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        port = server.server_address[1]
        try:
            url = (
                f"http://127.0.0.1:{port}/api/search?year=2024&q="
                + urllib.request.quote("Deerfield")
            )
            with urllib.request.urlopen(url, timeout=600) as response:
                payload = json.loads(response.read().decode("utf-8"))
        finally:
            server.shutdown()
            server.server_close()
        rows = payload["rows"]
        cities = {row["City"] for row in rows}
        prince = [row for row in rows if row["NPI"] == "1124725817"]
        self.assertIn("Deerfield Beach", cities)
        self.assertEqual(len(prince), 1)
        self.assertEqual(prince[0]["City"], "Deerfield Beach")
        self.assertGreater(len(rows), 83)
        self.assertTrue(all("deerfield" in row["City"].lower() for row in rows))


@unittest.skipUnless(
    _page_files_present(),
    "needs models/candidates/blend_357_247.joblib and data/paper_rolled/2018-2024.csv",
)
class Step7ServerTest(unittest.TestCase):
    """Drive the shipped Handler after boot. Do not reimplement the routes."""

    @classmethod
    def setUpClass(cls) -> None:
        from app.server import Handler, boot
        from http.server import ThreadingHTTPServer

        boot()
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.base = f"http://127.0.0.1:{cls.server.server_address[1]}"

    @classmethod
    def tearDownClass(cls) -> None:
        cls.server.shutdown()
        cls.server.server_close()

    def _get(self, path: str) -> tuple[int, bytes]:
        with urllib.request.urlopen(self.base + path, timeout=120) as response:
            return response.status, response.read()

    def _get_json(self, path: str) -> dict:
        status, body = self._get(path)
        self.assertEqual(status, 200)
        return json.loads(body.decode("utf-8"))

    def _post_json(self, path: str, payload: dict) -> dict:
        request = urllib.request.Request(
            self.base + path,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=120) as response:
            self.assertEqual(response.status, 200)
            return json.loads(response.read().decode("utf-8"))

    def test_home_is_one_screen_with_features_and_years(self) -> None:
        status, body = self._get("/")
        self.assertEqual(status, 200)
        page = body.decode("utf-8")
        self.assertIn('id="form-pane"', page)
        self.assertIn('id="browser-pane"', page)
        for name in FEATURE_FIELDS:
            self.assertIn(f'name="{name}"', page)
        for year in (2018, 2019, 2020, 2021, 2022, 2023, 2024):
            self.assertIn(f"<option>{year}</option>" if year != 2024 else f"<option selected>{year}</option>", page)
        self.assertIn("1124725817", page)
        self.assertIn("1639879034", page)
        self.assertIn(RESEMBLANCE, page)

    def test_about_names_the_disclosure(self) -> None:
        status, body = self._get("/about.html")
        self.assertEqual(status, 200)
        page = body.decode("utf-8")
        for token in (
            "For the demo",
            "Medicare Fraud Flagger",
            "Written answers",
            "1124725817",
            "1639879034",
            "Grok",
            "CMS",
            "LEIE",
            "blend_357_247.joblib",
            "RandomForest",
            "Leaflet",
            "2019",
            "2020",
            "2021",
            "2022",
            "2023",
            "1270",
            "11/48",
            "18/48",
            "at least 100 events",
            "not a precise estimate",
        ):
            self.assertIn(token, page)

    def test_name_city_and_npi_search_open_the_same_features(self) -> None:
        by_name = self._get_json(
            "/api/search?year=2024&q=" + urllib.parse.quote("Prince Laboratories")
        )
        by_city = self._get_json(
            "/api/search?year=2024&q=" + urllib.parse.quote("Deerfield Beach")
        )
        by_npi = self._get_json("/api/search?year=2024&q=1124725817")
        self.assertEqual(by_name["resemblance"], RESEMBLANCE)
        self.assertEqual(by_city["resemblance"], RESEMBLANCE)
        self.assertEqual(by_npi["resemblance"], RESEMBLANCE)
        name_row = next(row for row in by_name["rows"] if row["NPI"] == "1124725817")
        city_row = next(row for row in by_city["rows"] if row["NPI"] == "1124725817")
        npi_row = by_npi["rows"][0]
        self.assertEqual(npi_row["NPI"], "1124725817")
        opened = self._get_json("/api/row?year=2024&npi=1124725817")
        self.assertTrue(opened["found"])
        self.assertEqual(opened["resemblance"], RESEMBLANCE)
        for name in FEATURE_FIELDS:
            self.assertEqual(opened[name], name_row[name])
            self.assertEqual(opened[name], city_row[name])
            self.assertEqual(opened[name], npi_row[name])
        pin = opened["pin"]
        self.assertEqual(pin["npi"], "1124725817")
        self.assertEqual(pin["city"], opened["City"])
        self.assertEqual(pin["state"], opened["State"])
        self.assertEqual(pin["zip"], opened["ZIP"])
        self.assertIsInstance(pin["lat"], float)
        self.assertIsInstance(pin["lon"], float)
        reopened = self._get_json(f"/api/row?year=2024&npi={pin['npi']}")
        self.assertEqual(reopened["NPI"], opened["NPI"])
        for name in FEATURE_FIELDS:
            self.assertEqual(reopened[name], opened[name])

    def test_blank_feature_stays_blank_on_the_score_route(self) -> None:
        payload = {name: "1" for name in FEATURE_FIELDS}
        payload["Specialty"] = "Clinical Laboratory"
        payload["Gender"] = "F"
        payload["line_srvc_cnt_mean"] = ""
        scored = self._post_json("/api/score", payload)
        self.assertIsNone(scored["features"]["line_srvc_cnt_mean"])
        self.assertEqual(scored["line_srvc_cnt_mean"], "")
        self.assertIsNone(scored["score"])
        self.assertTrue(scored["incomplete"])
        self.assertIn("line_srvc_cnt_mean", scored["missing"])
        self.assertEqual(scored["resemblance"], RESEMBLANCE)
        blank_gender = {name: "1" for name in FEATURE_FIELDS}
        blank_gender["Specialty"] = "Clinical Laboratory"
        blank_gender["Gender"] = ""
        typed = self._post_json("/api/score", blank_gender)
        self.assertEqual(typed["Gender"], "")
        self.assertIsNone(typed["features"]["Gender"])
        self.assertIsNone(typed["score"])
        self.assertIsNone(typed["percentile"])
        self.assertTrue(typed["incomplete"])
        self.assertIn("Gender", typed["missing"])

    def test_opened_2024_labs_keep_stored_percentiles(self) -> None:
        """Organizations have blank gender. Opening them still shows the forest score."""
        for npi, name in (
            ("1124725817", "Prince Laboratories Limited Liability Company"),
            ("1639879034", "Reliable Results Labs Inc"),
        ):
            opened = self._get_json(f"/api/row?year=2024&npi={npi}")
            self.assertTrue(opened["found"])
            self.assertEqual(opened["Name"], name)
            self.assertEqual(opened["Gender"], "")
            self.assertIn("Gender", opened["missing"])
            self.assertFalse(opened["incomplete"])
            self.assertTrue(opened["stored_score"])
            self.assertIsInstance(opened["score"], float)
            self.assertIsInstance(opened["percentile"], float)
            self.assertIn("2024 percentile", opened["percentile_text"])
            self.assertEqual(opened["resemblance"], RESEMBLANCE)
            searched = self._get_json(f"/api/search?year=2024&q={npi}")
            row = searched["rows"][0]
            self.assertEqual(row["NPI"], npi)
            self.assertEqual(row["percentile"], opened["percentile"])
            self.assertFalse(row["incomplete"])
            self.assertTrue(row["stored_score"])

    def test_both_demo_percentiles_are_numeric(self) -> None:
        demos = self._get_json("/api/demos")
        self.assertEqual(demos["resemblance"], RESEMBLANCE)
        by_npi = {row["NPI"]: row for row in demos["rows"]}
        status, body = self._get("/")
        self.assertEqual(status, 200)
        page = body.decode("utf-8")
        for npi in ("1124725817", "1639879034"):
            row = by_npi[npi]
            self.assertIsInstance(row["percentile"], float)
            self.assertIn("2024 percentile", row["percentile_text"])
            self.assertEqual(row["resemblance"], RESEMBLANCE)
            card = page.split(f'data-npi="{npi}"', 1)[1].split("</article>", 1)[0]
            self.assertIn(npi, card)
            self.assertIn("2024 percentile:", card)
            self.assertIn(RESEMBLANCE, card)
            if row["outside_top_5"]:
                self.assertIn("outside the top 5%", row["percentile_text"])
                self.assertIn("outside the top 5%", card)
            else:
                self.assertNotIn("outside the top 5%", row["percentile_text"])
                self.assertNotIn("outside the top 5%", card)


if __name__ == "__main__":
    unittest.main()
