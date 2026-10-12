from datetime import date, datetime
from zoneinfo import ZoneInfo

from flask import (
    render_template,
    request,
    redirect,
    url_for,
    flash,
    abort
)

from flask_login import login_required, current_user

from app.extensions import db
from app.bookings import bookings_bp

from app.models.booking import Booking
from app.models.service import Service
from app.models.provider_service import ProviderService
from app.models.address import Address

from app.utils.booking_helpers import (
    BOOKING_TIMEZONE,
    calculate_end_time,
    provider_is_available,
    booking_conflicts,
    get_booking_price,
    get_booking_duration
)
from app.models.provider_profile import ProviderProfile
from app.models.user import User

# =================================================
# CUSTOMER BOOKING FORM
# =================================================

@bookings_bp.route(
    "/new/<int:service_id>",
    methods=["GET", "POST"]
)
@login_required
def new_booking(service_id):

    if current_user.role != "CUSTOMER":
        abort(403)

    service = db.session.get(Service, service_id)

    if (
        service is None
        or not service.is_active
        or not service.category.is_active
    ):
        abort(404)

    # Approved providers offering this service.
    provider_services = db.session.execute(
        db.select(ProviderService)
        .join(
            ProviderProfile,
            ProviderService.provider_id == ProviderProfile.id
        )
        .join(
            User,
            ProviderProfile.user_id == User.id
        )
        .where(
            ProviderService.service_id == service.id,
            ProviderService.is_active.is_(True),
            ProviderProfile.verification_status == "APPROVED",
            ProviderProfile.is_available.is_(True),
            User.role == "PROVIDER",
            User.is_active.is_(True)
        )
    ).scalars().all()
    # Customer's saved addresses.
    addresses = db.session.execute(
        db.select(Address).where(
            Address.user_id == current_user.id
        )
    ).scalars().all()

    if request.method == "POST":

        try:
            provider_service_id = int(
                request.form.get("provider_service_id", "")
            )

            booking_date = date.fromisoformat(
                request.form.get("booking_date", "")
            )

            start_time = datetime.strptime(
                request.form.get("start_time", ""),
                "%H:%M"
            ).time()

        except (ValueError, TypeError):

            flash(
                "Please enter valid booking details.",
                "error"
            )

            return redirect(
                url_for(
                    "bookings.new_booking",
                    service_id=service.id
                )
            )

        provider_service = db.session.get(
            ProviderService,
            provider_service_id
        )

        # Never trust provider IDs supplied by the browser.
        if (
            provider_service is None
            or provider_service.service_id != service.id
            or not provider_service.is_active
        ):
            abort(400)

        provider = provider_service.provider

        if (
            provider.verification_status != "APPROVED"
            or not provider.is_available
            or provider.user.role != "PROVIDER"
            or not provider.user.is_active
        ):

            flash(
                "This provider is currently unavailable.",
                "error"
            )

            return redirect(
                url_for(
                    "bookings.new_booking",
                    service_id=service.id
                )
            )

        # Do not allow bookings in the past.
        now = datetime.now(BOOKING_TIMEZONE)

        booking_start = datetime.combine(
            booking_date,
            start_time,
            tzinfo=BOOKING_TIMEZONE
        )

        if booking_start <= now:

            flash(
                "Please choose a future date and time.",
                "error"
            )

            return redirect(
                url_for(
                    "bookings.new_booking",
                    service_id=service.id
                )
            )

        duration = get_booking_duration(provider_service)
        price = get_booking_price(provider_service)

        if duration is None or duration <= 0:

            flash(
                "This service has no valid session duration.",
                "error"
            )

            return redirect(
                url_for(
                    "bookings.new_booking",
                    service_id=service.id
                )
            )

        if price is None or not price.is_finite() or price < 0:

            flash(
                "This service has no valid booking price.",
                "error"
            )

            return redirect(
                url_for(
                    "bookings.new_booking",
                    service_id=service.id
                )
            )

        end_time = calculate_end_time(
            booking_date,
            start_time,
            duration
        )

        if end_time is None:

            flash(
                "The session cannot extend into the next day.",
                "error"
            )

            return redirect(
                url_for(
                    "bookings.new_booking",
                    service_id=service.id
                )
            )

        if not provider_is_available(
            provider.id,
            booking_date,
            start_time,
            end_time
        ):

            flash(
                "The provider is not available at this time.",
                "error"
            )

            return redirect(
                url_for(
                    "bookings.new_booking",
                    service_id=service.id
                )
            )

        if booking_conflicts(
            provider.id,
            booking_date,
            start_time,
            end_time
        ):

            flash(
                "This time is already reserved. Choose another time.",
                "error"
            )

            return redirect(
                url_for(
                    "bookings.new_booking",
                    service_id=service.id
                )
            )

        # Home and hybrid services require an address.
        address = None

        if service.service_mode in ("HOME", "HYBRID"):

            try:
                address_id = int(
                    request.form.get("address_id", "")
                )
            except (ValueError, TypeError):
                abort(400)

            address = db.session.execute(
                db.select(Address).where(
                    Address.id == address_id,
                    Address.user_id == current_user.id
                )
            ).scalar_one_or_none()

            if address is None:
                abort(400)

        notes = request.form.get(
            "customer_notes",
            ""
        ).strip()[:1000]

        booking = Booking(
            customer_id=current_user.id,
            provider_id=provider.id,
            service_id=service.id,
            address_id=address.id if address else None,
            booking_date=booking_date,
            start_time=start_time,
            end_time=end_time,
            total_price=price,
            status="PENDING",
            customer_notes=notes or None
        )

        db.session.add(booking)
        db.session.commit()

        flash(
            "Booking request submitted successfully.",
            "success"
        )

        return redirect(
            url_for("bookings.history")
        )

    return render_template(
        "bookings/new.html",
        service=service,
        provider_services=provider_services,
        addresses=addresses,
        today=date.today().isoformat()
    )


# =================================================
# CUSTOMER BOOKING HISTORY
# =================================================

@bookings_bp.route("/history")
@login_required
def history():

    if current_user.role != "CUSTOMER":
        abort(403)

    bookings = db.session.execute(
        db.select(Booking)
        .where(
            Booking.customer_id == current_user.id
        )
        .order_by(
            Booking.booking_date.desc(),
            Booking.start_time.desc()
        )
    ).scalars().all()

    return render_template(
        "bookings/history.html",
        bookings=bookings
    )


# =================================================
# CUSTOMER BOOKING CANCELLATION
# =================================================

@bookings_bp.route(
    "/<int:booking_id>/cancel",
    methods=["POST"]
)
@login_required
def cancel_booking(booking_id):

    if current_user.role != "CUSTOMER":
        abort(403)

    booking = db.session.get(Booking, booking_id)

    if booking is None:
        abort(404)

    if booking.customer_id != current_user.id:
        abort(403)

    if booking.status not in {"PENDING", "CONFIRMED"}:
        flash(
            "This booking can no longer be cancelled.",
            "error"
        )
        return redirect(url_for("bookings.history"))

    booking_start = datetime.combine(
        booking.booking_date,
        booking.start_time,
        tzinfo=BOOKING_TIMEZONE
    )

    if booking_start <= datetime.now(BOOKING_TIMEZONE):
        flash(
            "A past booking cannot be cancelled.",
            "error"
        )
        return redirect(url_for("bookings.history"))

    booking.status = "CANCELLED"
    db.session.commit()

    flash(
        "Booking cancelled successfully.",
        "success"
    )

    return redirect(url_for("bookings.history"))


# =================================================
# PROVIDER BOOKING MANAGEMENT
# =================================================

@bookings_bp.route("/provider")
@login_required
def provider_bookings():

    if current_user.role != "PROVIDER":
        abort(403)

    profile = current_user.provider_profile

    if profile is None:
        abort(403)

    bookings = db.session.execute(
        db.select(Booking)
        .where(Booking.provider_id == profile.id)
        .order_by(
            Booking.booking_date.desc(),
            Booking.start_time.desc()
        )
    ).scalars().all()

    return render_template(
        "bookings/provider.html",
        bookings=bookings
    )


@bookings_bp.route(
    "/provider/<int:booking_id>/status",
    methods=["POST"]
)
@login_required
def update_provider_booking_status(booking_id):

    if current_user.role != "PROVIDER":
        abort(403)

    profile = current_user.provider_profile

    if profile is None:
        abort(403)

    booking = db.session.get(Booking, booking_id)

    if booking is None:
        abort(404)

    if booking.provider_id != profile.id:
        abort(403)

    action = request.form.get(
        "action",
        ""
    ).strip().upper()

    transitions = {
        "PENDING": {
            "CONFIRM": "CONFIRMED",
            "REJECT": "REJECTED"
        },
        "CONFIRMED": {
            "COMPLETE": "COMPLETED",
            "CANCEL": "CANCELLED"
        }
    }

    new_status = transitions.get(
        booking.status,
        {}
    ).get(action)

    if new_status is None:
        flash(
            "That booking status change is not allowed.",
            "error"
        )
        return redirect(
            url_for("bookings.provider_bookings")
        )

    booking.status = new_status
    db.session.commit()

    flash(
        f"Booking marked as {new_status.lower()}.",
        "success"
    )

    return redirect(
        url_for("bookings.provider_bookings")
    )
