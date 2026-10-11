from datetime import datetime, timezone

from app.extensions import db


class CustomerProfile(db.Model):
    """
    Additional profile information for CUSTOMER users.

    Authentication information stays in the users table.
    Customer-specific information stays here.
    """

    __tablename__ = "customer_profiles"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True
    )

    date_of_birth = db.Column(
        db.Date,
        nullable=True
    )

    gender = db.Column(
        db.String(20),
        nullable=True
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

    # One customer profile belongs to one user.
    user = db.relationship(
        "User",
        back_populates="customer_profile"
    )

    def __repr__(self):
        return f"<CustomerProfile user_id={self.user_id}>"