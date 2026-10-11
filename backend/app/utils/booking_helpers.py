from datetime import datetime, timedelta
from decimal import Decimal
from zoneinfo import ZoneInfo

from app.extensions import db
from app.models.booking import Booking
from app.models.provider_availability import ProviderAvailability


BOOKING_TIMEZONE = ZoneInfo("Asia/Kolkata")

BLOCKING_STATUSES = ("PENDING", "CONFIRMED")


def calculate_end_time(booking_date, start_time, duration_minutes):
    """Calculate the session end, disallowing overnight sessions."""

    start_dt = datetime.combine(booking_date, start_time)
    end_dt = start_dt + timedelta(minutes=duration_minutes)

    if end_dt.date() != booking_date:
        return None

    return end_dt.time()


def provider_is_available(
    provider_id,
    booking_date,
    start_time,
    end_time
):
    """Check that the session fits an active weekly window."""

    day = booking_date.weekday()

    slot = db.session.execute(
        db.select(ProviderAvailability).where(
            ProviderAvailability.provider_id == provider_id,
            ProviderAvailability.day_of_week == day,
            ProviderAvailability.is_active.is_(True),
            ProviderAvailability.start_time <= start_time,
            ProviderAvailability.end_time >= end_time
        )
    ).scalars().first()

    return slot is not None


def booking_conflicts(
    provider_id,
    booking_date,
    start_time,
    end_time
):
    """Check overlapping pending or confirmed bookings."""

    conflict = db.session.execute(
        db.select(Booking.id).where(
            Booking.provider_id == provider_id,
            Booking.booking_date == booking_date,
            Booking.status.in_(BLOCKING_STATUSES),
            Booking.start_time < end_time,
            Booking.end_time > start_time
        ).limit(1)
    ).first()

    return conflict is not None


def get_booking_price(provider_service):
    """Use provider price first, otherwise catalog price."""

    if provider_service.price is not None:
        return Decimal(str(provider_service.price))

    if provider_service.service.base_price is not None:
        return Decimal(str(provider_service.service.base_price))

    return None


def get_booking_duration(provider_service):
    """Use provider duration first, otherwise catalog duration."""

    return (
        provider_service.duration_minutes
        or provider_service.service.duration_minutes
    )