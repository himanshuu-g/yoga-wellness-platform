from datetime import datetime, timezone

from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

from app.extensions import db


class User(UserMixin, db.Model):
    """
    Main user account model.

    Roles:
    CUSTOMER
    PROVIDER
    ADMIN
    """

    __tablename__ = "users"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    name = db.Column(
        db.String(100),
        nullable=False
    )

    email = db.Column(
        db.String(255),
        unique=True,
        nullable=False,
        index=True
    )

    phone = db.Column(
        db.String(20),
        unique=True,
        nullable=True,
        index=True
    )

    password_hash = db.Column(
        db.String(255),
        nullable=False
    )

    role = db.Column(
        db.String(20),
        nullable=False,
        default="CUSTOMER"
    )

    is_active = db.Column(
        db.Boolean,
        nullable=False,
        default=True
    )

    email_verified = db.Column(
        db.Boolean,
        nullable=False,
        default=False
    )

    phone_verified = db.Column(
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
    
    # ---------------------------------------------
    # Relationships
    # ---------------------------------------------

    provider_profile = db.relationship(
        "ProviderProfile",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan"
    )

    customer_profile = db.relationship(
        "CustomerProfile",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan"
    )

    addresses = db.relationship(
        "Address",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy=True
    )

    def set_password(self, password):
        """
        Convert plain-text password into a secure hash.
        """
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """
        Compare login password against stored hash.
        """
        return check_password_hash(
            self.password_hash,
            password
        )

    def __repr__(self):
        return f"<User {self.email}>"