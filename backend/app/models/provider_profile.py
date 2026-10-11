from datetime import datetime, timezone

from app.extensions import db


class ProviderProfile(db.Model):
    """
    Professional profile for a service provider/trainer.

    A PROVIDER user has one ProviderProfile.
    """

    __tablename__ = "provider_profiles"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey(
            "users.id",
            ondelete="CASCADE"
        ),
        unique=True,
        nullable=False,
        index=True
    )

    bio = db.Column(
        db.Text,
        nullable=True
    )

    qualification = db.Column(
        db.String(255),
        nullable=True
    )

    experience_years = db.Column(
        db.Integer,
        nullable=True
    )

    specialization = db.Column(
        db.String(255),
        nullable=True
    )

    service_city = db.Column(
        db.String(100),
        nullable=True
    )

    verification_status = db.Column(
        db.String(20),
        nullable=False,
        default="PENDING"
    )

    is_available = db.Column(
        db.Boolean,
        nullable=False,
        default=False
    )

    created_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc)
    )

    updated_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    user = db.relationship(
        "User",
        back_populates="provider_profile"
    )

    provider_services = db.relationship(
        "ProviderService",
        back_populates="provider",
        cascade="all, delete-orphan",
        lazy=True
    )

    availability_slots = db.relationship(
        "ProviderAvailability",
        back_populates="provider",
        cascade="all, delete-orphan",
        lazy=True
    )

    def __repr__(self):
        return (
            f"<ProviderProfile "
            f"user_id={self.user_id} "
            f"status={self.verification_status}>"
        )