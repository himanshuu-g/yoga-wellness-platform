import os

from flask import Flask, render_template
from dotenv import load_dotenv


# -------------------------------------------------
# 1. Find backend directory
# -------------------------------------------------
backend_dir = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..")
)


# -------------------------------------------------
# 2. Load backend/.env BEFORE importing Config
# -------------------------------------------------
load_dotenv(
    os.path.join(backend_dir, ".env")
)


# -------------------------------------------------
# 3. Import application components
# -------------------------------------------------
from app.config import Config
from app.extensions import db, migrate, login_manager, csrf
from app.models import (
    User,
    CustomerProfile,
    Address,
    ServiceCategory,
    Service,
    ProviderProfile,
    ProviderService,
    ProviderAvailability
)


def create_app():
    """
    Create and configure the Flask application.
    """

    # -------------------------------------------------
    # 4. Find project root
    # -------------------------------------------------
    project_root = os.path.abspath(
        os.path.join(backend_dir, "..")
    )


    # -------------------------------------------------
    # 5. Configure frontend folders
    # -------------------------------------------------
    template_folder = os.path.join(
        project_root,
        "frontend",
        "templates"
    )

    static_folder = os.path.join(
        project_root,
        "frontend",
        "static"
    )


    # -------------------------------------------------
    # 6. Create Flask application
    # -------------------------------------------------
    app = Flask(
        __name__,
        template_folder=template_folder,
        static_folder=static_folder
    )


    # -------------------------------------------------
    # 7. Load Flask configuration
    # -------------------------------------------------
    app.config.from_object(Config)


    # -------------------------------------------------
    # 8. Initialize database
    # -------------------------------------------------
    db.init_app(app)

    migrate.init_app(
        app,
        db
    )


    # -------------------------------------------------
    # 9. Initialize Flask-Login
    # -------------------------------------------------
    login_manager.init_app(app)

    csrf.init_app(app)

    login_manager.login_view = "auth.login"

    login_manager.login_message = (
        "Please log in to access this page."
    )


    # -------------------------------------------------
    # 10. Tell Flask-Login how to load a user
    # -------------------------------------------------
    @login_manager.user_loader
    def load_user(user_id):
        """
        Load the logged-in user from PostgreSQL
        using the user ID stored in the session.
        """

        return db.session.get(
            User,
            int(user_id)
        )


    # -------------------------------------------------
    # 11. Home route
    # -------------------------------------------------
    @app.route("/")
    def home():
        return render_template(
            "public/home.html"
        )


    # -------------------------------------------------
    # 12. Register authentication Blueprint
    # -------------------------------------------------
    from app.auth import auth_bp

    app.register_blueprint(
        auth_bp,
        url_prefix="/auth"
    )

    from app.bookings import bookings_bp

    app.register_blueprint(
        bookings_bp,
        url_prefix="/bookings"
    )
    from app.customer import customer_bp

    app.register_blueprint(
        customer_bp,
        url_prefix="/customer"
    )

    from app.services import services_bp

    app.register_blueprint(
    services_bp,
    url_prefix="/services"
    )

    from app.admin import admin_bp

    app.register_blueprint(
    admin_bp,
    url_prefix="/admin"
    )

    from app.provider import provider_bp

    app.register_blueprint(
    provider_bp,
    url_prefix="/provider"
    )
    
    # -------------------------------------------------
    # 13. Return Flask application
    # -------------------------------------------------
    return app