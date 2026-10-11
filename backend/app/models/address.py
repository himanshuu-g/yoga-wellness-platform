from datetime import datetime, timezone

from app.extensions import db


class Address(db.Model):
    """
    Stores customer service addresses.

    A user can save multiple addresses such as:
    Home, Office, Parents' Home, etc.
    """

    __tablename__ = "addresses"
    
    id = db.Column(
        db.Integer,
        primary_key=True
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    label = db.Column(
        db.String(50),
        nullable=False,
        default="Home"
    )

    address_line_1 = db.Column(
        db.String(255),
        nullable=False
    )

    address_line_2 = db.Column(
        db.String(255),
        nullable=True
    )

    locality = db.Column(
        db.String(100),
        nullable=False
    )

    city = db.Column(
        db.String(100),
        nullable=False
    )

    state = db.Column(
        db.String(100),
        nullable=False
    )

    postal_code = db.Column(
        db.String(10),
        nullable=False
    )

    landmark = db.Column(
        db.String(255),
        nullable=True
    )

    is_default = db.Column(
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

    user = db.relationship(
        "User",
        back_populates="addresses"
    )

    def __repr__(self):
        return f"<Address {self.label} user_id={self.user_id}>"