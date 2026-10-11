from flask import (
    render_template,
    request,
    redirect,
    url_for,
    flash
)

from flask_login import (
    login_user,
    logout_user,
    login_required,
    current_user
)

from app.extensions import db
from app.models.user import User
from app.auth import auth_bp


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    """
    Register a new customer account.
    """

    if current_user.is_authenticated:
        return redirect(url_for("home"))

    if request.method == "POST":

        # -----------------------------------------
        # Read and normalize form data
        # -----------------------------------------
        name = request.form.get(
            "name",
            ""
        ).strip()

        email = request.form.get(
            "email",
            ""
        ).strip().lower()

        phone = request.form.get(
            "phone",
            ""
        ).strip()

        password = request.form.get(
            "password",
            ""
        )

        confirm_password = request.form.get(
            "confirm_password",
            ""
        )


        # -----------------------------------------
        # Required fields
        # -----------------------------------------
        if not name or not email or not password:

            flash(
                "Name, email and password are required.",
                "error"
            )

            return redirect(
                url_for("auth.register")
            )


        # -----------------------------------------
        # Name validation
        # -----------------------------------------
        if len(name) < 2 or len(name) > 100:

            flash(
                "Please enter a valid name.",
                "error"
            )

            return redirect(
                url_for("auth.register")
            )


        # -----------------------------------------
        # Basic email validation
        # -----------------------------------------
        if (
            "@" not in email
            or "." not in email.split("@")[-1]
        ):

            flash(
                "Please enter a valid email address.",
                "error"
            )

            return redirect(
                url_for("auth.register")
            )


        # -----------------------------------------
        # Password validation
        # -----------------------------------------
        if len(password) < 8:

            flash(
                "Password must contain at least 8 characters.",
                "error"
            )

            return redirect(
                url_for("auth.register")
            )


        if password != confirm_password:

            flash(
                "Passwords do not match.",
                "error"
            )

            return redirect(
                url_for("auth.register")
            )


        # -----------------------------------------
        # Normalize phone number
        #
        # For now we accept:
        # 9876543210
        # +919876543210
        # -----------------------------------------
        if phone:

            normalized_phone = (
                phone
                .replace(" ", "")
                .replace("-", "")
            )

            if normalized_phone.startswith("+91"):
                normalized_phone = normalized_phone[3:]

            if (
                not normalized_phone.isdigit()
                or len(normalized_phone) != 10
            ):

                flash(
                    "Please enter a valid 10-digit mobile number.",
                    "error"
                )

                return redirect(
                    url_for("auth.register")
                )

            phone = normalized_phone


        # -----------------------------------------
        # Duplicate email check
        # -----------------------------------------
        existing_email = db.session.execute(
            db.select(User).where(
                User.email == email
            )
        ).scalar_one_or_none()

        if existing_email:

            flash(
                "An account with this email already exists.",
                "error"
            )

            return redirect(
                url_for("auth.register")
            )


        # -----------------------------------------
        # Duplicate phone check
        # -----------------------------------------
        if phone:

            existing_phone = db.session.execute(
                db.select(User).where(
                    User.phone == phone
                )
            ).scalar_one_or_none()

            if existing_phone:

                flash(
                    "An account with this phone number already exists.",
                    "error"
                )

                return redirect(
                    url_for("auth.register")
                )


        # -----------------------------------------
        # Create CUSTOMER account
        # -----------------------------------------
        user = User(
            name=name,
            email=email,
            phone=phone if phone else None,
            role="CUSTOMER"
        )


        # -----------------------------------------
        # Hash password
        # -----------------------------------------
        user.set_password(password)


        # -----------------------------------------
        # Save user
        # -----------------------------------------
        db.session.add(user)
        db.session.commit()


        flash(
            "Account created successfully. Please log in.",
            "success"
        )


        return redirect(
            url_for("auth.login")
        )


    return render_template(
        "auth/register.html"
    )

@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    """
    Authenticate an existing user.
    """

    if current_user.is_authenticated:
        return redirect(url_for("home"))

    if request.method == "POST":

        email = request.form.get(
            "email",
            ""
        ).strip().lower()

        password = request.form.get(
            "password",
            ""
        )

        user = db.session.execute(
            db.select(User).where(
                User.email == email
            )
        ).scalar_one_or_none()

        if user is None or not user.check_password(password):

            flash(
                "Invalid email or password.",
                "error"
            )

            return redirect(
                url_for("auth.login")
            )

        if not user.is_active:
            flash(
                "This account is currently disabled.",
                "error"
            )

            return redirect(
                url_for("auth.login")
            )

        login_user(user)

        return redirect(
            url_for("home")
        )

    return render_template(
        "auth/login.html"
    )

@auth_bp.route("/logout", methods=["POST"])
@login_required
def logout():
    """
    Log the current user out.
    """

    logout_user()

    flash(
        "You have been logged out.",
        "success"
    )

    return redirect(
        url_for("home")
    )