from functools import wraps

from flask import abort
from flask_login import current_user


def admin_required(function):
    """
    Allow access only to ADMIN users.
    """

    @wraps(function)
    def decorated_function(*args, **kwargs):

        if current_user.role != "ADMIN":
            abort(403)

        return function(*args, **kwargs)

    return decorated_function


def provider_required(function):
    """
    Allow access only to PROVIDER users.
    """

    @wraps(function)
    def decorated_function(*args, **kwargs):

        if current_user.role != "PROVIDER":
            abort(403)

        return function(*args, **kwargs)

    return decorated_function


def customer_required(function):
    """
    Allow access only to CUSTOMER users.
    """

    @wraps(function)
    def decorated_function(*args, **kwargs):

        if current_user.role != "CUSTOMER":
            abort(403)

        return function(*args, **kwargs)

    return decorated_function
