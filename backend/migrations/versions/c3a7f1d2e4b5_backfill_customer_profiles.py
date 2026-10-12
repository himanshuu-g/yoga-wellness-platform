"""Backfill customer profiles for existing customer accounts.

Revision ID: c3a7f1d2e4b5
Revises: 6e656586f003
"""

from alembic import op


# revision identifiers, used by Alembic.
revision = "c3a7f1d2e4b5"
down_revision = "6e656586f003"
branch_labels = None
depends_on = None


def upgrade():
    op.execute(
        """
        INSERT INTO customer_profiles (
            user_id,
            created_at,
            updated_at
        )
        SELECT
            users.id,
            CURRENT_TIMESTAMP,
            CURRENT_TIMESTAMP
        FROM users
        WHERE users.role = 'CUSTOMER'
          AND NOT EXISTS (
              SELECT 1
              FROM customer_profiles
              WHERE customer_profiles.user_id = users.id
          )
        """
    )


def downgrade():
    # Existing profile data is intentionally preserved on downgrade.
    pass
