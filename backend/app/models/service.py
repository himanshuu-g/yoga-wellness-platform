from datetime import datetime, timezone

from app.extensions import db


class Service(db.Model):
    """
    Individual bookable wellness service.
    """

    __tablename__ = "services"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    category_id = db.Column(
        db.Integer,
        db.ForeignKey(
            "service_categories.id",
            ondelete="CASCADE"
        ),
        nullable=False,
        index=True
    )

    name = db.Column(
        db.String(150),
        nullable=False
    )

    slug = db.Column(
        db.String(170),
        unique=True,
        nullable=False,
        index=True
    )

    short_description = db.Column(
        db.String(300),
        nullable=True
    )

    description = db.Column(
        db.Text,
        nullable=True
    )

    duration_minutes = db.Column(
        db.Integer,
        nullable=True
    )

    base_price = db.Column(
        db.Numeric(10, 2),
        nullable=True
    )

    service_mode = db.Column(
        db.String(30),
        nullable=False,
        default="HOME"
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
    
    category = db.relationship(
        "ServiceCategory",
        back_populates="services"
    )

    provider_services = db.relationship(
        "ProviderService",
        back_populates="service",
        cascade="all, delete-orphan",
        lazy=True
    )

    def __repr__(self):
        return f"<Service {self.name}>"