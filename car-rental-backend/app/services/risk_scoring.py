"""Risk-scoring engine for DriveEase customers.

Computes a 0..100 risk score for a user from their incident history and
rental volume. The score is event-driven: every completed return triggers
a recompute via ``recompute_and_persist`` so the next rental's price
multiplier reflects the latest state.

Higher score → riskier customer → larger price multiplier. The mapping
from score to multiplier lives in
:func:`app.services.rental_service.compute_risk_multiplier`.

All arithmetic uses :class:`decimal.Decimal` to avoid floating-point
drift in money-adjacent values.
"""

import uuid
from datetime import UTC, datetime
from decimal import Decimal

import sqlalchemy as sa
from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.incident import Incident, IncidentSeverity
from app.models.rental import Rental, Reservation
from app.repositories import user_repository

SEVERITY_WEIGHT: dict[IncidentSeverity, Decimal] = {
    IncidentSeverity.MINOR: Decimal("4"),
    IncidentSeverity.MODERATE: Decimal("12"),
    IncidentSeverity.MAJOR: Decimal("30"),
}

# Recency: an incident's contribution halves every HALF_LIFE_DAYS.
HALF_LIFE_DAYS = 365

# Score assigned to brand-new users / users with no history.
NEUTRAL_BASELINE = Decimal("50")

# A customer is eligible for the loyalty discount only after this many
# completed rentals with zero (decay-weighted) incidents.
LOYALTY_RENTAL_THRESHOLD = 5

# Hard cap on the loyalty discount magnitude.
LOYALTY_MAX_DISCOUNT = Decimal("30")

# Multiplier applied to incidents-per-rental, amplifying the effect of
# repeat-offender patterns vs. one-off incidents.
RATE_BOOST_MULTIPLIER = Decimal("5")

# Treat a decay-weighted incident total below this epsilon as "effectively
# clean" for loyalty-discount eligibility. Using strict-zero would mean a
# very old/decayed incident (e.g. weighted = 0.0001) silently disqualifies
# an otherwise-clean long-time customer; the epsilon makes the boundary
# robust to recency decay.
LOYALTY_WEIGHTED_EPSILON = Decimal("0.01")


def _recency_factor(age_days: int) -> Decimal:
    """Exponential half-life decay: 0.5 ** (age_days / HALF_LIFE_DAYS).

    Pure ``Decimal`` math — no float — so the score is reproducible
    across platforms.
    """
    if age_days <= 0:
        return Decimal("1")
    exponent = Decimal(age_days) / Decimal(HALF_LIFE_DAYS)
    return Decimal("0.5") ** exponent


async def compute_user_risk_score(
    db: AsyncSession,
    user_id: uuid.UUID,
    *,
    now: datetime | None = None,
) -> Decimal:
    """Score 0..100. NEUTRAL_BASELINE for users with no history.

    Higher = riskier. Weighted by severity, decayed by recency, offset by
    rental volume (more clean rentals → near-zero weighted incidents lowers
    the score via the loyalty discount).
    """
    current_time = now or datetime.now(UTC)

    # Completed rentals = rentals with a non-null return_date that belong to
    # a reservation owned by this user.
    completed_rentals = (
        await db.execute(
            select(func.count(Rental.id))
            .join(Reservation, Rental.reservation_id == Reservation.id)
            .where(
                Rental.return_date.is_not(None),
                Reservation.user_id == user_id,
            )
        )
    ).scalar_one()

    # Only count incidents that (a) are not tied to a specific rental
    # (e.g. complaints) or (b) are tied to a rental that has actually been
    # completed. In-flight rentals are excluded from ``completed_rentals``
    # above, so counting their incidents here would inflate the rate.
    incidents_result = await db.execute(
        select(Incident)
        .outerjoin(Rental, Incident.rental_id == Rental.id)
        .where(
            Incident.customer_id == user_id,
            sa.or_(Incident.rental_id.is_(None), Rental.return_date.is_not(None)),
        )
    )
    incidents = list(incidents_result.scalars())

    if not incidents and completed_rentals == 0:
        return NEUTRAL_BASELINE

    weighted = Decimal("0")
    for incident in incidents:
        age_days = (current_time - incident.created_at).days
        weight = SEVERITY_WEIGHT[incident.severity]
        weighted += weight * _recency_factor(age_days)

    divisor = Decimal(max(completed_rentals, 1))
    rate = weighted / divisor
    score = NEUTRAL_BASELINE + weighted + rate * RATE_BOOST_MULTIPLIER

    # Loyalty discount: near-clean history + enough rentals to be a "regular".
    # Use an epsilon rather than strict-zero so a tiny decayed residual from
    # an ancient incident doesn't silently disqualify a long-time customer.
    if weighted < LOYALTY_WEIGHTED_EPSILON and completed_rentals >= LOYALTY_RENTAL_THRESHOLD:
        discount = min(
            Decimal(completed_rentals) * Decimal("2"),
            LOYALTY_MAX_DISCOUNT,
        )
        score -= discount

    # Clamp to [0, 100] and quantize to 2 decimals.
    score = max(Decimal("0"), min(Decimal("100"), score))
    return score.quantize(Decimal("0.01"))


async def recompute_and_persist(db: AsyncSession, user_id: uuid.UUID) -> Decimal:
    """Recompute and write ``User.risk_score``. Returns the new score.

    Uses the ORM path (load → mutate → flush) rather than a Core UPDATE so
    that any already-loaded ``User`` instance in the same session keeps a
    consistent ``risk_score``. Raises 404 if the user does not exist —
    important when this is invoked from event hooks where a bogus
    ``user_id`` would otherwise silently no-op.
    """
    user = await user_repository.get_by_id(db, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    new_score = await compute_user_risk_score(db, user_id)
    user.risk_score = new_score
    await db.flush()
    return new_score
