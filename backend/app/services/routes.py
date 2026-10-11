from flask import (
    render_template,
    abort
)

from app.extensions import db

from app.models.service_category import (
    ServiceCategory
)

from app.models.service import Service

from app.services import services_bp


# -------------------------------------------------
# All service categories
# -------------------------------------------------
@services_bp.route("/")
def service_catalog():
    """
    Public service catalog.
    """

    categories = db.session.execute(
        db.select(ServiceCategory)
        .where(
            ServiceCategory.is_active.is_(True)
        )
        .order_by(
            ServiceCategory.display_order,
            ServiceCategory.name
        )
    ).scalars().all()


    return render_template(
        "services/catalog.html",
        categories=categories
    )


# -------------------------------------------------
# Category page
# -------------------------------------------------
@services_bp.route("/category/<string:slug>")
def category_detail(slug):
    """
    Display services belonging to one category.
    """

    category = db.session.execute(
        db.select(ServiceCategory)
        .where(
            ServiceCategory.slug == slug,
            ServiceCategory.is_active.is_(True)
        )
    ).scalar_one_or_none()


    if category is None:
        abort(404)


    services = db.session.execute(
        db.select(Service)
        .where(
            Service.category_id == category.id,
            Service.is_active.is_(True)
        )
        .order_by(
            Service.display_order,
            Service.name
        )
    ).scalars().all()


    return render_template(
        "services/category.html",
        category=category,
        services=services
    )


# -------------------------------------------------
# Individual service page
# -------------------------------------------------
@services_bp.route("/<string:slug>")
def service_detail(slug):
    """
    Display one service.
    """

    service = db.session.execute(
        db.select(Service)
        .where(
            Service.slug == slug,
            Service.is_active.is_(True)
        )
    ).scalar_one_or_none()


    if service is None:
        abort(404)


    return render_template(
        "services/detail.html",
        service=service
    )