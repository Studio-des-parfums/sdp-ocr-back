"""
Tests API — vérifie que les endpoints répondent correctement
sans planter, avec les bons codes HTTP et la bonne structure JSON.

Tous les accès à la base de données sont mockés via conftest.py.
Les repositories sont patchés pour retourner des données fictives stables.
"""

from unittest.mock import patch

# ═══════════════════════════════════════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════════════════════════════════════

FAKE_CUSTOMER = {
    "id": 1,
    "first_name": "Jean",
    "last_name": "Dupont",
    "email": "jean@example.com",
    "phone": "+33600000000",
    "job": None,
    "city": "Paris",
    "country": "France",
    "date": "2024-01-15",
    "verified_email": True,
    "verified_domain": True,
    "verified_phone": False,
    "formulas": [],
}

FAKE_FORMULA = {
    "id": 1,
    "customer_id": 1,
    "file_id": None,
    "reference": "REF-001",
    "perfume_name": "Rose Oud",
    "top_notes": [],
    "heart_notes": [],
    "base_notes": [],
}

FAKE_USER = {
    "id": 1,
    "first_name": "Alice",
    "last_name": "Martin",
    "email": "alice@sdp.fr",
    "phone": None,
    "job": "Parfumeur",
    "team": "Atelier",
    "role_id": 1,
    "is_online": False,
    "last_login": None,
}

FAKE_ROLE = {
    "id": 1,
    "name": "Admin",
    "description": "Administrateur",
    "permissions": [],
}


# ═══════════════════════════════════════════════════════════════════════════
# 1. Routes de base — l'app ne crashe pas au démarrage
# ═══════════════════════════════════════════════════════════════════════════


class TestAppStartup:
    def test_root_returns_200(self, client):
        """GET / → 200 avec un message de bienvenue."""
        r = client.get("/")
        assert r.status_code == 200
        data = r.json()
        assert "message" in data

    def test_health_returns_200(self, client):
        """GET /health → 200 avec status=healthy."""
        r = client.get("/health")
        assert r.status_code == 200
        data = r.json()
        assert data["status"] == "healthy"

    def test_openapi_schema_available(self, client):
        """GET /openapi.json → 200, l'app a bien enregistré ses routes."""
        r = client.get("/openapi.json")
        assert r.status_code == 200
        schema = r.json()
        assert "paths" in schema
        # Vérifie que les principaux préfixes sont présents
        paths = schema["paths"]
        prefixes = {p.split("/")[1] for p in paths if p.startswith("/")}
        assert "api" in prefixes

    def test_docs_available(self, client):
        """GET /docs → 200, Swagger UI accessible."""
        r = client.get("/docs")
        assert r.status_code == 200


# ═══════════════════════════════════════════════════════════════════════════
# 2. Customers
# ═══════════════════════════════════════════════════════════════════════════


class TestCustomersEndpoints:
    BASE = "/api/v1/customers"

    def test_get_customers_returns_200(self, client):
        """GET /customers → 200 avec pagination."""
        with patch(
            "app.repositories.customer_repository.customer_repository.get_all_customers",
            return_value=([FAKE_CUSTOMER], 1),
        ):
            r = client.get(self.BASE)
        assert r.status_code == 200
        data = r.json()
        assert "customers" in data
        assert "total" in data
        assert data["total"] == 1

    def test_get_customers_pagination_params(self, client):
        """GET /customers?page=2&size=5 → 200, params respectés."""
        with patch(
            "app.repositories.customer_repository.customer_repository.get_all_customers",
            return_value=([], 0),
        ):
            r = client.get(self.BASE, params={"page": 2, "size": 5})
        assert r.status_code == 200
        data = r.json()
        assert data["page"] == 2
        assert data["size"] == 5

    def test_get_customer_by_id_returns_200(self, client):
        """GET /customers/1 → 200 avec les données du customer."""
        with patch(
            "app.repositories.customer_repository.customer_repository.get_customer_by_id",
            return_value=FAKE_CUSTOMER,
        ):
            r = client.get(f"{self.BASE}/1")
        assert r.status_code == 200
        data = r.json()
        assert data["id"] == 1
        assert data["email"] == "jean@example.com"

    def test_get_customer_not_found_returns_404(self, client):
        """GET /customers/9999 → 404 si le customer n'existe pas."""
        with patch(
            "app.repositories.customer_repository.customer_repository.get_customer_by_id",
            return_value=None,
        ):
            r = client.get(f"{self.BASE}/9999")
        assert r.status_code == 404

    def test_create_customer_returns_200(self, client):
        """POST /customers → 200 avec le customer créé."""
        with (
            patch(
                "app.repositories.customer_repository.customer_repository.create_customer",
                return_value=1,
            ),
            patch(
                "app.repositories.customer_repository.customer_repository.get_customer_by_id",
                return_value=FAKE_CUSTOMER,
            ),
        ):
            r = client.post(
                self.BASE,
                json={"first_name": "Jean", "last_name": "Dupont", "email": "jean@example.com"},
            )
        assert r.status_code == 200
        data = r.json()
        assert data["id"] == 1

    def test_invalid_page_param_returns_422(self, client):
        """GET /customers?page=0 → 422 (validation FastAPI)."""
        r = client.get(self.BASE, params={"page": 0})
        assert r.status_code == 422


# ═══════════════════════════════════════════════════════════════════════════
# 3. Formulas
# ═══════════════════════════════════════════════════════════════════════════


class TestFormulasEndpoints:
    BASE = "/api/v1/formulas"

    def test_get_formula_returns_200(self, client):
        """GET /formulas/1 → 200 avec la formule."""
        with patch(
            "app.repositories.formula_repository.formula_repository.get_formula_by_id",
            return_value=FAKE_FORMULA,
        ):
            r = client.get(f"{self.BASE}/1")
        assert r.status_code == 200
        data = r.json()
        assert data["id"] == 1
        assert data["reference"] == "REF-001"

    def test_get_formula_not_found_returns_404(self, client):
        """GET /formulas/9999 → 404."""
        with patch(
            "app.repositories.formula_repository.formula_repository.get_formula_by_id",
            return_value=None,
        ):
            r = client.get(f"{self.BASE}/9999")
        assert r.status_code == 404
        assert "9999" in r.json()["detail"]


# ═══════════════════════════════════════════════════════════════════════════
# 4. Users
# ═══════════════════════════════════════════════════════════════════════════


class TestUsersEndpoints:
    BASE = "/api/v1/users"

    def test_get_users_returns_200(self, client):
        """GET /users → 200 avec pagination."""
        with patch(
            "app.repositories.user_repository.user_repository.get_all_users",
            return_value=([FAKE_USER], 1),
        ):
            r = client.get(self.BASE)
        assert r.status_code == 200
        data = r.json()
        assert "users" in data or "total" in data  # shape variable selon impl

    def test_get_user_not_found_returns_404(self, client):
        """GET /users/9999 → 404."""
        with patch(
            "app.repositories.user_repository.user_repository.get_user_by_id",
            return_value=None,
        ):
            r = client.get(f"{self.BASE}/9999")
        assert r.status_code == 404


# ═══════════════════════════════════════════════════════════════════════════
# 5. Roles
# ═══════════════════════════════════════════════════════════════════════════


class TestRolesEndpoints:
    BASE = "/api/v1/roles"

    def test_get_roles_returns_200(self, client):
        """GET /roles → 200 avec liste paginée."""
        with patch(
            "app.repositories.role_repository.role_repository.get_all_roles",
            return_value=([FAKE_ROLE], 1),
        ):
            r = client.get(f"{self.BASE}/")
        assert r.status_code == 200
        data = r.json()
        assert "roles" in data
        assert "total" in data

    def test_get_role_by_id_returns_200(self, client):
        """GET /roles/1 → 200."""
        with patch(
            "app.repositories.role_repository.role_repository.get_role_by_id",
            return_value=FAKE_ROLE,
        ):
            r = client.get(f"{self.BASE}/1")
        assert r.status_code == 200
        assert r.json()["name"] == "Admin"

    def test_get_role_not_found_returns_404(self, client):
        """GET /roles/9999 → 404."""
        with patch(
            "app.repositories.role_repository.role_repository.get_role_by_id",
            return_value=None,
        ):
            r = client.get(f"{self.BASE}/9999")
        assert r.status_code == 404


# ═══════════════════════════════════════════════════════════════════════════
# 6. Analytics — validation des paramètres
# ═══════════════════════════════════════════════════════════════════════════


class TestAnalyticsEndpoints:
    BASE = "/api/v1/analytics"

    FAKE_COUNT_RESPONSE = {
        "total": 42,
        "group_by": "month",
        "period_label": "month",
        "data": [],
    }

    def test_formula_count_default_returns_200(self, client):
        """GET /analytics/formulas/count → 200 sans paramètre."""
        with patch(
            "app.repositories.analytics_repository.analytics_repository.get_formula_count_by_date",
            return_value=self.FAKE_COUNT_RESPONSE,
        ):
            r = client.get(f"{self.BASE}/formulas/count")
        assert r.status_code == 200
        data = r.json()
        assert "total" in data
        assert "data" in data

    def test_formula_count_invalid_group_by_returns_400(self, client):
        """GET /analytics/formulas/count?group_by=week → 400 (valeur invalide)."""
        r = client.get(f"{self.BASE}/formulas/count", params={"group_by": "week"})
        assert r.status_code == 400

    def test_formula_count_invalid_date_format_returns_400(self, client):
        """GET /analytics/formulas/count?date_from=01/01/2024 → 400 (mauvais format)."""
        r = client.get(f"{self.BASE}/formulas/count", params={"date_from": "01/01/2024"})
        assert r.status_code == 400

    def test_formula_count_inverted_dates_returns_400(self, client):
        """date_from > date_to → 400."""
        r = client.get(
            f"{self.BASE}/formulas/count",
            params={"date_from": "2024-12-31", "date_to": "2024-01-01"},
        )
        assert r.status_code == 400

    def test_formula_count_valid_date_range(self, client):
        """date_from <= date_to → 200."""
        with patch(
            "app.repositories.analytics_repository.analytics_repository.get_formula_count_by_date",
            return_value=self.FAKE_COUNT_RESPONSE,
        ):
            r = client.get(
                f"{self.BASE}/formulas/count",
                params={"date_from": "2024-01-01", "date_to": "2024-12-31"},
            )
        assert r.status_code == 200


# ═══════════════════════════════════════════════════════════════════════════
# 7. Crash resilience — repository qui lève une exception
# ═══════════════════════════════════════════════════════════════════════════


class TestCrashResilience:
    """
    Vérifie que l'app renvoie 500 (et ne crash pas) quand un repository
    lève une exception inattendue.
    """

    def test_customers_db_error_returns_500(self, client):
        with patch(
            "app.repositories.customer_repository.customer_repository.get_all_customers",
            side_effect=RuntimeError("DB is down"),
        ):
            r = client.get("/api/v1/customers")
        # L'app doit répondre 500 et ne pas s'arrêter
        assert r.status_code == 500
        assert r.json() is not None  # Toujours du JSON

    def test_roles_db_error_returns_500(self, client):
        with patch(
            "app.repositories.role_repository.role_repository.get_all_roles",
            side_effect=Exception("Connexion perdue"),
        ):
            r = client.get("/api/v1/roles/")
        assert r.status_code == 500

    def test_analytics_db_error_returns_500(self, client):
        with patch(
            "app.repositories.analytics_repository.analytics_repository.get_formula_count_by_date",
            side_effect=Exception("timeout"),
        ):
            r = client.get("/api/v1/analytics/formulas/count")
        assert r.status_code == 500
