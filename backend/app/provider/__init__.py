from flask import Blueprint


provider_bp = Blueprint(
    "provider",
    __name__
)


from app.provider import routes