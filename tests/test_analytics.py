import json
import unittest
import urllib.error
import urllib.parse
import urllib.request

BASE_URL = "http://localhost:8000"


class TestAnalyticsRoutes(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Vérifier que le serveur est bien démarré
        try:
            req = urllib.request.urlopen(f"{BASE_URL}/health", timeout=5)
            assert req.status == 200
        except Exception as e:
            raise RuntimeError(f"Le serveur sur {BASE_URL} n'est pas joignable: {e}")

    def _get(self, path: str, params: dict = None):
        url = f"{BASE_URL}/api/v1/analytics{path}"
        if params:
            url += "?" + urllib.parse.urlencode({k: v for k, v in params.items() if v is not None})
        try:
            req = urllib.request.Request(url)
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                return resp.status, data
        except urllib.error.HTTPError as e:
            try:
                body = json.loads(e.read().decode("utf-8"))
            except Exception:
                body = e.read().decode("utf-8")
            return e.code, body

    # -----------------------------------------------------------------------
    # 1. Formulas Count
    # -----------------------------------------------------------------------
    def test_formulas_count_default(self):
        status, data = self._get("/formulas/count")
        self.assertEqual(status, 200)
        self.assertIn("total", data)
        self.assertIn("group_by", data)
        self.assertIn("data", data)
        self.assertEqual(data["group_by"], "month")
        self.assertIsInstance(data["data"], list)

    def test_formulas_count_granularities(self):
        for gb in ("day", "month", "year", "DAY", "Month", "YEAR "):
            status, data = self._get("/formulas/count", {"group_by": gb})
            self.assertEqual(status, 200, f"Failed for group_by={gb}")
            self.assertEqual(data["group_by"], gb.strip().lower())

    def test_formulas_count_invalid_group_by(self):
        status, data = self._get("/formulas/count", {"group_by": "decade"})
        self.assertEqual(status, 400)
        self.assertIn("group_by doit être", data["detail"])

    def test_formulas_count_date_filter(self):
        status, data = self._get(
            "/formulas/count",
            {"date_from": "2026-10-01", "date_to": "2026-10-15", "group_by": "day"},
        )
        self.assertEqual(status, 200)
        self.assertTrue(all("2026-10-" in item["period"] for item in data["data"]))

    def test_formulas_count_inverted_dates(self):
        status, data = self._get(
            "/formulas/count", {"date_from": "2026-10-15", "date_to": "2026-10-01"}
        )
        self.assertEqual(status, 400)
        self.assertIn("antérieure", data["detail"])

    def test_formulas_count_invalid_date_format(self):
        status, data = self._get("/formulas/count", {"date_from": "invalid-date"})
        self.assertEqual(status, 400)
        self.assertIn("Format de date invalide", data["detail"])

    # -----------------------------------------------------------------------
    # 2. Best Periods
    # -----------------------------------------------------------------------
    def test_best_periods_default(self):
        status, data = self._get("/formulas/best-periods")
        self.assertEqual(status, 200)
        self.assertIn("top_months", data)
        self.assertIn("top_days_of_week", data)
        self.assertIn("top_years", data)
        if data["top_months"]:
            self.assertIn("label", data["top_months"][0])
            self.assertIn("count", data["top_months"][0])
        if data["top_days_of_week"]:
            self.assertIn("label", data["top_days_of_week"][0])
            self.assertIn("day", data["top_days_of_week"][0])

    def test_best_periods_limit(self):
        status, data = self._get("/formulas/best-periods", {"limit": 2})
        self.assertEqual(status, 200)
        self.assertLessEqual(len(data["top_months"]), 2)
        self.assertLessEqual(len(data["top_days_of_week"]), 2)

    def test_best_periods_invalid_limit(self):
        status, _ = self._get("/formulas/best-periods", {"limit": 0})
        self.assertEqual(status, 422)
        status, _ = self._get("/formulas/best-periods", {"limit": 51})
        self.assertEqual(status, 422)

    # -----------------------------------------------------------------------
    # 3. Top Ateliers
    # -----------------------------------------------------------------------
    def test_top_ateliers_default(self):
        status, data = self._get("/ateliers/top")
        self.assertEqual(status, 200)
        self.assertIsInstance(data, list)
        for item in data:
            self.assertIn("atelier_name", item)
            self.assertIn("count", item)

    def test_top_ateliers_date_filter(self):
        status, data = self._get(
            "/ateliers/top", {"date_from": "2026-01-01", "date_to": "2026-12-31", "limit": 5}
        )
        self.assertEqual(status, 200)
        self.assertIsInstance(data, list)

    def test_top_ateliers_inverted_dates(self):
        status, data = self._get(
            "/ateliers/top", {"date_from": "2026-12-31", "date_to": "2026-01-01"}
        )
        self.assertEqual(status, 400)

    # -----------------------------------------------------------------------
    # 4. Top Notes (Exclusion de 'A définir')
    # -----------------------------------------------------------------------
    def test_top_notes_default(self):
        status, data = self._get("/notes/top", {"limit": 10})
        self.assertEqual(status, 200)
        self.assertIn("all", data)
        self.assertIn("top_note", data)
        self.assertIn("heart_note", data)
        self.assertIn("base_note", data)
        self.assertIn("booster_note", data)

        # Vérification critique : 'A définir' doit être TOTALEMENT absent
        all_note_names = [item["name"].lower() for item in data["all"]]
        self.assertNotIn("a définir", all_note_names)
        self.assertNotIn("a definir", all_note_names)

        top_names = [item["name"].lower() for item in data["top_note"]]
        self.assertNotIn("a définir", top_names)

        heart_names = [item["name"].lower() for item in data["heart_note"]]
        self.assertNotIn("a définir", heart_names)

        base_names = [item["name"].lower() for item in data["base_note"]]
        self.assertNotIn("a définir", base_names)

    def test_top_notes_specific_type(self):
        status, data = self._get("/notes/top", {"note_type": "top_note", "limit": 5})
        self.assertEqual(status, 200)
        self.assertIn("top_note", data)
        self.assertNotIn("heart_note", data)

    def test_top_notes_case_insensitivity(self):
        status, data = self._get("/notes/top", {"note_type": "TOP_NOTE", "limit": 3})
        self.assertEqual(status, 200)
        self.assertIn("top_note", data)

    def test_top_notes_invalid_type(self):
        status, data = self._get("/notes/top", {"note_type": "super_note"})
        self.assertEqual(status, 400)

    # -----------------------------------------------------------------------
    # 5. Top Options
    # -----------------------------------------------------------------------
    def test_top_options_default(self):
        status, data = self._get("/options/top")
        self.assertEqual(status, 200)
        self.assertIsInstance(data, list)
        for item in data:
            self.assertIn("option_name", item)
            self.assertIn("count", item)

    def test_top_options_date_filter(self):
        status, data = self._get(
            "/options/top", {"date_from": "2026-01-01", "date_to": "2026-12-31"}
        )
        self.assertEqual(status, 200)
        self.assertIsInstance(data, list)

    # -----------------------------------------------------------------------
    # 6. Customer Gender Distribution
    # -----------------------------------------------------------------------
    def test_gender_distribution_default(self):
        status, data = self._get("/customers/gender")
        self.assertEqual(status, 200)
        self.assertIn("male", data)
        self.assertIn("female", data)
        self.assertIn("unknown", data)
        self.assertIn("total", data)
        self.assertIn("male_pct", data)
        self.assertIn("female_pct", data)
        self.assertIn("unknown_pct", data)

        self.assertEqual(data["male"] + data["female"] + data["unknown"], data["total"])
        self.assertGreaterEqual(data["unknown_pct"], 0.0)
        self.assertLessEqual(data["unknown_pct"], 100.0)

    def test_gender_distribution_empty_period(self):
        status, data = self._get(
            "/customers/gender", {"date_from": "2040-01-01", "date_to": "2040-12-31"}
        )
        self.assertEqual(status, 200)
        self.assertEqual(data["total"], 0)
        self.assertEqual(data["male_pct"], 0.0)
        self.assertEqual(data["female_pct"], 0.0)
        self.assertEqual(data["unknown_pct"], 0.0)

    # -----------------------------------------------------------------------
    # 7. Customer Locations
    # -----------------------------------------------------------------------
    def test_top_locations_default(self):
        status, data = self._get("/customers/locations")
        self.assertEqual(status, 200)
        self.assertIn("top_countries", data)
        self.assertIn("top_cities", data)
        if data["top_countries"]:
            self.assertIn("country", data["top_countries"][0])
            self.assertIn("count", data["top_countries"][0])
        if data["top_cities"]:
            self.assertIn("city", data["top_cities"][0])
            self.assertIn("count", data["top_cities"][0])

    def test_top_locations_limit(self):
        status, data = self._get("/customers/locations", {"limit": 3})
        self.assertEqual(status, 200)
        self.assertLessEqual(len(data["top_countries"]), 3)
        self.assertLessEqual(len(data["top_cities"]), 3)

    # -----------------------------------------------------------------------
    # 8. Customer Loyalty
    # -----------------------------------------------------------------------
    def test_loyalty_default(self):
        status, data = self._get("/customers/loyalty")
        self.assertEqual(status, 200)
        self.assertIn("total_customers_with_formula", data)
        self.assertIn("loyal_customers", data)
        self.assertIn("loyalty_rate", data)
        self.assertIn("distribution", data)
        self.assertIn("new_loyal_by_month", data)
        self.assertGreaterEqual(data["loyalty_rate"], 0.0)
        self.assertLessEqual(data["loyalty_rate"], 100.0)

    def test_loyalty_threshold_validation(self):
        status, _ = self._get("/customers/loyalty", {"min_formulas": 1})
        self.assertEqual(status, 422)

    def test_loyalty_date_filter_on_new_loyal_by_month(self):
        # En filtrant sur octobre 2026 uniquement, juillet 2026 NE DOIT PAS être présent
        status, data = self._get(
            "/customers/loyalty", {"date_from": "2026-10-01", "date_to": "2026-10-15"}
        )
        self.assertEqual(status, 200)
        months = [item["month"] for item in data["new_loyal_by_month"]]
        self.assertNotIn("2026-07", months)
        self.assertTrue(all(m.startswith("2026-10") for m in months))

    # -----------------------------------------------------------------------
    # 9. OpenAPI Schema Validation
    # -----------------------------------------------------------------------
    def test_openapi_schema_contains_analytics(self):
        req = urllib.request.urlopen(f"{BASE_URL}/openapi.json")
        self.assertEqual(req.status, 200)
        spec = json.loads(req.read().decode("utf-8"))
        paths = spec["paths"]
        expected_endpoints = [
            "/api/v1/analytics/formulas/count",
            "/api/v1/analytics/formulas/best-periods",
            "/api/v1/analytics/ateliers/top",
            "/api/v1/analytics/notes/top",
            "/api/v1/analytics/options/top",
            "/api/v1/analytics/customers/gender",
            "/api/v1/analytics/customers/locations",
            "/api/v1/analytics/customers/loyalty",
        ]
        for ep in expected_endpoints:
            self.assertIn(ep, paths, f"Path {ep} missing from OpenAPI specification")
            # Verify response schema exists (not empty 200)
            get_op = paths[ep]["get"]
            self.assertIn("200", get_op["responses"])
            self.assertIn("content", get_op["responses"]["200"])


if __name__ == "__main__":
    unittest.main()
