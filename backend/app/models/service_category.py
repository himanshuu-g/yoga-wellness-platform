from datetime import datetime, timezone

from app.extensions import db


class ServiceCategory(db.Model):
    """
    Main category for wellness services.

    Examples:
    Yoga
    Hydrotherapy
    Mud Therapy
    Massage Therapy
    """

    __tablename__ = "service_categories"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    name = db.Column(
        db.String(100),
        unique=True,
        nullable=False
    )

    slug = db.Column(
        db.String(120),
        unique=True,
        nullable=False,
        index=True
    )

    description = db.Column(
        db.Text,
        nullable=True
    )

    is_active = db.Column(
        db.Boolean,
        nullable=False,
        default=True
    )

    display_order = db.Column(
        db.Integer,
        nullable=False,
        default=0
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


    # ---------------------------------------------
    # Relationships
    # ---------------------------------------------
    services = db.relationship(
        "Service",
        back_populates="category",
        cascade="all, delete-orphan",
        lazy=True
    )


    def __repr__(self):
        return f"<ServiceCategory {self.name}>"