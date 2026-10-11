from datetime import datetime, timezone

from app.extensions import db


class ProviderAvailability(db.Model):
    """
    Weekly recurring availability for a provider.

    Example:
    Monday 09:00 - 12:00
    Monday 16:00 - 19:00
    """

    __tablename__ = "provider_availability"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    provider_id = db.Column(
        db.Integer,
        db.ForeignKey(
            "provider_profiles.id",
            ondelete="CASCADE"
        ),
        nullable=False,
        index=True
    )

    day_of_week = db.Column(
        db.Integer,
        nullable=False
    )

    start_time = db.Column(
        db.Time,
        nullable=False
    )

    end_time = db.Column(
        db.Time,
        nullable=False
    )

    is_active = db.Column(
        db.Boolean,
        nullable=False,
        default=True
    )

    created_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc)
    )

    provider = db.relationship(
        "ProviderProfile",
        back_populates="availability_slots"
    )

    def __repr__(self):
        return (
            f"<ProviderAvailability "
            f"provider={self.provider_id} "
            f"day={self.day_of_week}>"
        )