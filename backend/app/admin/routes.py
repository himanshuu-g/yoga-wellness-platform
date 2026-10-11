from app.models.user import User
from app.models.provider_profile import ProviderProfile

from flask import (
    render_template,
    request,
    redirect,
    url_for,
    flash,
    abort
)

from flask_login import login_required

from app.extensions import db
from app.models.service_category import ServiceCategory
from app.models.service import Service
from app.admin import admin_bp
from app.utils.decorators import admin_required


# =================================================
# ADMIN DASHBOARD
# =================================================

@admin_bp.route("/")
@login_required
@admin_required
def dashboard():
    """
    Main admin dashboard.
    """

    category_count = db.session.scalar(
        db.select(
            db.func.count(ServiceCategory.id)
        )
    )

    service_count = db.session.scalar(
        db.select(
            db.func.count(Service.id)
        )
    )

    return render_template(
        "admin/dashboard.html",
        category_count=category_count,
        service_count=service_count
    )


# =================================================
# CATEGORY MANAGEMENT
# =================================================

@admin_bp.route("/categories")
@login_required
@admin_required
def categories():
    """
    Display all service categories.
    """

    category_list = db.session.execute(
        db.select(ServiceCategory)
        .order_by(
            ServiceCategory.display_order,
            ServiceCategory.name
        )
    ).scalars().all()

    return render_template(
        "admin/categories.html",
        categories=category_list
    )


# -------------------------------------------------
# Add category
# -------------------------------------------------

@admin_bp.route(
    "/categories/add",
    methods=["GET", "POST"]
)
@login_required
@admin_required
def add_category():

    if request.method == "POST":

        name = request.form.get(
            "name",
            ""
        ).strip()

        slug = request.form.get(
            "slug",
            ""
        ).strip().lower()

        description = request.form.get(
            "description",
            ""
        ).strip()

        display_order_raw = request.form.get(
            "display_order",
            "0"
        ).strip()

        # -----------------------------------------
        # Validation
        # -----------------------------------------

        if not name or not slug:

            flash(
                "Category name and slug are required.",
                "error"
            )

            return redirect(
                url_for("admin.add_category")
            )

        try:
            display_order = int(
                display_order_raw
            )

        except ValueError:

            flash(
                "Display order must be a number.",
                "error"
            )

            return redirect(
                url_for("admin.add_category")
            )

        if display_order < 0:

            flash(
                "Display order cannot be negative.",
                "error"
            )

            return redirect(
                url_for("admin.add_category")
            )

        # -----------------------------------------
        # Duplicate name / slug
        # -----------------------------------------

        duplicate = db.session.execute(
            db.select(ServiceCategory).where(
                db.or_(
                    ServiceCategory.name == name,
                    ServiceCategory.slug == slug
                )
            )
        ).scalar_one_or_none()

        if duplicate:

            flash(
                "A category with this name or slug already exists.",
                "error"
            )

            return redirect(
                url_for("admin.add_category")
            )

        # -----------------------------------------
        # Create category
        # -----------------------------------------

        category = ServiceCategory(
            name=name,
            slug=slug,
            description=(
                description
                if description
                else None
            ),
            display_order=display_order,
            is_active=True
        )

        db.session.add(category)
        db.session.commit()

        flash(
            "Category created successfully.",
            "success"
        )

        return redirect(
            url_for("admin.categories")
        )

    return render_template(
        "admin/add_category.html"
    )


# -------------------------------------------------
# Edit category
# -------------------------------------------------

@admin_bp.route(
    "/categories/<int:category_id>/edit",
    methods=["GET", "POST"]
)
@login_required
@admin_required
def edit_category(category_id):

    category = db.session.get(
        ServiceCategory,
        category_id
    )

    if category is None:
        abort(404)

    if request.method == "POST":

        name = request.form.get(
            "name",
            ""
        ).strip()

        slug = request.form.get(
            "slug",
            ""
        ).strip().lower()

        description = request.form.get(
            "description",
            ""
        ).strip()

        display_order_raw = request.form.get(
            "display_order",
            "0"
        ).strip()

        if not name or not slug:

            flash(
                "Category name and slug are required.",
                "error"
            )

            return redirect(
                url_for(
                    "admin.edit_category",
                    category_id=category.id
                )
            )

        try:
            display_order = int(
                display_order_raw
            )

        except ValueError:

            flash(
                "Display order must be a number.",
                "error"
            )

            return redirect(
                url_for(
                    "admin.edit_category",
                    category_id=category.id
                )
            )

        if display_order < 0:

            flash(
                "Display order cannot be negative.",
                "error"
            )

            return redirect(
                url_for(
                    "admin.edit_category",
                    category_id=category.id
                )
            )

        duplicate = db.session.execute(
            db.select(ServiceCategory).where(
                ServiceCategory.id != category.id,
                db.or_(
                    ServiceCategory.name == name,
                    ServiceCategory.slug == slug
                )
            )
        ).scalar_one_or_none()

        if duplicate:

            flash(
                "Another category already uses this name or slug.",
                "error"
            )

            return redirect(
                url_for(
                    "admin.edit_category",
                    category_id=category.id
                )
            )

        category.name = name
        category.slug = slug

        category.description = (
            description
            if description
            else None
        )

        category.display_order = display_order

        db.session.commit()

        flash(
            "Category updated successfully.",
            "success"
        )

        return redirect(
            url_for("admin.categories")
        )

    return render_template(
        "admin/edit_category.html",
        category=category
    )


# -------------------------------------------------
# Activate / deactivate category
# -------------------------------------------------

@admin_bp.route(
    "/categories/<int:category_id>/toggle",
    methods=["POST"]
)
@login_required
@admin_required
def toggle_category(category_id):

    category = db.session.get(
        ServiceCategory,
        category_id
    )

    if category is None:
        abort(404)

    category.is_active = (
        not category.is_active
    )

    db.session.commit()

    if category.is_active:
        message = "Category activated."
    else:
        message = "Category deactivated."

    flash(
        message,
        "success"
    )

    return redirect(
        url_for("admin.categories")
    )

# =================================================
# PROVIDER MANAGEMENT
# =================================================

@admin_bp.route("/providers")
@login_required
@admin_required
def providers():
    """
    Display all provider accounts.
    """

    provider_list = db.session.execute(
        db.select(User)
        .where(
            User.role == "PROVIDER"
        )
        .order_by(User.name)
    ).scalars().all()

    return render_template(
        "admin/providers.html",
        providers=provider_list
    )

# =================================================
# SERVICE MANAGEMENT
# =================================================

@admin_bp.route("/services")
@login_required
@admin_required
def services():
    """
    Display all services.
    """

    service_list = db.session.execute(
        db.select(Service)
        .order_by(
            Service.category_id,
            Service.display_order,
            Service.name
        )
    ).scalars().all()

    return render_template(
        "admin/services.html",
        services=service_list
    )


# -------------------------------------------------
# Add service
# -------------------------------------------------

@admin_bp.route(
    "/services/add",
    methods=["GET", "POST"]
)
@login_required
@admin_required
def add_service():

    categories = db.session.execute(
        db.select(ServiceCategory)
        .where(
            ServiceCategory.is_active.is_(True)
        )
        .order_by(
            ServiceCategory.name
        )
    ).scalars().all()

    if request.method == "POST":

        category_id_raw = request.form.get(
            "category_id",
            ""
        ).strip()

        name = request.form.get(
            "name",
            ""
        ).strip()

        slug = request.form.get(
            "slug",
            ""
        ).strip().lower()

        short_description = request.form.get(
            "short_description",
            ""
        ).strip()

        description = request.form.get(
            "description",
            ""
        ).strip()

        duration_raw = request.form.get(
            "duration_minutes",
            ""
        ).strip()

        price_raw = request.form.get(
            "base_price",
            ""
        ).strip()

        service_mode = request.form.get(
            "service_mode",
            "HOME"
        ).strip().upper()

        display_order_raw = request.form.get(
            "display_order",
            "0"
        ).strip()

        # -----------------------------------------
        # Required values
        # -----------------------------------------

        if not category_id_raw or not name or not slug:

            flash(
                "Category, service name and slug are required.",
                "error"
            )

            return redirect(
                url_for("admin.add_service")
            )

        # -----------------------------------------
        # Category
        # -----------------------------------------

        try:
            category_id = int(
                category_id_raw
            )

        except ValueError:

            flash(
                "Invalid category.",
                "error"
            )

            return redirect(
                url_for("admin.add_service")
            )

        category = db.session.get(
            ServiceCategory,
            category_id
        )

        if category is None:

            flash(
                "Selected category does not exist.",
                "error"
            )

            return redirect(
                url_for("admin.add_service")
            )

        if not category.is_active:

            flash(
                "Please select an active category.",
                "error"
            )

            return redirect(
                url_for("admin.add_service")
            )

        # -----------------------------------------
        # Duration
        # -----------------------------------------

        duration = None

        if duration_raw:

            try:
                duration = int(
                    duration_raw
                )

            except ValueError:

                flash(
                    "Duration must be a number.",
                    "error"
                )

                return redirect(
                    url_for("admin.add_service")
                )

            if duration <= 0:

                flash(
                    "Duration must be greater than zero.",
                    "error"
                )

                return redirect(
                    url_for("admin.add_service")
                )

        # -----------------------------------------
        # Price
        # -----------------------------------------

        base_price = None

        if price_raw:

            try:
                base_price = float(
                    price_raw
                )

            except ValueError:

                flash(
                    "Price must be a valid number.",
                    "error"
                )

                return redirect(
                    url_for("admin.add_service")
                )

            if base_price < 0:

                flash(
                    "Price cannot be negative.",
                    "error"
                )

                return redirect(
                    url_for("admin.add_service")
                )

        # -----------------------------------------
        # Display order
        # -----------------------------------------

        try:
            display_order = int(
                display_order_raw
            )

        except ValueError:

            flash(
                "Display order must be a number.",
                "error"
            )

            return redirect(
                url_for("admin.add_service")
            )

        if display_order < 0:

            flash(
                "Display order cannot be negative.",
                "error"
            )

            return redirect(
                url_for("admin.add_service")
            )

        # -----------------------------------------
        # Service mode
        # -----------------------------------------

        allowed_modes = {
            "HOME",
            "ONLINE",
            "CENTER",
            "HYBRID"
        }

        if service_mode not in allowed_modes:

            flash(
                "Invalid service mode.",
                "error"
            )

            return redirect(
                url_for("admin.add_service")
            )

        # -----------------------------------------
        # Duplicate slug
        # -----------------------------------------

        duplicate = db.session.execute(
            db.select(Service).where(
                Service.slug == slug
            )
        ).scalar_one_or_none()

        if duplicate:

            flash(
                "A service with this slug already exists.",
                "error"
            )

            return redirect(
                url_for("admin.add_service")
            )

        # -----------------------------------------
        # Create service
        # -----------------------------------------

        service = Service(
            category_id=category.id,
            name=name,
            slug=slug,
            short_description=(
                short_description
                if short_description
                else None
            ),
            description=(
                description
                if description
                else None
            ),
            duration_minutes=duration,
            base_price=base_price,
            service_mode=service_mode,
            display_order=display_order,
            is_active=True
        )

        db.session.add(service)
        db.session.commit()

        flash(
            "Service created successfully.",
            "success"
        )

        return redirect(
            url_for("admin.services")
        )

    return render_template(
        "admin/add_service.html",
        categories=categories
    )


# -------------------------------------------------
# Edit service
# -------------------------------------------------

@admin_bp.route(
    "/services/<int:service_id>/edit",
    methods=["GET", "POST"]
)
@login_required
@admin_required
def edit_service(service_id):

    service = db.session.get(
        Service,
        service_id
    )

    if service is None:
        abort(404)

    categories = db.session.execute(
        db.select(ServiceCategory)
        .order_by(
            ServiceCategory.name
        )
    ).scalars().all()

    if request.method == "POST":

        category_id_raw = request.form.get(
            "category_id",
            ""
        ).strip()

        name = request.form.get(
            "name",
            ""
        ).strip()

        slug = request.form.get(
            "slug",
            ""
        ).strip().lower()

        short_description = request.form.get(
            "short_description",
            ""
        ).strip()

        description = request.form.get(
            "description",
            ""
        ).strip()

        duration_raw = request.form.get(
            "duration_minutes",
            ""
        ).strip()

        price_raw = request.form.get(
            "base_price",
            ""
        ).strip()

        service_mode = request.form.get(
            "service_mode",
            "HOME"
        ).strip().upper()

        display_order_raw = request.form.get(
            "display_order",
            "0"
        ).strip()

        # -----------------------------------------
        # Required values
        # -----------------------------------------

        if not category_id_raw or not name or not slug:

            flash(
                "Category, service name and slug are required.",
                "error"
            )

            return redirect(
                url_for(
                    "admin.edit_service",
                    service_id=service.id
                )
            )

        # -----------------------------------------
        # Category
        # -----------------------------------------

        try:
            category_id = int(
                category_id_raw
            )

        except ValueError:

            flash(
                "Invalid category.",
                "error"
            )

            return redirect(
                url_for(
                    "admin.edit_service",
                    service_id=service.id
                )
            )

        category = db.session.get(
            ServiceCategory,
            category_id
        )

        if category is None:

            flash(
                "Selected category does not exist.",
                "error"
            )

            return redirect(
                url_for(
                    "admin.edit_service",
                    service_id=service.id
                )
            )

        # -----------------------------------------
        # Duration
        # -----------------------------------------

        duration = None

        if duration_raw:

            try:
                duration = int(
                    duration_raw
                )

            except ValueError:

                flash(
                    "Duration must be a number.",
                    "error"
                )

                return redirect(
                    url_for(
                        "admin.edit_service",
                        service_id=service.id
                    )
                )

            if duration <= 0:

                flash(
                    "Duration must be greater than zero.",
                    "error"
                )

                return redirect(
                    url_for(
                        "admin.edit_service",
                        service_id=service.id
                    )
                )

        # -----------------------------------------
        # Price
        # -----------------------------------------

        base_price = None

        if price_raw:

            try:
                base_price = float(
                    price_raw
                )

            except ValueError:

                flash(
                    "Price must be a valid number.",
                    "error"
                )

                return redirect(
                    url_for(
                        "admin.edit_service",
                        service_id=service.id
                    )
                )

            if base_price < 0:

                flash(
                    "Price cannot be negative.",
                    "error"
                )

                return redirect(
                    url_for(
                        "admin.edit_service",
                        service_id=service.id
                    )
                )

        # -----------------------------------------
        # Display order
        # -----------------------------------------

        try:
            display_order = int(
                display_order_raw
            )

        except ValueError:

            flash(
                "Display order must be a number.",
                "error"
            )

            return redirect(
                url_for(
                    "admin.edit_service",
                    service_id=service.id
                )
            )

        if display_order < 0:

            flash(
                "Display order cannot be negative.",
                "error"
            )

            return redirect(
                url_for(
                    "admin.edit_service",
                    service_id=service.id
                )
            )

        # -----------------------------------------
        # Service mode
        # -----------------------------------------

        allowed_modes = {
            "HOME",
            "ONLINE",
            "CENTER",
            "HYBRID"
        }

        if service_mode not in allowed_modes:

            flash(
                "Invalid service mode.",
                "error"
            )

            return redirect(
                url_for(
                    "admin.edit_service",
                    service_id=service.id
                )
            )

        # -----------------------------------------
        # Duplicate slug
        # -----------------------------------------

        duplicate = db.session.execute(
            db.select(Service).where(
                Service.id != service.id,
                Service.slug == slug
            )
        ).scalar_one_or_none()

        if duplicate:

            flash(
                "Another service already uses this slug.",
                "error"
            )

            return redirect(
                url_for(
                    "admin.edit_service",
                    service_id=service.id
                )
            )

        # -----------------------------------------
        # Update service
        # -----------------------------------------

        service.category_id = category.id
        service.name = name
        service.slug = slug

        service.short_description = (
            short_description
            if short_description
            else None
        )

        service.description = (
            description
            if description
            else None
        )

        service.duration_minutes = duration
        service.base_price = base_price
        service.service_mode = service_mode
        service.display_order = display_order

        db.session.commit()

        flash(
            "Service updated successfully.",
            "success"
        )

        return redirect(
            url_for("admin.services")
        )

    return render_template(
        "admin/edit_service.html",
        service=service,
        categories=categories
    )


# -------------------------------------------------
# Activate / deactivate service
# -------------------------------------------------

@admin_bp.route(
    "/services/<int:service_id>/toggle",
    methods=["POST"]
)
@login_required
@admin_required
def toggle_service(service_id):

    service = db.session.get(
        Service,
        service_id
    )

    if service is None:
        abort(404)

    service.is_active = (
        not service.is_active
    )

    db.session.commit()

    if service.is_active:
        message = "Service activated."
    else:
        message = "Service deactivated."

    flash(
        message,
        "success"
    )

    return redirect(
        url_for("admin.services")
    )


@admin_bp.route(
    "/users/<int:user_id>/make-provider",
    methods=["POST"]
)
@login_required
@admin_required
def make_provider(user_id):
    """
    Promote an existing customer account
    to PROVIDER and create its provider profile.
    """

    user = db.session.get(
        User,
        user_id
    )

    if user is None:
        abort(404)

    if user.role == "ADMIN":

        flash(
            "An admin account cannot be converted to a provider.",
            "error"
        )

        return redirect(
            url_for("admin.providers")
        )

    if user.role == "PROVIDER":

        flash(
            "This user is already a provider.",
            "error"
        )

        return redirect(
            url_for("admin.providers")
        )

    user.role = "PROVIDER"

    if user.provider_profile is None:

        provider_profile = ProviderProfile(
            user=user,
            verification_status="PENDING",
            is_available=False
        )

        db.session.add(
            provider_profile
        )

    db.session.commit()

    flash(
        f"{user.name} is now a provider.",
        "success"
    )

    return redirect(
        url_for("admin.providers")
    )

@admin_bp.route("/provider-candidates")
@login_required
@admin_required
def provider_candidates():

    customers = db.session.execute(
        db.select(User)
        .where(
            User.role == "CUSTOMER"
        )
        .order_by(User.name)
    ).scalars().all()

    return render_template(
        "admin/provider_candidates.html",
        customers=customers
    )

@admin_bp.route(
    "/providers/<int:provider_id>/verification",
    methods=["POST"]
)
@login_required
@admin_required
def provider_verification(provider_id):

    provider = db.session.get(
        ProviderProfile,
        provider_id
    )

    if provider is None:
        abort(404)

    action = request.form.get(
        "action",
        ""
    ).strip().upper()

    if action not in {
        "APPROVE",
        "REJECT"
    }:

        abort(400)

    if action == "APPROVE":

        provider.verification_status = "APPROVED"

        flash(
            "Provider approved successfully.",
            "success"
        )

    else:

        provider.verification_status = "REJECTED"

        # Rejected providers cannot remain available.
        provider.is_available = False

        flash(
            "Provider rejected.",
            "success"
        )

    db.session.commit()

    return redirect(
        url_for("admin.providers")
    )