from decimal import Decimal, InvalidOperation
from datetime import datetime

from flask import abort
from app.models.provider_availability import ProviderAvailability

from flask import (
    render_template,
    request,
    redirect,
    url_for,
    flash,
    abort
)

from flask_login import (
    login_required,
    current_user
)

from app.extensions import db
from app.models.provider_profile import ProviderProfile
from app.models.provider_service import ProviderService
from app.models.service import Service
from app.provider import provider_bp
from app.utils.decorators import provider_required


# =================================================
# PROVIDER DASHBOARD
# =================================================

@provider_bp.route("/")
@login_required
@provider_required
def dashboard():
    """
    Main dashboard for service providers.
    """

    profile = current_user.provider_profile

    return render_template(
        "provider/dashboard.html",
        profile=profile
    )


# =================================================
# EDIT PROVIDER PROFILE
# =================================================

@provider_bp.route(
    "/profile",
    methods=["GET", "POST"]
)
@login_required
@provider_required
def profile():
    """
    Provider can create/update professional profile.
    """

    provider_profile = current_user.provider_profile

    # Safety fallback:
    # If provider role exists but profile doesn't,
    # create the corresponding profile.
    if provider_profile is None:

        provider_profile = ProviderProfile(
            user_id=current_user.id,
            verification_status="PENDING",
            is_available=False
        )

        db.session.add(provider_profile)
        db.session.commit()

    if request.method == "POST":

        bio = request.form.get(
            "bio",
            ""
        ).strip()

        qualification = request.form.get(
            "qualification",
            ""
        ).strip()

        specialization = request.form.get(
            "specialization",
            ""
        ).strip()

        service_city = request.form.get(
            "service_city",
            ""
        ).strip()

        experience_raw = request.form.get(
            "experience_years",
            ""
        ).strip()

        # -----------------------------------------
        # Required fields
        # -----------------------------------------

        if (
            not qualification
            or not specialization
            or not service_city
        ):

            flash(
                "Qualification, specialization and service city are required.",
                "error"
            )

            return redirect(
                url_for("provider.profile")
            )

        # -----------------------------------------
        # Experience validation
        # -----------------------------------------

        experience_years = None

        if experience_raw:

            try:
                experience_years = int(
                    experience_raw
                )

            except ValueError:

                flash(
                    "Experience must be a valid number.",
                    "error"
                )

                return redirect(
                    url_for("provider.profile")
                )

            if (
                experience_years < 0
                or experience_years > 80
            ):

                flash(
                    "Please enter valid years of experience.",
                    "error"
                )

                return redirect(
                    url_for("provider.profile")
                )

        provider_profile.bio = (
            bio or None
        )

        provider_profile.qualification = (
            qualification
        )

        provider_profile.specialization = (
            specialization
        )

        provider_profile.service_city = (
            service_city
        )

        provider_profile.experience_years = (
            experience_years
        )

        db.session.commit()

        flash(
            "Provider profile updated successfully.",
            "success"
        )

        return redirect(
            url_for("provider.dashboard")
        )

    return render_template(
        "provider/profile.html",
        profile=provider_profile
    )

# =================================================
# PROVIDER SERVICE MANAGEMENT
# =================================================

@provider_bp.route("/services")
@login_required
@provider_required
def services():
    """
    Display services offered by the current provider.
    """

    profile = current_user.provider_profile

    if profile is None:
        flash(
            "Please complete your provider profile first.",
            "error"
        )

        return redirect(
            url_for("provider.profile")
        )

    provider_services = db.session.execute(
        db.select(ProviderService)
        .where(
            ProviderService.provider_id == profile.id
        )
        .order_by(ProviderService.id)
    ).scalars().all()

    return render_template(
        "provider/services.html",
        provider_services=provider_services,
        profile=profile
    )


# =================================================
# ADD PROVIDER SERVICE
# =================================================

@provider_bp.route(
    "/services/add",
    methods=["GET", "POST"]
)
@login_required
@provider_required
def add_service():
    """
    Allow an approved provider to select a service
    and configure provider-specific price/duration.
    """

    profile = current_user.provider_profile

    if profile is None:

        flash(
            "Please complete your provider profile first.",
            "error"
        )

        return redirect(
            url_for("provider.profile")
        )

    # Only approved providers can configure services.
    if profile.verification_status != "APPROVED":

        flash(
            "Your provider account must be approved before adding services.",
            "error"
        )

        return redirect(
            url_for("provider.dashboard")
        )

    # Only active services from the admin catalog.
    available_services = db.session.execute(
        db.select(Service)
        .where(
            Service.is_active.is_(True)
        )
        .order_by(
            Service.name
        )
    ).scalars().all()

    if request.method == "POST":

        service_id_raw = request.form.get(
            "service_id",
            ""
        ).strip()

        price_raw = request.form.get(
            "price",
            ""
        ).strip()

        duration_raw = request.form.get(
            "duration_minutes",
            ""
        ).strip()

        # -----------------------------------------
        # Required values
        # -----------------------------------------

        if not service_id_raw:

            flash(
                "Please select a service.",
                "error"
            )

            return redirect(
                url_for("provider.add_service")
            )

        # -----------------------------------------
        # Service ID
        # -----------------------------------------

        try:
            service_id = int(service_id_raw)

        except ValueError:

            flash(
                "Invalid service selected.",
                "error"
            )

            return redirect(
                url_for("provider.add_service")
            )

        service = db.session.get(
            Service,
            service_id
        )

        if service is None or not service.is_active:

            flash(
                "Selected service is not available.",
                "error"
            )

            return redirect(
                url_for("provider.add_service")
            )

        # -----------------------------------------
        # Prevent duplicate provider/service
        # -----------------------------------------

        existing = db.session.execute(
            db.select(ProviderService).where(
                ProviderService.provider_id == profile.id,
                ProviderService.service_id == service.id
            )
        ).scalar_one_or_none()

        if existing:

            flash(
                "You already offer this service.",
                "error"
            )

            return redirect(
                url_for("provider.services")
            )

        # -----------------------------------------
        # Price
        # -----------------------------------------

        price = None

        if price_raw:

            try:
                price = Decimal(price_raw)

            except InvalidOperation:

                flash(
                    "Please enter a valid price.",
                    "error"
                )

                return redirect(
                    url_for("provider.add_service")
                )

            if price < 0:

                flash(
                    "Price cannot be negative.",
                    "error"
                )

                return redirect(
                    url_for("provider.add_service")
                )

            if price.as_tuple().exponent < -2:

                flash(
                    "Price can have a maximum of 2 decimal places.",
                    "error"
                )

                return redirect(
                    url_for("provider.add_service")
                )

        # -----------------------------------------
        # Duration
        # -----------------------------------------

        duration = None

        if duration_raw:

            try:
                duration = int(duration_raw)

            except ValueError:

                flash(
                    "Duration must be a number.",
                    "error"
                )

                return redirect(
                    url_for("provider.add_service")
                )

            if duration <= 0:

                flash(
                    "Duration must be greater than zero.",
                    "error"
                )

                return redirect(
                    url_for("provider.add_service")
                )

        # -----------------------------------------
        # Create provider service
        # -----------------------------------------

        provider_service = ProviderService(
            provider_id=profile.id,
            service_id=service.id,
            price=price,
            duration_minutes=duration,
            is_active=True
        )

        db.session.add(provider_service)
        db.session.commit()

        flash(
            f"{service.name} added successfully.",
            "success"
        )

        return redirect(
            url_for("provider.services")
        )

    return render_template(
        "provider/add_service.html",
        services=available_services
    )


# =================================================
# EDIT PROVIDER SERVICE
# =================================================

@provider_bp.route(
    "/services/<int:provider_service_id>/edit",
    methods=["GET", "POST"]
)
@login_required
@provider_required
def edit_service(provider_service_id):
    """
    Edit provider-specific price and duration.
    """

    profile = current_user.provider_profile

    if profile is None:
        abort(403)

    provider_service = db.session.get(
        ProviderService,
        provider_service_id
    )

    if provider_service is None:
        abort(404)

    # SECURITY:
    # Provider can only edit their own service.
    if provider_service.provider_id != profile.id:
        abort(403)

    if profile.verification_status != "APPROVED":

        flash(
            "Your provider account must be approved.",
            "error"
        )

        return redirect(
            url_for("provider.dashboard")
        )

    if request.method == "POST":

        price_raw = request.form.get(
            "price",
            ""
        ).strip()

        duration_raw = request.form.get(
            "duration_minutes",
            ""
        ).strip()

        price = None

        if price_raw:

            try:
                price = Decimal(price_raw)

            except InvalidOperation:

                flash(
                    "Please enter a valid price.",
                    "error"
                )

                return redirect(
                    url_for(
                        "provider.edit_service",
                        provider_service_id=provider_service.id
                    )
                )

            if price < 0:

                flash(
                    "Price cannot be negative.",
                    "error"
                )

                return redirect(
                    url_for(
                        "provider.edit_service",
                        provider_service_id=provider_service.id
                    )
                )

            if price.as_tuple().exponent < -2:

                flash(
                    "Price can have a maximum of 2 decimal places.",
                    "error"
                )

                return redirect(
                    url_for(
                        "provider.edit_service",
                        provider_service_id=provider_service.id
                    )
                )

        duration = None

        if duration_raw:

            try:
                duration = int(duration_raw)

            except ValueError:

                flash(
                    "Duration must be a number.",
                    "error"
                )

                return redirect(
                    url_for(
                        "provider.edit_service",
                        provider_service_id=provider_service.id
                    )
                )

            if duration <= 0:

                flash(
                    "Duration must be greater than zero.",
                    "error"
                )

                return redirect(
                    url_for(
                        "provider.edit_service",
                        provider_service_id=provider_service.id
                    )
                )

        provider_service.price = price
        provider_service.duration_minutes = duration

        db.session.commit()

        flash(
            "Service settings updated successfully.",
            "success"
        )

        return redirect(
            url_for("provider.services")
        )

    return render_template(
        "provider/edit_service.html",
        provider_service=provider_service
    )


# =================================================
# ACTIVATE / DEACTIVATE PROVIDER SERVICE
# =================================================

@provider_bp.route(
    "/services/<int:provider_service_id>/toggle",
    methods=["POST"]
)
@login_required
@provider_required
def toggle_service(provider_service_id):
    """
    Activate or deactivate one of the
    current provider's services.
    """

    profile = current_user.provider_profile

    if profile is None:
        abort(403)

    if profile.verification_status != "APPROVED":

        flash(
            "Your provider account must be approved.",
            "error"
        )

        return redirect(
            url_for("provider.dashboard")
        )

    provider_service = db.session.get(
        ProviderService,
        provider_service_id
    )

    if provider_service is None:
        abort(404)

    # Never trust an ID from the browser.
    if provider_service.provider_id != profile.id:
        abort(403)

    provider_service.is_active = (
        not provider_service.is_active
    )

    db.session.commit()

    if provider_service.is_active:
        message = "Service activated."
    else:
        message = "Service deactivated."

    flash(
        message,
        "success"
    )

    return redirect(
        url_for("provider.services")
    )

# =================================================
# PROVIDER WEEKLY AVAILABILITY
# =================================================

DAYS_OF_WEEK = [
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
    "Sunday"
]


def get_approved_provider():
    """
    Return the logged-in provider's approved profile.
    """

    profile = current_user.provider_profile

    if profile is None:
        abort(403)

    if profile.verification_status != "APPROVED":
        abort(403)

    return profile


def parse_availability_form():
    """
    Validate availability submitted from the form.
    """

    try:
        day = int(request.form.get("day_of_week", ""))

        start_time = datetime.strptime(
            request.form.get("start_time", ""),
            "%H:%M"
        ).time()

        end_time = datetime.strptime(
            request.form.get("end_time", ""),
            "%H:%M"
        ).time()

    except (ValueError, TypeError):
        return None, "Please enter valid day and time values."

    if day not in range(7):
        return None, "Invalid day selected."

    if start_time >= end_time:
        return None, "End time must be later than start time."

    return {
        "day_of_week": day,
        "start_time": start_time,
        "end_time": end_time
    }, None


def has_overlapping_slot(
    provider_id,
    day,
    start_time,
    end_time,
    exclude_id=None
):
    """
    Prevent overlapping ACTIVE weekly availability slots.
    """

    query = db.select(ProviderAvailability).where(
        ProviderAvailability.provider_id == provider_id,
        ProviderAvailability.day_of_week == day,
        ProviderAvailability.is_active.is_(True),
        ProviderAvailability.start_time < end_time,
        ProviderAvailability.end_time > start_time
    )

    if exclude_id is not None:
        query = query.where(
            ProviderAvailability.id != exclude_id
        )

    existing = db.session.execute(
        query
    ).scalar_one_or_none()

    return existing is not None


# =================================================
# VIEW AVAILABILITY
# =================================================

@provider_bp.route("/availability")
@login_required
@provider_required
def availability():

    profile = get_approved_provider()

    slots = db.session.execute(
        db.select(ProviderAvailability)
        .where(
            ProviderAvailability.provider_id == profile.id
        )
        .order_by(
            ProviderAvailability.day_of_week,
            ProviderAvailability.start_time
        )
    ).scalars().all()

    return render_template(
        "provider/availability.html",
        slots=slots,
        days=DAYS_OF_WEEK
    )


# =================================================
# ADD AVAILABILITY
# =================================================

@provider_bp.route(
    "/availability/add",
    methods=["GET", "POST"]
)
@login_required
@provider_required
def add_availability():

    profile = get_approved_provider()

    if request.method == "POST":

        data, error = parse_availability_form()

        if error:
            flash(error, "error")
            return redirect(
                url_for("provider.add_availability")
            )

        if has_overlapping_slot(
            profile.id,
            data["day_of_week"],
            data["start_time"],
            data["end_time"]
        ):
            flash(
                "This time overlaps with an existing active slot.",
                "error"
            )
            return redirect(
                url_for("provider.add_availability")
            )

        slot = ProviderAvailability(
            provider_id=profile.id,
            day_of_week=data["day_of_week"],
            start_time=data["start_time"],
            end_time=data["end_time"],
            is_active=True
        )

        db.session.add(slot)
        db.session.commit()

        flash(
            "Availability added successfully.",
            "success"
        )

        return redirect(
            url_for("provider.availability")
        )

    return render_template(
        "provider/add_availability.html",
        days=DAYS_OF_WEEK
    )


# =================================================
# EDIT AVAILABILITY
# =================================================

@provider_bp.route(
    "/availability/<int:slot_id>/edit",
    methods=["GET", "POST"]
)
@login_required
@provider_required
def edit_availability(slot_id):

    profile = get_approved_provider()

    slot = db.session.get(
        ProviderAvailability,
        slot_id
    )

    if slot is None:
        abort(404)

    # Provider cannot modify another provider's slot.
    if slot.provider_id != profile.id:
        abort(403)

    if request.method == "POST":

        data, error = parse_availability_form()

        if error:
            flash(error, "error")
            return redirect(
                url_for(
                    "provider.edit_availability",
                    slot_id=slot.id
                )
            )

        if slot.is_active and has_overlapping_slot(
            profile.id,
            data["day_of_week"],
            data["start_time"],
            data["end_time"],
            exclude_id=slot.id
        ):
            flash(
                "This time overlaps with another active slot.",
                "error"
            )
            return redirect(
                url_for(
                    "provider.edit_availability",
                    slot_id=slot.id
                )
            )

        slot.day_of_week = data["day_of_week"]
        slot.start_time = data["start_time"]
        slot.end_time = data["end_time"]

        db.session.commit()

        flash(
            "Availability updated successfully.",
            "success"
        )

        return redirect(
            url_for("provider.availability")
        )

    return render_template(
        "provider/edit_availability.html",
        slot=slot,
        days=DAYS_OF_WEEK
    )


# =================================================
# ACTIVATE / DEACTIVATE AVAILABILITY
# =================================================

@provider_bp.route(
    "/availability/<int:slot_id>/toggle",
    methods=["POST"]
)
@login_required
@provider_required
def toggle_availability(slot_id):

    profile = get_approved_provider()

    slot = db.session.get(
        ProviderAvailability,
        slot_id
    )

    if slot is None:
        abort(404)

    if slot.provider_id != profile.id:
        abort(403)

    if not slot.is_active:

        if has_overlapping_slot(
            profile.id,
            slot.day_of_week,
            slot.start_time,
            slot.end_time,
            exclude_id=slot.id
        ):
            flash(
                "Cannot activate: this slot overlaps with another active slot.",
                "error"
            )
            return redirect(
                url_for("provider.availability")
            )

    slot.is_active = not slot.is_active

    db.session.commit()

    flash(
        "Availability activated."
        if slot.is_active
        else "Availability deactivated.",
        "success"
    )

    return redirect(
        url_for("provider.availability")
    )