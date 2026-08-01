"""
pytest tests for the Norms Library API.

Covered:
  1. Seed data loads correctly
  2. Duplicate creates an independent copy
  3. Editing a historical (published) version is rejected
  4. Publish demotes the old current version
"""
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.norms import (
    MaterialGrade,
    NormsVersion,
    ProcessRate,
    RmPriceBand,
    ScrapRate,
)


# ---------------------------------------------------------------------------
# 1. Seed data loads correctly
# ---------------------------------------------------------------------------

class TestSeedData:
    def test_seed_version_exists(self, db: Session):
        v = db.query(NormsVersion).filter_by(label="v4.5 (seed)").first()
        assert v is not None
        assert v.is_current is True
        assert v.is_draft is False

    def test_all_grades_present(self, db: Session):
        names = {g.name for g in db.query(MaterialGrade).all()}
        expected = {"IS2062 E250BR", "IS2062 E350C", "En8D", "Yst240", "ASTM A106 Gr B"}
        assert expected.issubset(names)

    def test_e350c_is_premium_derived(self, db: Session):
        e350c = db.query(MaterialGrade).filter_by(name="IS2062 E350C").first()
        e250br = db.query(MaterialGrade).filter_by(name="IS2062 E250BR").first()
        assert e350c.base_grade_id == e250br.id
        assert e350c.premium_amount == Decimal("5.0000")

    def test_rm_price_bands_count(self, db: Session):
        v = db.query(NormsVersion).filter_by(label="v4.5 (seed)").first()
        count = db.query(RmPriceBand).filter_by(norms_version_id=v.id).count()
        # 4 base-priced grades × 7 thickness bands
        assert count == 28

    def test_e250br_price_exact_decimal(self, db: Session):
        v = db.query(NormsVersion).filter_by(label="v4.5 (seed)").first()
        e250br = db.query(MaterialGrade).filter_by(name="IS2062 E250BR").first()
        band = (
            db.query(RmPriceBand)
            .filter_by(norms_version_id=v.id, grade_id=e250br.id, thickness_band="<10mm")
            .first()
        )
        assert band is not None
        assert band.price_per_kg == Decimal("56.9600")
        # Prove it's exact Decimal, not float
        assert type(band.price_per_kg) is Decimal

    def test_process_rates_count(self, db: Session):
        v = db.query(NormsVersion).filter_by(label="v4.5 (seed)").first()
        count = db.query(ProcessRate).filter_by(norms_version_id=v.id).count()
        assert count == 25

    def test_scrap_rate(self, db: Session):
        v = db.query(NormsVersion).filter_by(label="v4.5 (seed)").first()
        scrap = db.query(ScrapRate).filter_by(norms_version_id=v.id).first()
        assert scrap is not None
        assert scrap.rate_per_kg == Decimal("30.0000")

    def test_get_version_api(self, client: TestClient, db: Session):
        v = db.query(NormsVersion).filter_by(label="v4.5 (seed)").first()
        resp = client.get(f"/api/v1/norms/versions/{v.id}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["version"]["label"] == "v4.5 (seed)"
        assert data["version"]["is_current"] is True
        assert len(data["rm_price_bands"]) == 28
        assert len(data["process_rates"]) == 25
        assert len(data["overhead_params"]) == 3
        assert data["scrap_rate"]["rate_per_kg"] == "30.0000"

    def test_list_versions_api(self, client: TestClient):
        resp = client.get("/api/v1/norms/versions")
        assert resp.status_code == 200
        assert len(resp.json()) >= 1


# ---------------------------------------------------------------------------
# 2. Duplicate creates an independent copy
# ---------------------------------------------------------------------------

class TestDuplicate:
    def _seed_version_id(self, db: Session) -> int:
        return db.query(NormsVersion).filter_by(label="v4.5 (seed)").first().id

    def test_duplicate_returns_201(self, client: TestClient, db: Session):
        src_id = self._seed_version_id(db)
        resp = client.post(f"/api/v1/norms/versions/{src_id}/duplicate")
        assert resp.status_code == 201

    def test_duplicate_creates_draft(self, client: TestClient, db: Session):
        src_id = self._seed_version_id(db)
        resp = client.post(f"/api/v1/norms/versions/{src_id}/duplicate")
        data = resp.json()
        assert data["version"]["is_draft"] is True
        assert data["version"]["is_current"] is False

    def test_duplicate_copies_label(self, client: TestClient, db: Session):
        src_id = self._seed_version_id(db)
        resp = client.post(f"/api/v1/norms/versions/{src_id}/duplicate")
        assert "copy" in resp.json()["version"]["label"].lower()

    def test_duplicate_same_band_count(self, client: TestClient, db: Session):
        src_id = self._seed_version_id(db)
        src_bands = client.get(f"/api/v1/norms/versions/{src_id}").json()["rm_price_bands"]
        new_id = client.post(f"/api/v1/norms/versions/{src_id}/duplicate").json()["version"]["id"]
        new_bands = client.get(f"/api/v1/norms/versions/{new_id}").json()["rm_price_bands"]
        assert len(new_bands) == len(src_bands)

    def test_duplicate_is_independent(self, client: TestClient, db: Session):
        """Editing the duplicate must NOT affect the source version."""
        src_id = self._seed_version_id(db)
        new_id = client.post(f"/api/v1/norms/versions/{src_id}/duplicate").json()["version"]["id"]

        # Find a price band in the new version to update
        new_detail = client.get(f"/api/v1/norms/versions/{new_id}").json()
        band = new_detail["rm_price_bands"][0]
        original_price = band["price_per_kg"]

        new_price = str(Decimal(original_price) + Decimal("10.0000"))
        resp = client.patch(
            f"/api/v1/norms/versions/{new_id}/rm-prices",
            json={"price_updates": [{"grade_id": band["grade_id"], "thickness_band": band["thickness_band"], "price_per_kg": new_price}]},
        )
        assert resp.status_code == 200

        # Source version price must be unchanged
        src_detail = client.get(f"/api/v1/norms/versions/{src_id}").json()
        src_band = next(
            b for b in src_detail["rm_price_bands"]
            if b["grade_id"] == band["grade_id"] and b["thickness_band"] == band["thickness_band"]
        )
        assert src_band["price_per_kg"] == original_price


# ---------------------------------------------------------------------------
# 3. Editing a historical (published/demoted) version is rejected
# ---------------------------------------------------------------------------

class TestEditingLock:
    def test_editing_historical_rm_prices_rejected(self, client: TestClient, db: Session):
        src_id = db.query(NormsVersion).filter_by(label="v4.5 (seed)").first().id

        # Duplicate and publish the copy — this demotes v4.5 (seed) to historical
        new_id = client.post(f"/api/v1/norms/versions/{src_id}/duplicate").json()["version"]["id"]
        pub = client.post(f"/api/v1/norms/versions/{new_id}/publish")
        assert pub.status_code == 200

        # Now try to edit the original (now historical) version
        resp = client.patch(
            f"/api/v1/norms/versions/{src_id}/rm-prices",
            json={"price_updates": []},
        )
        assert resp.status_code == 409

    def test_editing_historical_process_rates_rejected(self, client: TestClient, db: Session):
        src_id = db.query(NormsVersion).filter_by(label="v4.5 (seed)").first().id
        new_id = client.post(f"/api/v1/norms/versions/{src_id}/duplicate").json()["version"]["id"]
        client.post(f"/api/v1/norms/versions/{new_id}/publish")

        rate_id = client.get(f"/api/v1/norms/versions/{src_id}").json()["process_rates"][0]["id"]
        resp = client.patch(
            f"/api/v1/norms/versions/{src_id}/process-rates",
            json={"rates": [{"id": rate_id, "rate": "99.00"}]},
        )
        assert resp.status_code == 409

    def test_editing_historical_overhead_rejected(self, client: TestClient, db: Session):
        src_id = db.query(NormsVersion).filter_by(label="v4.5 (seed)").first().id
        new_id = client.post(f"/api/v1/norms/versions/{src_id}/duplicate").json()["version"]["id"]
        client.post(f"/api/v1/norms/versions/{new_id}/publish")

        resp = client.patch(
            f"/api/v1/norms/versions/{src_id}/overhead-params",
            json={"params": [{"applies_to": "raw_material", "overhead_pct": "99.00"}]},
        )
        assert resp.status_code == 409

    def test_publishing_already_current_rejected(self, client: TestClient, db: Session):
        src_id = db.query(NormsVersion).filter_by(label="v4.5 (seed)").first().id
        resp = client.post(f"/api/v1/norms/versions/{src_id}/publish")
        assert resp.status_code == 409


# ---------------------------------------------------------------------------
# 4. Publish demotes the old current version
# ---------------------------------------------------------------------------

class TestPublish:
    def test_publish_makes_draft_current(self, client: TestClient, db: Session):
        src_id = db.query(NormsVersion).filter_by(label="v4.5 (seed)").first().id
        new_id = client.post(f"/api/v1/norms/versions/{src_id}/duplicate").json()["version"]["id"]

        resp = client.post(f"/api/v1/norms/versions/{new_id}/publish")
        assert resp.status_code == 200
        data = resp.json()
        assert data["version"]["is_current"] is True
        assert data["version"]["is_draft"] is False

    def test_publish_demotes_previous_current(self, client: TestClient, db: Session):
        src_id = db.query(NormsVersion).filter_by(label="v4.5 (seed)").first().id
        new_id = client.post(f"/api/v1/norms/versions/{src_id}/duplicate").json()["version"]["id"]
        client.post(f"/api/v1/norms/versions/{new_id}/publish")

        # Old version must no longer be current
        resp = client.get(f"/api/v1/norms/versions/{src_id}")
        data = resp.json()
        assert data["version"]["is_current"] is False
        assert data["version"]["is_draft"] is False

    def test_only_one_current_after_publish(self, client: TestClient, db: Session):
        src_id = db.query(NormsVersion).filter_by(label="v4.5 (seed)").first().id
        new_id = client.post(f"/api/v1/norms/versions/{src_id}/duplicate").json()["version"]["id"]
        client.post(f"/api/v1/norms/versions/{new_id}/publish")

        versions = client.get("/api/v1/norms/versions").json()
        current_count = sum(1 for v in versions if v["is_current"])
        assert current_count == 1

    def test_version_list_shows_history(self, client: TestClient, db: Session):
        src_id = db.query(NormsVersion).filter_by(label="v4.5 (seed)").first().id
        client.post(f"/api/v1/norms/versions/{src_id}/duplicate")

        versions = client.get("/api/v1/norms/versions").json()
        assert len(versions) >= 2

    def test_publish_nonexistent_version_404(self, client: TestClient):
        resp = client.post("/api/v1/norms/versions/99999/publish")
        assert resp.status_code == 404
