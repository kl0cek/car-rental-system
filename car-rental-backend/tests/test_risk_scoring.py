"""Unit tests for the risk-scoring engine and its multiplier mapping.

These tests intentionally stub the SQLAlchemy session: the engine has no
SQL-specific behavior worth integration-testing here — the value of these
tests is pinning the deterministic ``Decimal`` math so future tweaks to the
algorithm don't silently shift scores.
"""

import uuid
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException

from app.models.incident import IncidentSeverity
from app.services import risk_scoring
from app.services.rental_service import compute_risk_multiplier
from app.services.risk_scoring import (
    NEUTRAL_BASELINE,
    compute_user_risk_score,
    recompute_and_persist,
)


def _make_db_with(*, completed_rentals: int, incidents: list[SimpleNamespace]) -> AsyncMock:
    """Return an AsyncMock session whose two queries yield the values we want.

    The first ``db.execute`` call inside ``compute_user_risk_score`` runs the
    "completed rentals count" query; the second fetches incidents (joined to
    rentals to filter out in-flight rentals). We replay those in order via
    ``side_effect``.
    """
    count_result = MagicMock()
    count_result.scalar_one.return_value = completed_rentals

    incidents_result = MagicMock()
    incidents_result.scalars.return_value = incidents

    db = AsyncMock()
    db.execute = AsyncMock(side_effect=[count_result, incidents_result])
    return db


@pytest.fixture
def now() -> datetime:
    # Fixed clock so age_days math is independent of wall time.
    return datetime(2026, 5, 10, 12, 0, 0, tzinfo=UTC)


class TestComputeUserRiskScore:
    async def test_new_user_returns_neutral_baseline(self, now):
        db = _make_db_with(completed_rentals=0, incidents=[])
        score = await compute_user_risk_score(db, uuid.uuid4(), now=now)
        assert score == NEUTRAL_BASELINE
        assert score == Decimal("50")

    async def test_single_minor_incident_30_days_ago(self, now):
        # Pinned: weight=4, factor=0.5**(30/365) ≈ 0.9446..., weighted ≈ 3.7785,
        # rate boost = weighted*5, score = 50 + 6*weighted, quantized to 0.01.
        incident = SimpleNamespace(
            severity=IncidentSeverity.MINOR,
            created_at=now - timedelta(days=30),
        )
        db = _make_db_with(completed_rentals=0, incidents=[incident])
        score = await compute_user_risk_score(db, uuid.uuid4(), now=now)
        assert score == Decimal("72.67")

    async def test_single_major_incident_730_days_ago(self, now):
        # 730 days = 2 half-lives → factor = 0.25; weighted = 30 * 0.25 = 7.5.
        # rate = 7.5 / max(0, 1) = 7.5; score = 50 + 7.5 + 7.5*5 = 95.00.
        incident = SimpleNamespace(
            severity=IncidentSeverity.MAJOR,
            created_at=now - timedelta(days=730),
        )
        db = _make_db_with(completed_rentals=0, incidents=[incident])
        score = await compute_user_risk_score(db, uuid.uuid4(), now=now)
        assert score == Decimal("95.00")

    async def test_loyalty_discount_applies_below_baseline(self, now):
        # 5 completed rentals, zero incidents → discount = min(5*2, 30) = 10.
        # Score = 50 - 10 = 40.00.
        db = _make_db_with(completed_rentals=5, incidents=[])
        score = await compute_user_risk_score(db, uuid.uuid4(), now=now)
        assert score == Decimal("40.00")
        assert score < NEUTRAL_BASELINE

    async def test_loyalty_discount_caps_at_max(self, now):
        # 100 clean rentals → cap kicks in: discount = LOYALTY_MAX_DISCOUNT (30).
        db = _make_db_with(completed_rentals=100, incidents=[])
        score = await compute_user_risk_score(db, uuid.uuid4(), now=now)
        assert score == Decimal("20.00")

    async def test_loyalty_does_not_apply_below_threshold(self, now):
        # 4 completed rentals is below LOYALTY_RENTAL_THRESHOLD (5) → no discount.
        db = _make_db_with(completed_rentals=4, incidents=[])
        score = await compute_user_risk_score(db, uuid.uuid4(), now=now)
        assert score == NEUTRAL_BASELINE

    async def test_score_clamped_to_100(self, now):
        # Many major incidents — make sure the upper clamp engages.
        incidents = [
            SimpleNamespace(
                severity=IncidentSeverity.MAJOR,
                created_at=now,
            )
            for _ in range(20)
        ]
        db = _make_db_with(completed_rentals=0, incidents=incidents)
        score = await compute_user_risk_score(db, uuid.uuid4(), now=now)
        assert score == Decimal("100.00")

    async def test_loyalty_discount_applies_when_weighted_below_epsilon(self, now):
        # A very old MINOR incident decays to a tiny residual (well below
        # LOYALTY_WEIGHTED_EPSILON=0.01). With 10 completed rentals, the
        # loyalty discount should still kick in — that's the S1 fix vs.
        # the previous strict-zero check.
        ancient = SimpleNamespace(
            severity=IncidentSeverity.MINOR,
            # ~20 half-lives back: 0.5**20 ≈ 9.5e-7 → weight*factor ≪ 0.01.
            created_at=now - timedelta(days=risk_scoring.HALF_LIFE_DAYS * 20),
        )
        db = _make_db_with(completed_rentals=10, incidents=[ancient])
        score = await compute_user_risk_score(db, uuid.uuid4(), now=now)
        # Discount of min(10*2, 30) = 20 → score ≈ 50 - 20 = 30.00 (the
        # weighted residual contribution is negligible).
        assert score < NEUTRAL_BASELINE
        assert score < Decimal("30.01")


class TestRecencyFactor:
    def test_zero_age_is_one(self):
        assert risk_scoring._recency_factor(0) == Decimal("1")

    def test_one_half_life_is_one_half(self):
        # Exactly one half-life → 0.5.
        assert risk_scoring._recency_factor(risk_scoring.HALF_LIFE_DAYS) == Decimal("0.5")

    def test_two_half_lives_is_one_quarter(self):
        assert risk_scoring._recency_factor(risk_scoring.HALF_LIFE_DAYS * 2) == Decimal("0.25")

    def test_negative_age_clamped_to_one(self):
        # Future-dated incidents (clock skew etc.) shouldn't blow up — treat as fresh.
        assert risk_scoring._recency_factor(-5) == Decimal("1")


class TestComputeRiskMultiplier:
    """Boundary tests for the piecewise multiplier mapping."""

    def test_none_is_neutral(self):
        assert compute_risk_multiplier(None) == Decimal("1.0000")

    def test_just_below_20_is_discount(self):
        assert compute_risk_multiplier(Decimal("19.99")) == Decimal("0.8000")

    def test_exactly_20_is_next_bucket(self):
        assert compute_risk_multiplier(Decimal("20")) == Decimal("0.9000")

    def test_just_below_40(self):
        assert compute_risk_multiplier(Decimal("39.99")) == Decimal("0.9000")

    def test_exactly_40_is_neutral(self):
        assert compute_risk_multiplier(Decimal("40")) == Decimal("1.0000")

    def test_just_below_60(self):
        assert compute_risk_multiplier(Decimal("59.99")) == Decimal("1.0000")

    def test_exactly_60_is_premium(self):
        assert compute_risk_multiplier(Decimal("60")) == Decimal("1.2000")

    def test_just_below_80(self):
        assert compute_risk_multiplier(Decimal("79.99")) == Decimal("1.2000")

    def test_exactly_80_is_max(self):
        assert compute_risk_multiplier(Decimal("80")) == Decimal("1.5000")

    def test_at_100_is_max(self):
        assert compute_risk_multiplier(Decimal("100")) == Decimal("1.5000")


class TestRecomputeAndPersist:
    async def test_writes_score_to_loaded_orm_instance_and_returns_it(self, now):
        # New behavior (B1 fix): load user via repository → mutate in place →
        # flush. We mock user_repository.get_by_id, then feed the two queries
        # inside compute_user_risk_score (count + incidents).
        user_id = uuid.uuid4()
        user_obj = SimpleNamespace(id=user_id, risk_score=Decimal("0.00"))

        count_result = MagicMock()
        count_result.scalar_one.return_value = 0
        incidents_result = MagicMock()
        incidents_result.scalars.return_value = []

        db = AsyncMock()
        db.execute = AsyncMock(side_effect=[count_result, incidents_result])
        db.flush = AsyncMock()

        with patch(
            "app.services.risk_scoring.user_repository.get_by_id",
            new_callable=AsyncMock,
            return_value=user_obj,
        ) as mock_get:
            score = await recompute_and_persist(db, user_id)

        # New-user path → neutral baseline.
        assert score == NEUTRAL_BASELINE
        # User was loaded via the repository (so the in-session instance stays
        # consistent — that's the whole point of the fix).
        mock_get.assert_awaited_once_with(db, user_id)
        # The score was written onto the loaded instance, not via Core UPDATE.
        assert user_obj.risk_score == NEUTRAL_BASELINE
        # Two execute() calls: count + incidents. No third UPDATE call.
        assert db.execute.await_count == 2
        db.flush.assert_awaited_once()

    async def test_raises_404_when_user_not_found(self):
        # B1 / B3: bogus user_id used to silently no-op via Core UPDATE.
        # ORM-load path raises 404 instead.
        db = AsyncMock()
        db.execute = AsyncMock()
        db.flush = AsyncMock()

        with patch(
            "app.services.risk_scoring.user_repository.get_by_id",
            new_callable=AsyncMock,
            return_value=None,
        ):
            with pytest.raises(HTTPException) as exc_info:
                await recompute_and_persist(db, uuid.uuid4())

        assert exc_info.value.status_code == 404
        assert exc_info.value.detail == "User not found"
        # Nothing was executed/flushed on the bogus path.
        db.execute.assert_not_called()
        db.flush.assert_not_called()
