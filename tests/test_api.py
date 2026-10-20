"""
Tests API — couvre toutes les méthodes HTTP (GET, POST, PUT, PATCH, DELETE).

Stratégie :
- L'app FastAPI est instanciée une seule fois (fixture session dans conftest.py).
- Chaque test mock uniquement le repository qu'il touche.
- On vérifie : code HTTP, structure JSON, gestion des 404 / 400 / 422 / 500.
"""

from unittest.mock import MagicMock, patch

# ══════════════════════════════════════════════════════════════════════════════
# Données fictives stables
# ══════════════════════════════════════════════════════════════════════════════

CUSTOMER = {
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

FORMULA = {
    "id": 1,
    "customer_id": 1,
    "file_id": None,
    "reference": "REF-001",
    "perfume_name": "Rose Oud",
    "top_notes": [],
    "heart_notes": [],
    "base_notes": [],
}

USER = {
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

ROLE = {
    "id": 1,
    "name": "Admin",
    "csv_download_limit": 0,
    "email_sending": False,
    "pdf_extraction_limit": 0,
    "customers_access": True,
    "customers_edit": True,
    "access_to_extraction": True,
    "customers_review_access": True,
    "formula_edit": True,
    "full_access": True,
    "devices_access": True,
}

GROUP = {
    "id": 1,
    "name": "VIP",
    "description": "Clients VIP",
    "created_by": 1,
    "created_at": "2024-01-01T00:00:00",
    "updated_at": "2024-01-01T00:00:00",
    "is_deleted": False,
}

ORDER = {
    "id": 1,
    "customer_id": 1,
    "formula_id": 1,
    "status": "PENDING",
    "comment": None,
    "allergy": None,
    "items": [],
    "created_at": "2024-01-01T00:00:00",
    "updated_at": "2024-01-01T00:00:00",
}

ORDER_ITEM = {
    "id": 1,
    "order_id": 1,
    "name": "Rose",
    "quantity": 2,
}

ANALYTICS_COUNT = {
    "total": 42,
    "group_by": "month",
    "period_label": "month",
    "data": [],
}


# ══════════════════════════════════════════════════════════════════════════════
# 1. App startup — l'app ne crashe pas
# ══════════════════════════════════════════════════════════════════════════════


class TestAppStartup:
    def test_root_200(self, client):
        r = client.get("/")
        assert r.status_code == 200
        assert "message" in r.json()

    def test_health_200(self, client):
        r = client.get("/health")
        assert r.status_code == 200
        assert r.json()["status"] == "healthy"

    def test_openapi_schema_has_routes(self, client):
        r = client.get("/openapi.json")
        assert r.status_code == 200
        paths = r.json()["paths"]
        # Vérifie quelques routes clés
        assert "/api/v1/customers" in paths
        assert "/api/v1/roles/" in paths
        assert "/api/v1/orders/" in paths

    def test_swagger_docs_200(self, client):
        r = client.get("/docs")
        assert r.status_code == 200


# ══════════════════════════════════════════════════════════════════════════════
# 2. Customers — GET / POST / PUT / DELETE
# ══════════════════════════════════════════════════════════════════════════════

_CUST_REPO = "app.repositories.customer_repository.customer_repository"


class TestCustomers:
    BASE = "/api/v1/customers"

    # ── GET ──────────────────────────────────────────────────────────────────

    def test_list_200(self, client):
        with patch(f"{_CUST_REPO}.get_all_customers", return_value=([CUSTOMER], 1)):
            r = client.get(self.BASE)
        assert r.status_code == 200
        body = r.json()
        assert body["total"] == 1
        assert len(body["customers"]) == 1

    def test_list_pagination_422_on_page_zero(self, client):
        """page=0 viole ge=1 → FastAPI renvoie 422 automatiquement."""
        r = client.get(self.BASE, params={"page": 0})
        assert r.status_code == 422

    def test_list_size_too_large_422(self, client):
        """size=200 viole le=100 → 422."""
        r = client.get(self.BASE, params={"size": 200})
        assert r.status_code == 422

    def test_get_by_id_200(self, client):
        with patch(f"{_CUST_REPO}.get_customer_by_id", return_value=CUSTOMER):
            r = client.get(f"{self.BASE}/1")
        assert r.status_code == 200
        assert r.json()["email"] == "jean@example.com"

    def test_get_by_id_404(self, client):
        with patch(f"{_CUST_REPO}.get_customer_by_id", return_value=None):
            r = client.get(f"{self.BASE}/9999")
        assert r.status_code == 404

    # ── POST ─────────────────────────────────────────────────────────────────

    def test_create_200(self, client):
        with (
            patch(f"{_CUST_REPO}.create_customer", return_value=1),
            patch(f"{_CUST_REPO}.get_customer_by_id", return_value=CUSTOMER),
        ):
            r = client.post(self.BASE, json={"first_name": "Jean", "email": "jean@example.com"})
        assert r.status_code == 200
        assert r.json()["id"] == 1

    def test_create_500_on_db_error(self, client):
        with patch(f"{_CUST_REPO}.create_customer", side_effect=RuntimeError("DB down")):
            r = client.post(self.BASE, json={"first_name": "X"})
        assert r.status_code == 500

    # ── PUT ──────────────────────────────────────────────────────────────────

    def test_update_200(self, client):
        updated = {**CUSTOMER, "city": "Lyon"}
        with (
            patch(f"{_CUST_REPO}.get_customer_by_id", return_value=CUSTOMER),
            patch(f"{_CUST_REPO}.update_customer", return_value=True),
            # 2e appel get après update
            patch(
                f"{_CUST_REPO}.get_customer_by_id",
                side_effect=[CUSTOMER, updated],
            ),
        ):
            r = client.put(f"{self.BASE}/1", json={"city": "Lyon"})
        assert r.status_code == 200

    def test_update_404_unknown_customer(self, client):
        with patch(f"{_CUST_REPO}.get_customer_by_id", return_value=None):
            r = client.put(f"{self.BASE}/9999", json={"city": "Lyon"})
        assert r.status_code == 404

    # ── DELETE ───────────────────────────────────────────────────────────────

    def test_delete_200(self, client):
        with (
            patch(f"{_CUST_REPO}.get_customer_by_id", return_value=CUSTOMER),
            patch(f"{_CUST_REPO}.delete_customer", return_value=True),
        ):
            r = client.delete(f"{self.BASE}/1")
        assert r.status_code == 200
        assert "supprimé" in r.json()["message"]

    def test_delete_404_unknown(self, client):
        with patch(f"{_CUST_REPO}.get_customer_by_id", return_value=None):
            r = client.delete(f"{self.BASE}/9999")
        assert r.status_code == 404

    def test_delete_500_on_db_error(self, client):
        with (
            patch(f"{_CUST_REPO}.get_customer_by_id", return_value=CUSTOMER),
            patch(f"{_CUST_REPO}.delete_customer", side_effect=RuntimeError("crash")),
        ):
            r = client.delete(f"{self.BASE}/1")
        assert r.status_code == 500

    # ── PUT bulk ─────────────────────────────────────────────────────────────

    def test_bulk_update_200(self, client):
        fake_result = [{"id": 1, "success": True, "message": "ok"}]
        with patch(f"{_CUST_REPO}.bulk_update_customers", return_value=fake_result):
            r = client.put(
                f"{self.BASE}/bulk",
                json={"customers": [{"id": 1, "city": "Bordeaux"}]},
            )
        assert r.status_code == 200
        body = r.json()
        assert body["total_updated"] == 1


# ══════════════════════════════════════════════════════════════════════════════
# 3. Formulas — GET / PUT notes / DELETE
# ══════════════════════════════════════════════════════════════════════════════

_FORM_REPO = "app.repositories.formula_repository.formula_repository"


class TestFormulas:
    BASE = "/api/v1/formulas"

    def test_get_200(self, client):
        with patch(f"{_FORM_REPO}.get_formula_by_id", return_value=FORMULA):
            r = client.get(f"{self.BASE}/1")
        assert r.status_code == 200
        assert r.json()["reference"] == "REF-001"

    def test_get_404(self, client):
        with patch(f"{_FORM_REPO}.get_formula_by_id", return_value=None):
            r = client.get(f"{self.BASE}/9999")
        assert r.status_code == 404

    def test_update_notes_200(self, client):
        """PUT /formulas/1/notes — mise à jour des notes de la pyramide."""
        updated = {
            **FORMULA,
            "top_notes": [{"id": 1, "name": "Bergamote", "quantity": "3ml", "formula_id": 1}],
        }
        # Le endpoint importe formula_repository directement depuis son module
        _repo = "app.api.endpoints.formulas.formula_repository"
        with (
            patch(f"{_repo}.get_formula_by_id", side_effect=[FORMULA, updated]),
            patch(f"{_repo}.update_formula_notes", return_value=True),
        ):
            r = client.put(
                f"{self.BASE}/1/notes",
                json={
                    "top_notes": [{"name": "Bergamote", "quantity": "3ml"}],
                    "heart_notes": [],
                    "base_notes": [],
                },
            )
        assert r.status_code == 200

    def test_update_notes_404(self, client):
        with patch(f"{_FORM_REPO}.get_formula_by_id", return_value=None):
            r = client.put(
                f"{self.BASE}/9999/notes",
                json={"top_notes": [], "heart_notes": [], "base_notes": []},
            )
        assert r.status_code == 404

    def test_delete_200(self, client):
        with (
            patch(f"{_FORM_REPO}.get_formula_by_id", return_value=FORMULA),
            patch(f"{_FORM_REPO}.delete_formula", return_value=True),
        ):
            r = client.delete(f"{self.BASE}/1")
        assert r.status_code == 200

    def test_delete_404(self, client):
        with patch(f"{_FORM_REPO}.get_formula_by_id", return_value=None):
            r = client.delete(f"{self.BASE}/9999")
        assert r.status_code == 404

    def test_duplicate_201(self, client):
        duplicated = {
            **FORMULA,
            "id": 2,
            "reference": "REF-001-2",
        }
        with (
            patch(f"{_FORM_REPO}.get_formula_by_id", return_value=FORMULA),
            patch(f"{_FORM_REPO}.duplicate_formula", return_value=duplicated),
        ):
            r = client.post(f"{self.BASE}/1/duplicate")
        assert r.status_code == 201
        assert r.json()["id"] == 2
        assert r.json()["reference"] == "REF-001-2"

    def test_duplicate_404(self, client):
        with patch(f"{_FORM_REPO}.get_formula_by_id", return_value=None):
            r = client.post(f"{self.BASE}/9999/duplicate")
        assert r.status_code == 404

    def test_duplicate_500_on_error(self, client):
        with (
            patch(f"{_FORM_REPO}.get_formula_by_id", return_value=FORMULA),
            patch(f"{_FORM_REPO}.duplicate_formula", return_value=None),
        ):
            r = client.post(f"{self.BASE}/1/duplicate")
        assert r.status_code == 500


class TestGenerateReusedReference:
    def test_first_duplicate(self):
        from app.crud.crud_formula import generate_reused_reference

        conn = MagicMock()
        cursor = conn.cursor.return_value
        cursor.fetchone.return_value = {"reference": "202610001"}
        cursor.fetchall.return_value = []
        ref = generate_reused_reference(conn, 1)
        assert ref == "202610001-2"

    def test_second_duplicate(self):
        from app.crud.crud_formula import generate_reused_reference

        conn = MagicMock()
        cursor = conn.cursor.return_value
        cursor.fetchone.return_value = {"reference": "202610001"}
        cursor.fetchall.return_value = [{"reference": "202610001-2"}]
        ref = generate_reused_reference(conn, 1)
        assert ref == "202610001-3"

    def test_third_duplicate_with_nested_duplicate(self):
        from app.crud.crud_formula import generate_reused_reference

        conn = MagicMock()
        cursor = conn.cursor.return_value
        cursor.fetchone.return_value = {"reference": "202610001"}
        cursor.fetchall.return_value = [
            {"reference": "202610001-2"},
            {"reference": "202610001-3"},
            {"reference": "202610001-2-2"},
        ]
        ref = generate_reused_reference(conn, 1)
        assert ref == "202610001-4"

    def test_duplicate_of_duplicate(self):
        from app.crud.crud_formula import generate_reused_reference

        conn = MagicMock()
        cursor = conn.cursor.return_value
        cursor.fetchone.return_value = {"reference": "202610001-2"}
        cursor.fetchall.return_value = []
        ref = generate_reused_reference(conn, 2)
        assert ref == "202610001-2-2"

    def test_duplicate_of_duplicate_second_time(self):
        from app.crud.crud_formula import generate_reused_reference

        conn = MagicMock()
        cursor = conn.cursor.return_value
        cursor.fetchone.return_value = {"reference": "202610001-2"}
        cursor.fetchall.return_value = [{"reference": "202610001-2-2"}]
        ref = generate_reused_reference(conn, 2)
        assert ref == "202610001-2-3"


# ══════════════════════════════════════════════════════════════════════════════
# 4. Roles — GET / POST / PUT / DELETE
# ══════════════════════════════════════════════════════════════════════════════

_ROLE_REPO = "app.repositories.role_repository.role_repository"


class TestRoles:
    BASE = "/api/v1/roles"

    def test_list_200(self, client):
        with patch(f"{_ROLE_REPO}.get_all_roles", return_value=([ROLE], 1)):
            r = client.get(f"{self.BASE}/")
        assert r.status_code == 200
        assert r.json()["total"] == 1

    def test_get_200(self, client):
        with patch(f"{_ROLE_REPO}.get_role_by_id", return_value=ROLE):
            r = client.get(f"{self.BASE}/1")
        assert r.status_code == 200
        assert r.json()["name"] == "Admin"

    def test_get_404(self, client):
        with patch(f"{_ROLE_REPO}.get_role_by_id", return_value=None):
            r = client.get(f"{self.BASE}/9999")
        assert r.status_code == 404

    def test_create_200(self, client):
        with (
            patch(f"{_ROLE_REPO}.create_role", return_value=1),
            patch(f"{_ROLE_REPO}.get_role_by_id", return_value=ROLE),
        ):
            r = client.post(f"{self.BASE}/", json={"name": "Admin"})
        assert r.status_code == 200
        assert r.json()["id"] == 1

    def test_create_missing_name_422(self, client):
        """name est requis — FastAPI renvoie 422 sans toucher au repo."""
        r = client.post(f"{self.BASE}/", json={})
        assert r.status_code == 422

    def test_update_200(self, client):
        updated = {**ROLE, "name": "SuperAdmin"}
        with (
            patch(f"{_ROLE_REPO}.get_role_by_id", side_effect=[ROLE, updated]),
            patch(f"{_ROLE_REPO}.update_role", return_value=True),
        ):
            r = client.put(f"{self.BASE}/1", json={"name": "SuperAdmin"})
        assert r.status_code == 200

    def test_update_404(self, client):
        with patch(f"{_ROLE_REPO}.get_role_by_id", return_value=None):
            r = client.put(f"{self.BASE}/9999", json={"name": "X"})
        assert r.status_code == 404

    def test_delete_200(self, client):
        with (
            patch(f"{_ROLE_REPO}.get_role_by_id", return_value=ROLE),
            patch(f"{_ROLE_REPO}.delete_role", return_value=True),
        ):
            r = client.delete(f"{self.BASE}/1")
        assert r.status_code == 200

    def test_delete_404(self, client):
        with patch(f"{_ROLE_REPO}.get_role_by_id", return_value=None):
            r = client.delete(f"{self.BASE}/9999")
        assert r.status_code == 404


# ══════════════════════════════════════════════════════════════════════════════
# 5. Groups — GET / POST / PUT / DELETE + actions métier
# ══════════════════════════════════════════════════════════════════════════════

_GROUP_REPO = "app.repositories.group_repository.group_repository"


class TestGroups:
    BASE = "/api/v1/groups"

    def test_list_200(self, client):
        with patch(f"{_GROUP_REPO}.get_all_groups", return_value=([GROUP], 1)):
            r = client.get(f"{self.BASE}/")
        assert r.status_code == 200

    def test_get_200(self, client):
        with patch(f"{_GROUP_REPO}.get_group_by_id", return_value=GROUP):
            r = client.get(f"{self.BASE}/1")
        assert r.status_code == 200
        assert r.json()["name"] == "VIP"

    def test_get_404(self, client):
        with patch(f"{_GROUP_REPO}.get_group_by_id", return_value=None):
            r = client.get(f"{self.BASE}/9999")
        assert r.status_code == 404

    def test_create_200(self, client):
        with (
            patch(f"{_GROUP_REPO}.create_group", return_value=1),
            patch(f"{_GROUP_REPO}.get_group_by_id", return_value=GROUP),
        ):
            r = client.post(f"{self.BASE}/", json={"name": "VIP", "created_by": 1})
        assert r.status_code == 200

    def test_create_missing_fields_422(self, client):
        """name et created_by sont requis."""
        r = client.post(f"{self.BASE}/", json={})
        assert r.status_code == 422

    def test_update_200(self, client):
        with (
            patch(f"{_GROUP_REPO}.get_group_by_id", return_value=GROUP),
            patch(f"{_GROUP_REPO}.update_group", return_value=True),
            patch(f"{_GROUP_REPO}.get_group_by_id", side_effect=[GROUP, {**GROUP, "name": "VIP+"}]),
        ):
            r = client.put(f"{self.BASE}/1", json={"name": "VIP+"})
        assert r.status_code == 200

    def test_update_404(self, client):
        with patch(f"{_GROUP_REPO}.get_group_by_id", return_value=None):
            r = client.put(f"{self.BASE}/9999", json={"name": "X"})
        assert r.status_code == 404

    def test_delete_200(self, client):
        with patch(f"{_GROUP_REPO}.soft_delete_group", return_value=True):
            r = client.delete(f"{self.BASE}/1")
        assert r.status_code == 200

    def test_delete_404(self, client):
        with patch(f"{_GROUP_REPO}.soft_delete_group", return_value=False):
            r = client.delete(f"{self.BASE}/9999")
        assert r.status_code == 404

    def test_add_customers_200(self, client):
        """POST /groups/1/customers — ajouter des clients à un groupe."""
        fake_result = {"success": True, "message": "ok", "added": 2, "already_in": 0}
        with patch(f"{_GROUP_REPO}.add_customers_to_group", return_value=fake_result):
            r = client.post(
                f"{self.BASE}/1/customers",
                json={"customer_ids": [1, 2], "added_by": 1},
            )
        assert r.status_code == 200

    def test_merge_groups_400_less_than_two(self, client):
        """POST /groups/merge avec un seul groupe → 400 (règle métier).
        Le schéma requiert new_group_name + created_by, sinon FastAPI renvoie 422."""
        r = client.post(
            f"{self.BASE}/merge",
            json={
                "source_group_ids": [1],
                "new_group_name": "Fusion",
                "created_by": 1,
            },
        )
        assert r.status_code == 400


# ══════════════════════════════════════════════════════════════════════════════
# 6. Orders — GET / POST / PUT / DELETE + items
# ══════════════════════════════════════════════════════════════════════════════

_ORDER_REPO = "app.repositories.order_repository.order_repository"


class TestOrders:
    BASE = "/api/v1/orders"

    def test_list_200(self, client):
        with patch(f"{_ORDER_REPO}.get_all_orders", return_value=([ORDER], 1)):
            r = client.get(f"{self.BASE}/")
        assert r.status_code == 200

    def test_get_200(self, client):
        with patch(f"{_ORDER_REPO}.get_order_by_id", return_value=ORDER):
            r = client.get(f"{self.BASE}/1")
        assert r.status_code == 200
        assert r.json()["status"] == "PENDING"

    def test_get_404(self, client):
        with patch(f"{_ORDER_REPO}.get_order_by_id", return_value=None):
            r = client.get(f"{self.BASE}/9999")
        assert r.status_code == 404

    def test_create_200(self, client):
        with (
            patch(f"{_ORDER_REPO}.create_order", return_value=1),
            patch(f"{_ORDER_REPO}.get_order_by_id", return_value=ORDER),
        ):
            r = client.post(
                f"{self.BASE}/",
                json={"customer_id": 1, "formula_id": 1},
            )
        assert r.status_code == 200

    def test_create_missing_fields_422(self, client):
        """customer_id et formula_id sont requis."""
        r = client.post(f"{self.BASE}/", json={})
        assert r.status_code == 422

    def test_update_200(self, client):
        updated = {**ORDER, "status": "CONFIRMED"}
        with (
            patch(f"{_ORDER_REPO}.get_order_by_id", side_effect=[ORDER, updated]),
            patch(f"{_ORDER_REPO}.update_order", return_value=True),
        ):
            r = client.put(f"{self.BASE}/1", json={"status": "CONFIRMED"})
        assert r.status_code == 200

    def test_update_404(self, client):
        with patch(f"{_ORDER_REPO}.get_order_by_id", return_value=None):
            r = client.put(f"{self.BASE}/9999", json={"status": "CONFIRMED"})
        assert r.status_code == 404

    def test_update_empty_body_400(self, client):
        """PUT sans champ → 400 (aucune donnée à mettre à jour)."""
        with patch(f"{_ORDER_REPO}.get_order_by_id", return_value=ORDER):
            r = client.put(f"{self.BASE}/1", json={})
        assert r.status_code == 400

    def test_delete_200(self, client):
        with (
            patch(f"{_ORDER_REPO}.get_order_by_id", return_value=ORDER),
            patch(f"{_ORDER_REPO}.delete_order", return_value=True),
        ):
            r = client.delete(f"{self.BASE}/1")
        assert r.status_code == 200

    def test_delete_404(self, client):
        with patch(f"{_ORDER_REPO}.get_order_by_id", return_value=None):
            r = client.delete(f"{self.BASE}/9999")
        assert r.status_code == 404

    # ── Items ─────────────────────────────────────────────────────────────────

    def test_add_item_200(self, client):
        """POST /orders/1/items — ajouter un article à une commande."""
        with (
            patch(f"{_ORDER_REPO}.get_order_by_id", return_value=ORDER),
            patch(f"{_ORDER_REPO}.add_item_to_order", return_value=1),
            patch(f"{_ORDER_REPO}.get_order_item_by_id", return_value=ORDER_ITEM),
        ):
            r = client.post(f"{self.BASE}/1/items", json={"name": "Rose", "quantity": 2})
        assert r.status_code == 200

    def test_add_item_404_order_not_found(self, client):
        with patch(f"{_ORDER_REPO}.get_order_by_id", return_value=None):
            r = client.post(f"{self.BASE}/9999/items", json={"name": "Rose", "quantity": 2})
        assert r.status_code == 404

    def test_update_item_200(self, client):
        """PUT /orders/1/items/1 — mettre à jour un article."""
        with (
            patch(f"{_ORDER_REPO}.get_order_item_by_id", return_value=ORDER_ITEM),
            patch(f"{_ORDER_REPO}.update_order_item", return_value=True),
            patch(
                f"{_ORDER_REPO}.get_order_item_by_id",
                side_effect=[ORDER_ITEM, {**ORDER_ITEM, "quantity": 5}],
            ),
        ):
            r = client.put(f"{self.BASE}/1/items/1", json={"quantity": 5})
        assert r.status_code == 200

    def test_update_item_404(self, client):
        with patch(f"{_ORDER_REPO}.get_order_item_by_id", return_value=None):
            r = client.put(f"{self.BASE}/1/items/9999", json={"quantity": 5})
        assert r.status_code == 404

    def test_delete_item_200(self, client):
        """DELETE /orders/1/items/1."""
        with (
            patch(f"{_ORDER_REPO}.get_order_item_by_id", return_value=ORDER_ITEM),
            patch(f"{_ORDER_REPO}.delete_order_item", return_value=True),
        ):
            r = client.delete(f"{self.BASE}/1/items/1")
        assert r.status_code == 200

    def test_delete_item_404(self, client):
        with patch(f"{_ORDER_REPO}.get_order_item_by_id", return_value=None):
            r = client.delete(f"{self.BASE}/1/items/9999")
        assert r.status_code == 404


# ══════════════════════════════════════════════════════════════════════════════
# 7. Users — GET / POST / PUT / DELETE / PATCH
# ══════════════════════════════════════════════════════════════════════════════

_USER_REPO = "app.repositories.user_repository.user_repository"


class TestUsers:
    BASE = "/api/v1/users"

    def test_list_200(self, client):
        with patch(f"{_USER_REPO}.get_all_users", return_value=([USER], 1)):
            r = client.get(self.BASE)
        assert r.status_code == 200

    def test_get_200(self, client):
        with patch(f"{_USER_REPO}.get_user_by_id", return_value=USER):
            r = client.get(f"{self.BASE}/1")
        assert r.status_code == 200
        assert r.json()["email"] == "alice@sdp.fr"

    def test_get_404(self, client):
        with patch(f"{_USER_REPO}.get_user_by_id", return_value=None):
            r = client.get(f"{self.BASE}/9999")
        assert r.status_code == 404

    def test_create_200(self, client):
        with (
            patch(f"{_USER_REPO}.get_user_by_email", return_value=None),
            patch(f"{_USER_REPO}.create_user", return_value=1),
            patch(f"{_USER_REPO}.get_user_by_id", return_value=USER),
        ):
            r = client.post(self.BASE, json={"email": "alice@sdp.fr", "first_name": "Alice"})
        assert r.status_code == 200

    def test_create_duplicate_email_400(self, client):
        """Email déjà utilisé → 400."""
        with patch(f"{_USER_REPO}.get_user_by_email", return_value=USER):
            r = client.post(self.BASE, json={"email": "alice@sdp.fr"})
        assert r.status_code == 400

    def test_update_200(self, client):
        updated = {**USER, "job": "Directeur"}
        with (
            patch(f"{_USER_REPO}.get_user_by_id", side_effect=[USER, updated]),
            patch(f"{_USER_REPO}.update_user", return_value=True),
        ):
            r = client.put(f"{self.BASE}/1", json={"job": "Directeur"})
        assert r.status_code == 200

    def test_update_404(self, client):
        with patch(f"{_USER_REPO}.get_user_by_id", return_value=None):
            r = client.put(f"{self.BASE}/9999", json={"job": "X"})
        assert r.status_code == 404

    def test_delete_200(self, client):
        with (
            patch(f"{_USER_REPO}.get_user_by_id", return_value=USER),
            patch(f"{_USER_REPO}.delete_user", return_value=True),
        ):
            r = client.delete(f"{self.BASE}/1")
        assert r.status_code == 200

    def test_delete_404(self, client):
        with patch(f"{_USER_REPO}.get_user_by_id", return_value=None):
            r = client.delete(f"{self.BASE}/9999")
        assert r.status_code == 404

    def test_patch_login_status_200(self, client):
        """PATCH /users/1/login-status — met à jour le statut en ligne."""
        with (
            patch(f"{_USER_REPO}.get_user_by_id", return_value=USER),
            patch(f"{_USER_REPO}.update_user_login_status", return_value=True),
        ):
            r = client.patch(f"{self.BASE}/1/login-status", json={"is_online": True})
        assert r.status_code == 200

    def test_patch_login_status_404(self, client):
        with patch(f"{_USER_REPO}.get_user_by_id", return_value=None):
            r = client.patch(f"{self.BASE}/9999/login-status", json={"is_online": True})
        assert r.status_code == 404


# ══════════════════════════════════════════════════════════════════════════════
# 8. Analytics — validation des paramètres (GET)
# ══════════════════════════════════════════════════════════════════════════════

_ANALYTICS_REPO = "app.repositories.analytics_repository.analytics_repository"


class TestAnalytics:
    BASE = "/api/v1/analytics"

    def test_formula_count_200(self, client):
        with patch(f"{_ANALYTICS_REPO}.get_formula_count_by_date", return_value=ANALYTICS_COUNT):
            r = client.get(f"{self.BASE}/formulas/count")
        assert r.status_code == 200
        assert r.json()["total"] == 42

    def test_formula_count_invalid_group_by_400(self, client):
        r = client.get(f"{self.BASE}/formulas/count", params={"group_by": "week"})
        assert r.status_code == 400

    def test_formula_count_bad_date_format_400(self, client):
        r = client.get(f"{self.BASE}/formulas/count", params={"date_from": "01/01/2024"})
        assert r.status_code == 400

    def test_formula_count_inverted_dates_400(self, client):
        r = client.get(
            f"{self.BASE}/formulas/count",
            params={"date_from": "2024-12-31", "date_to": "2024-01-01"},
        )
        assert r.status_code == 400

    def test_formula_count_valid_range_200(self, client):
        with patch(f"{_ANALYTICS_REPO}.get_formula_count_by_date", return_value=ANALYTICS_COUNT):
            r = client.get(
                f"{self.BASE}/formulas/count",
                params={"date_from": "2024-01-01", "date_to": "2024-12-31"},
            )
        assert r.status_code == 200


# ══════════════════════════════════════════════════════════════════════════════
# 9. Crash resilience — DB qui plante → 500 JSON, l'app continue
# ══════════════════════════════════════════════════════════════════════════════


class TestCrashResilience:
    def test_customers_list_db_down_500(self, client):
        with patch(f"{_CUST_REPO}.get_all_customers", side_effect=RuntimeError("DB is down")):
            r = client.get("/api/v1/customers")
        assert r.status_code == 500
        assert r.json() is not None  # Toujours du JSON

    def test_customers_create_db_down_500(self, client):
        with patch(f"{_CUST_REPO}.create_customer", side_effect=Exception("timeout")):
            r = client.post("/api/v1/customers", json={"first_name": "X"})
        assert r.status_code == 500

    def test_roles_list_db_down_500(self, client):
        with patch(f"{_ROLE_REPO}.get_all_roles", side_effect=Exception("crash")):
            r = client.get("/api/v1/roles/")
        assert r.status_code == 500

    def test_orders_create_db_down_500(self, client):
        with patch(f"{_ORDER_REPO}.create_order", side_effect=Exception("IO error")):
            r = client.post("/api/v1/orders/", json={"customer_id": 1, "formula_id": 1})
        assert r.status_code == 500

    def test_analytics_db_down_500(self, client):
        with patch(
            f"{_ANALYTICS_REPO}.get_formula_count_by_date", side_effect=Exception("timeout")
        ):
            r = client.get("/api/v1/analytics/formulas/count")
        assert r.status_code == 500


# ══════════════════════════════════════════════════════════════════════════════
# 10. Devices — POST / GET / PATCH
# ══════════════════════════════════════════════════════════════════════════════

_DEVICE_REPO = "app.repositories.device_repository"
FAKE_DEVICE = {
    "id": 1,
    "device_id": "tablet-01",
    "device_name": "Tablette Atelier A",
    "registered_at": "2024-01-01T00:00:00",
    "status": "approved",
}


class TestDevices:
    BASE = "/api/v1/devices"

    def test_register_device_200(self, client):
        with patch(f"{_DEVICE_REPO}.register_device", return_value=FAKE_DEVICE):
            r = client.post(
                f"{self.BASE}/register",
                json={"device_id": "tablet-01", "device_name": "Tablette A"},
            )
        assert r.status_code == 200
        assert r.json()["device_id"] == "tablet-01"

    def test_register_device_500_on_failure(self, client):
        with patch(f"{_DEVICE_REPO}.register_device", return_value=None):
            r = client.post(f"{self.BASE}/register", json={"device_id": "tablet-01"})
        assert r.status_code == 500

    def test_register_device_missing_field_422(self, client):
        r = client.post(f"{self.BASE}/register", json={})
        assert r.status_code == 422

    def test_verify_device_approved_authorized(self, client):
        with patch(f"{_DEVICE_REPO}.verify_device", return_value=FAKE_DEVICE):
            r = client.post(f"{self.BASE}/verify", json={"device_id": "tablet-01"})
        assert r.status_code == 200
        assert r.json()["authorized"] is True

    def test_verify_device_unknown_unauthorized(self, client):
        with patch(f"{_DEVICE_REPO}.verify_device", return_value=None):
            r = client.post(f"{self.BASE}/verify", json={"device_id": "tablet-unknown"})
        assert r.status_code == 200
        assert r.json()["authorized"] is False

    def test_list_devices_200(self, client):
        with patch(f"{_DEVICE_REPO}.get_all_devices", return_value=[FAKE_DEVICE]):
            r = client.get(self.BASE)
        assert r.status_code == 200
        assert len(r.json()) == 1

    def test_approve_device_200(self, client):
        with patch(f"{_DEVICE_REPO}.approve_device", return_value=True):
            r = client.patch(f"{self.BASE}/1/approve")
        assert r.status_code == 200
        assert r.json()["status"] == "approved"

    def test_approve_device_404(self, client):
        with patch(f"{_DEVICE_REPO}.approve_device", return_value=False):
            r = client.patch(f"{self.BASE}/9999/approve")
        assert r.status_code == 404

    def test_reject_device_200(self, client):
        with patch(f"{_DEVICE_REPO}.reject_device", return_value=True):
            r = client.patch(f"{self.BASE}/1/reject")
        assert r.status_code == 200
        assert r.json()["status"] == "rejected"

    def test_reject_device_404(self, client):
        with patch(f"{_DEVICE_REPO}.reject_device", return_value=False):
            r = client.patch(f"{self.BASE}/9999/reject")
        assert r.status_code == 404

    def test_rename_device_200(self, client):
        with patch(f"{_DEVICE_REPO}.rename_device", return_value=True):
            r = client.patch(f"{self.BASE}/1/rename", json={"device_name": "Nouveau Nom"})
        assert r.status_code == 200
        assert r.json()["device_name"] == "Nouveau Nom"

    def test_rename_device_404(self, client):
        with patch(f"{_DEVICE_REPO}.rename_device", return_value=False):
            r = client.patch(f"{self.BASE}/9999/rename", json={"device_name": "Nouveau Nom"})
        assert r.status_code == 404


# ══════════════════════════════════════════════════════════════════════════════
# 11. Customer Reviews — GET / POST / PUT / DELETE
# ══════════════════════════════════════════════════════════════════════════════

_REVIEW_REPO = "app.repositories.customer_review_repository.customer_review_repository"
FAKE_REVIEW = {
    "id": 1,
    "last_name": "Martin",
    "first_name": "Sophie",
    "email": "sophie@example.com",
    "phone": "+33612345678",
    "job": None,
    "country": "France",
    "city": "Paris",
    "date": "2024-01-01",
    "type": "atelier",
    "v2": False,
    "verified_email": "1",
    "verified_domain": "1",
    "verified_phone": "0",
    "formulas": [],
}


class TestCustomerReviews:
    BASE = "/api/v1/customer-reviews"

    def test_create_review_200(self, client):
        with (
            patch(f"{_REVIEW_REPO}.insert_customer_review", return_value=1),
            patch(f"{_REVIEW_REPO}.get_customer_review_by_id", return_value=FAKE_REVIEW),
        ):
            r = client.post(
                f"{self.BASE}/",
                json={"first_name": "Sophie", "type": "atelier"},
            )
        assert r.status_code == 200
        assert r.json()["id"] == 1

    def test_create_review_missing_type_422(self, client):
        """Le champ 'type' est requis dans CustomerReviewBase."""
        r = client.post(f"{self.BASE}/", json={"first_name": "Sophie"})
        assert r.status_code == 422

    def test_create_review_500_on_db_failure(self, client):
        with patch(f"{_REVIEW_REPO}.insert_customer_review", return_value=None):
            r = client.post(
                f"{self.BASE}/",
                json={"first_name": "Sophie", "type": "atelier"},
            )
        assert r.status_code == 500

    def test_list_reviews_200(self, client):
        with patch(
            f"{_REVIEW_REPO}.get_all_customer_reviews",
            return_value=([FAKE_REVIEW], 1),
        ):
            r = client.get(f"{self.BASE}/")
        assert r.status_code == 200
        assert r.json()["total"] == 1

    def test_list_reviews_page_zero_422(self, client):
        r = client.get(f"{self.BASE}/", params={"page": 0})
        assert r.status_code == 422

    def test_get_review_by_id_200(self, client):
        with patch(f"{_REVIEW_REPO}.get_customer_review_by_id", return_value=FAKE_REVIEW):
            r = client.get(f"{self.BASE}/1")
        assert r.status_code == 200
        assert r.json()["first_name"] == "Sophie"

    def test_get_review_by_id_404(self, client):
        with patch(f"{_REVIEW_REPO}.get_customer_review_by_id", return_value=None):
            r = client.get(f"{self.BASE}/9999")
        assert r.status_code == 404

    def test_update_review_200(self, client):
        updated = {**FAKE_REVIEW, "city": "Lyon"}
        with (
            patch(f"{_REVIEW_REPO}.get_customer_review_by_id", side_effect=[FAKE_REVIEW, updated]),
            patch(f"{_REVIEW_REPO}.update_customer_review_with_validation", return_value=True),
        ):
            r = client.put(f"{self.BASE}/1", json={"city": "Lyon"})
        assert r.status_code == 200

    def test_update_review_404(self, client):
        with patch(f"{_REVIEW_REPO}.get_customer_review_by_id", return_value=None):
            r = client.put(f"{self.BASE}/9999", json={"city": "Lyon"})
        assert r.status_code == 404

    def test_delete_review_200(self, client):
        with (
            patch(f"{_REVIEW_REPO}.get_customer_review_by_id", return_value=FAKE_REVIEW),
            patch(f"{_REVIEW_REPO}.delete_customer_review", return_value=True),
        ):
            r = client.delete(f"{self.BASE}/1")
        assert r.status_code == 200

    def test_delete_review_404(self, client):
        with patch(f"{_REVIEW_REPO}.get_customer_review_by_id", return_value=None):
            r = client.delete(f"{self.BASE}/9999")
        assert r.status_code == 404


# ══════════════════════════════════════════════════════════════════════════════
# 12. Tablet & Sessions — GET / POST / PATCH / PUT
# ══════════════════════════════════════════════════════════════════════════════

_SESSION_REPO = "app.repositories.session_repository"
FAKE_SESSION = {
    "id": 1,
    "customer_name": "Claire",
    "customer_email": "claire@example.com",
    "room": "Salle 1",
    "status": "active",
    "started_at": "2024-01-01T10:00:00",
}


class TestTabletAndSessions:
    def test_get_notes_catalog_200(self, client):
        """GET /api/v1/tablet/notes retourne les catégories tête/cœur/fond."""
        r = client.get("/api/v1/tablet/notes")
        assert r.status_code == 200
        body = r.json()
        assert "top_notes" in body
        assert "heart_notes" in body
        assert "base_notes" in body

    def test_create_session_200(self, client):
        with patch(f"{_SESSION_REPO}.create_session", return_value=42):
            r = client.post(
                "/api/v1/tablet/sessions",
                json={"customer_name": "Claire", "room": "Salle 1"},
            )
        assert r.status_code == 200
        assert r.json()["session_id"] == 42

    def test_create_session_500_on_failure(self, client):
        with patch(f"{_SESSION_REPO}.create_session", return_value=None):
            r = client.post("/api/v1/tablet/sessions", json={"customer_name": "Claire"})
        assert r.status_code == 500

    def test_list_active_sessions_200(self, client):
        with patch(f"{_SESSION_REPO}.get_active_sessions", return_value=[FAKE_SESSION]):
            r = client.get("/api/v1/tablet/sessions/active")
        assert r.status_code == 200
        assert len(r.json()) == 1

    def test_get_session_detail_200(self, client):
        with (
            patch(f"{_SESSION_REPO}.get_session_by_id", return_value=FAKE_SESSION),
            patch(
                f"{_SESSION_REPO}.get_answers",
                return_value=[{"question_key": "q1", "answer_value": "Rose"}],
            ),
        ):
            r = client.get("/api/v1/tablet/sessions/1")
        assert r.status_code == 200
        body = r.json()
        assert body["session"]["id"] == 1
        assert len(body["answers"]) == 1

    def test_get_session_detail_404(self, client):
        with patch(f"{_SESSION_REPO}.get_session_by_id", return_value=None):
            r = client.get("/api/v1/tablet/sessions/9999")
        assert r.status_code == 404

    def test_cancel_session_200(self, client):
        with patch(f"{_SESSION_REPO}.update_session_status", return_value=True):
            r = client.patch("/api/v1/tablet/sessions/1/cancel")
        assert r.status_code == 200
        assert r.json()["status"] == "cancelled"

    def test_cancel_session_404(self, client):
        with patch(f"{_SESSION_REPO}.update_session_status", return_value=False):
            r = client.patch("/api/v1/tablet/sessions/9999/cancel")
        assert r.status_code == 404

    def test_complete_session_200(self, client):
        with patch(f"{_SESSION_REPO}.update_session_status", return_value=True):
            r = client.patch("/api/v1/tablet/sessions/1/complete")
        assert r.status_code == 200
        assert r.json()["status"] == "completed"

    def test_complete_session_404(self, client):
        with patch(f"{_SESSION_REPO}.update_session_status", return_value=False):
            r = client.patch("/api/v1/tablet/sessions/9999/complete")
        assert r.status_code == 404

    def test_assign_supervisor_200(self, client):
        with patch(f"{_SESSION_REPO}.assign_supervisor_to_session", return_value=True):
            r = client.patch(
                "/api/v1/tablet/sessions/1/assign-supervisor",
                json={"supervisor_id": 5},
            )
        assert r.status_code == 200
        assert r.json()["supervisor_id"] == 5

    def test_assign_supervisor_404(self, client):
        with patch(f"{_SESSION_REPO}.assign_supervisor_to_session", return_value=False):
            r = client.patch(
                "/api/v1/tablet/sessions/9999/assign-supervisor",
                json={"supervisor_id": 5},
            )
        assert r.status_code == 404

    def test_update_session_answers_200(self, client):
        with patch(f"{_SESSION_REPO}.upsert_answer", return_value=(True, None)):
            r = client.put(
                "/api/v1/tablet/sessions/1/answers",
                json={"answers": [{"question_key": "pref_floral", "answer_value": "yes"}]},
            )
        assert r.status_code == 200
        assert r.json()["status"] == "updated"


# ══════════════════════════════════════════════════════════════════════════════
# 13. OCR & Files — GET / POST
# ══════════════════════════════════════════════════════════════════════════════

_OCR_JOB_REPO = "app.repositories.ocr_job_repository.ocr_job_repository"
_FILE_REPO = "app.repositories.customer_file_repository.customer_file_repository"
FAKE_FILE = {
    "id": 1,
    "customer_id": 1,
    "customer_review_id": None,
    "file_path": "uploads/fiche1.pdf",
    "file_name": "fiche1.pdf",
    "file_type": "application/pdf",
    "file_size": 1024,
    "uploaded_at": "2024-01-01T10:00:00",
    "created_at": "2024-01-01T10:00:00",
    "updated_at": None,
}


class TestOCRAndFiles:
    def test_ocr_health_200(self, client):
        r = client.get("/api/v1/ocr/health")
        assert r.status_code == 200
        assert r.json()["status"] == "healthy"

    def test_ocr_job_status_200(self, client):
        fake_job = {"id": "job-123", "status": "completed", "total_pages": 1}
        with patch(f"{_OCR_JOB_REPO}.get_job", return_value=fake_job):
            r = client.get("/api/v1/ocr/jobs/job-123")
        assert r.status_code == 200
        assert r.json()["status"] == "completed"

    def test_ocr_job_not_found_404(self, client):
        with patch(f"{_OCR_JOB_REPO}.get_job", return_value=None):
            r = client.get("/api/v1/ocr/jobs/job-unknown")
        assert r.status_code == 404

    def test_upload_pdf_missing_file_422(self, client):
        """POST sans fichier attaché → FastAPI 422 Unprocessable Entity."""
        r = client.post("/api/v1/ocr/upload-pdf")
        assert r.status_code == 422

    def test_customer_files_200(self, client):
        with patch(f"{_FILE_REPO}.get_files_by_customer_id", return_value=[FAKE_FILE]):
            r = client.get("/api/v1/customers/1/files")
        assert r.status_code == 200
        body = r.json()
        assert body["total"] == 1

    def test_customer_files_500_on_error(self, client):
        with patch(
            f"{_FILE_REPO}.get_files_by_customer_id",
            side_effect=RuntimeError("disk error"),
        ):
            r = client.get("/api/v1/customers/1/files")
        assert r.status_code == 500

    def test_customer_review_files_200(self, client):
        with patch(
            f"{_FILE_REPO}.get_files_by_customer_review_id",
            return_value=[FAKE_FILE],
        ):
            r = client.get("/api/v1/customer-reviews/1/files")
        assert r.status_code == 200

    def test_get_file_info_200(self, client):
        with patch(f"{_FILE_REPO}.get_customer_file_by_id", return_value=FAKE_FILE):
            r = client.get("/api/v1/files/1")
        assert r.status_code == 200
        assert r.json()["file_name"] == "fiche1.pdf"

    def test_get_file_info_404(self, client):
        with patch(f"{_FILE_REPO}.get_customer_file_by_id", return_value=None):
            r = client.get("/api/v1/files/9999")
        assert r.status_code == 404


# ══════════════════════════════════════════════════════════════════════════════
# 14. Emails — POST
# ══════════════════════════════════════════════════════════════════════════════

_EMAIL_SENDER = "app.services.email.email_sender_service.email_sender_service"


class TestEmails:
    def test_send_test_email_200(self, client):
        with patch(
            f"{_EMAIL_SENDER}.send_test_email",
            return_value={"success": True, "message": "Email sent"},
        ):
            r = client.post("/api/v1/emails/test", json={"to_email": "test@example.com"})
        assert r.status_code == 200
        assert r.json()["success"] is True

    def test_send_test_email_failed_400(self, client):
        with patch(
            f"{_EMAIL_SENDER}.send_test_email",
            return_value={"success": False, "message": "Domain invalid"},
        ):
            r = client.post("/api/v1/emails/test", json={"to_email": "bad@example.com"})
        assert r.status_code == 400

    def test_send_test_email_missing_body_422(self, client):
        r = client.post("/api/v1/emails/test", json={})
        assert r.status_code == 422

    def test_preview_pyramid_email_missing_params_422(self, client):
        """Sans reference ni formula_id, _get_pyramid_data renvoie 422."""
        r = client.post("/api/v1/emails/pyramid/preview", json={})
        assert r.status_code == 422


# ══════════════════════════════════════════════════════════════════════════════
# 15. Global Error & Edge Case Handling (Crash Resistance)
# ══════════════════════════════════════════════════════════════════════════════


class TestGlobalErrorHandling:
    def test_non_existent_route_returns_404(self, client):
        r = client.get("/api/v1/unknown-endpoint-404")
        assert r.status_code == 404

    def test_method_not_allowed_returns_405(self, client):
        """DELETE sur /health renvoie 405 Method Not Allowed."""
        r = client.delete("/health")
        assert r.status_code == 405

    def test_malformed_json_returns_422(self, client):
        """Envoi de syntaxe JSON invalide."""
        r = client.post(
            "/api/v1/customers",
            content="not a valid json{",
            headers={"Content-Type": "application/json"},
        )
        assert r.status_code == 422
