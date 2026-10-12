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
from app.models.address import Address
from app.customer import customer_bp
from app.utils.decorators import customer_required


# -------------------------------------------------
# Customer profile
# -------------------------------------------------
@customer_bp.route("/profile")
@login_required
@customer_required
def profile():
    """
    Display the logged-in customer's profile
    and saved addresses.
    """

    return render_template(
        "customer/profile.html",
        user=current_user
    )


# -------------------------------------------------
# Add address
# -------------------------------------------------
@customer_bp.route(
    "/addresses/add",
    methods=["GET", "POST"]
)
@login_required
@customer_required
def add_address():
    """
    Add a new address for the logged-in user.
    """

    if request.method == "POST":

        label = request.form.get(
            "label",
            ""
        ).strip()

        address_line_1 = request.form.get(
            "address_line_1",
            ""
        ).strip()

        address_line_2 = request.form.get(
            "address_line_2",
            ""
        ).strip()

        locality = request.form.get(
            "locality",
            ""
        ).strip()

        city = request.form.get(
            "city",
            ""
        ).strip()

        state = request.form.get(
            "state",
            ""
        ).strip()

        postal_code = request.form.get(
            "postal_code",
            ""
        ).strip()

        landmark = request.form.get(
            "landmark",
            ""
        ).strip()


        # -----------------------------------------
        # Required field validation
        # -----------------------------------------
        if not all([
            label,
            address_line_1,
            locality,
            city,
            state,
            postal_code
        ]):

            flash(
                "Please fill in all required fields.",
                "error"
            )

            return redirect(
                url_for("customer.add_address")
            )


        # -----------------------------------------
        # PIN code validation
        # -----------------------------------------
        if (
            not postal_code.isdigit()
            or len(postal_code) != 6
        ):

            flash(
                "Please enter a valid 6-digit PIN code.",
                "error"
            )

            return redirect(
                url_for("customer.add_address")
            )


        # -----------------------------------------
        # Check whether user already has addresses
        # -----------------------------------------
        existing_address = db.session.execute(
            db.select(Address).where(
                Address.user_id == current_user.id
            )
        ).scalars().first()


        # First address automatically becomes default.
        is_default = existing_address is None


        # -----------------------------------------
        # Create address
        # -----------------------------------------
        address = Address(
            user_id=current_user.id,
            label=label,
            address_line_1=address_line_1,
            address_line_2=(
                address_line_2
                if address_line_2
                else None
            ),
            locality=locality,
            city=city,
            state=state,
            postal_code=postal_code,
            landmark=(
                landmark
                if landmark
                else None
            ),
            is_default=is_default
        )


        db.session.add(address)
        db.session.commit()


        flash(
            "Address added successfully.",
            "success"
        )


        return redirect(
            url_for("customer.profile")
        )


    return render_template(
        "customer/add_address.html"
    )


# -------------------------------------------------
# Edit address
# -------------------------------------------------
@customer_bp.route(
    "/addresses/<int:address_id>/edit",
    methods=["GET", "POST"]
)
@login_required
@customer_required
def edit_address(address_id):
    """
    Edit an address owned by the logged-in user.
    """

    address = db.session.get(
        Address,
        address_id
    )


    # Address does not exist.
    if address is None:
        abort(404)


    # SECURITY:
    # Prevent one customer from editing
    # another customer's address.
    if address.user_id != current_user.id:
        abort(403)


    if request.method == "POST":

        label = request.form.get(
            "label",
            ""
        ).strip()

        address_line_1 = request.form.get(
            "address_line_1",
            ""
        ).strip()

        address_line_2 = request.form.get(
            "address_line_2",
            ""
        ).strip()

        locality = request.form.get(
            "locality",
            ""
        ).strip()

        city = request.form.get(
            "city",
            ""
        ).strip()

        state = request.form.get(
            "state",
            ""
        ).strip()

        postal_code = request.form.get(
            "postal_code",
            ""
        ).strip()

        landmark = request.form.get(
            "landmark",
            ""
        ).strip()


        if not all([
            label,
            address_line_1,
            locality,
            city,
            state,
            postal_code
        ]):

            flash(
                "Please fill in all required fields.",
                "error"
            )

            return redirect(
                url_for(
                    "customer.edit_address",
                    address_id=address.id
                )
            )


        if (
            not postal_code.isdigit()
            or len(postal_code) != 6
        ):

            flash(
                "Please enter a valid 6-digit PIN code.",
                "error"
            )

            return redirect(
                url_for(
                    "customer.edit_address",
                    address_id=address.id
                )
            )


        address.label = label
        address.address_line_1 = address_line_1

        address.address_line_2 = (
            address_line_2
            if address_line_2
            else None
        )

        address.locality = locality
        address.city = city
        address.state = state
        address.postal_code = postal_code

        address.landmark = (
            landmark
            if landmark
            else None
        )


        db.session.commit()


        flash(
            "Address updated successfully.",
            "success"
        )


        return redirect(
            url_for("customer.profile")
        )


    return render_template(
        "customer/edit_address.html",
        address=address
    )


# -------------------------------------------------
# Set default address
# -------------------------------------------------
@customer_bp.route(
    "/addresses/<int:address_id>/default",
    methods=["POST"]
)
@login_required
@customer_required
def set_default_address(address_id):
    """
    Set one of the logged-in user's addresses
    as their default address.
    """

    address = db.session.get(
        Address,
        address_id
    )


    if address is None:
        abort(404)


    # Ownership check
    if address.user_id != current_user.id:
        abort(403)


    # -----------------------------------------
    # Remove default from user's other addresses
    # -----------------------------------------
    user_addresses = db.session.execute(
        db.select(Address).where(
            Address.user_id == current_user.id
        )
    ).scalars().all()


    for user_address in user_addresses:
        user_address.is_default = False


    # Make selected address default
    address.is_default = True


    db.session.commit()


    flash(
        "Default address updated.",
        "success"
    )


    return redirect(
        url_for("customer.profile")
    )


# -------------------------------------------------
# Delete address
# -------------------------------------------------
@customer_bp.route(
    "/addresses/<int:address_id>/delete",
    methods=["POST"]
)
@login_required
@customer_required
def delete_address(address_id):
    """
    Delete an address belonging to the
    currently logged-in user.
    """

    address = db.session.get(
        Address,
        address_id
    )


    if address is None:
        abort(404)


    # Ownership check
    if address.user_id != current_user.id:
        abort(403)


    was_default = address.is_default


    db.session.delete(address)
    db.session.flush()


    # -----------------------------------------
    # If default was deleted, choose another
    # address as default.
    # -----------------------------------------
    if was_default:

        next_address = db.session.execute(
            db.select(Address)
            .where(
                Address.user_id == current_user.id
            )
            .order_by(Address.id.asc())
        ).scalars().first()


        if next_address:
            next_address.is_default = True


    db.session.commit()


    flash(
        "Address deleted successfully.",
        "success"
    )


    return redirect(
        url_for("customer.profile")
    )
