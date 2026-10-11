from datetime import datetime, timezone

from app.extensions import db


class ProviderService(db.Model):
    """
    Connects providers with services they offer.

    Allows provider-specific pricing and duration.
    """

    __tablename__ = "provider_services"

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

    service_id = db.Column(
        db.Integer,
        db.ForeignKey(
            "services.id",
            ondelete="CASCADE"
        ),
        nullable=False,
        index=True
    )

    price = db.Column(
        db.Numeric(10, 2),
        nullable=True
    )

    duration_minutes = db.Column(
        db.Integer,
        nullable=True
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
        back_populates="provider_services"
    )

    service = db.relationship(
        "Service",
        back_populates="provider_services"
    )

    __table_args__ = (
        db.UniqueConstraint(
            "provider_id",
            "service_id",
            name="uq_provider_service"
        ),
    )

    def __repr__(self):
        return (
            f"<ProviderService "
            f"provider={self.provider_id} "
            f"service={self.service_id}>"
        )