from datetime import datetime, timezone
from app.extensions import db


class Booking(db.Model):
    __tablename__ = "bookings"

    id = db.Column(db.Integer, primary_key=True)

    customer_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False,
        index=True
    )

    provider_id = db.Column(
        db.Integer,
        db.ForeignKey("provider_profiles.id"),
        nullable=False,
        index=True
    )

    service_id = db.Column(
        db.Integer,
        db.ForeignKey("services.id"),
        nullable=False
    )

    address_id = db.Column(
        db.Integer,
        db.ForeignKey("addresses.id"),
        nullable=True
    )

    booking_date = db.Column(
        db.Date,
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

    total_price = db.Column(
        db.Numeric(10, 2),
        nullable=False
    )

    status = db.Column(
        db.String(20),
        nullable=False,
        default="PENDING"
    )

    customer_notes = db.Column(
        db.Text,
        nullable=True
    )

    created_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    customer = db.relationship(
        "User",
        foreign_keys=[customer_id]
    )

    provider = db.relationship(
        "ProviderProfile"
    )

    service = db.relationship(
        "Service"
    )

    address = db.relationship(
        "Address"
    )