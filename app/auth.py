from flask_login import current_user
from functools import wraps
from flask import abort

def admin_required(func):
    @wraps(func)
    def decorated_view(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            abort(403)  # 403 Forbidden
        return func(*args, **kwargs)
    return decorated_view