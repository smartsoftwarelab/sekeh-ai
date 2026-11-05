"""
سرویس اعتبارسنجی رول و دسترسی ادمین
بررسی رول کاربر از دیتابیس
"""

from flask import current_app
from flask_jwt_extended import get_jwt_identity
from ..extensions import db
from ..models import User


def get_current_user_from_token():
    """
    دریافت کاربر جاری از JWT token
    بازگشت: User یا None
    """
    try:
        user_id = get_jwt_identity()
        if not user_id:
            return None
        
        # بازیابی کاربر از دیتابیس
        user = db.session.get(User, int(user_id))
        return user
    except (TypeError, ValueError, AttributeError):
        return None


def is_admin(user: User) -> bool:
    """
    بررسی اینکه آیا کاربر دارای رول admin است
    
    Args:
        user: instance User
    
    Returns:
        bool: True اگر رول admin باشد، False در غیر این صورت
    """
    if not user:
        return False
    
    # دوباره بازیابی رول از دیتابیس برای اطمینان از داده‌های فعال
    refreshed_user = db.session.get(User, user.user_id)
    if not refreshed_user:
        return False
    
    role = getattr(refreshed_user, 'role', None)
    return isinstance(role, str) and role.lower() == 'admin'


def require_admin_role():
    """
    دکوریتور برای بررسی دسترسی ادمین
    بازگشت: tuple (user, error_response)
    - اگر دسترسی معتبر باشد: (User, None)
    - اگر دسترسی غیرمعتبر باشد: (None, api_error_response)
    """
    from ..utils.response_utils import api_error
    
    # دریافت کاربر از token
    user = get_current_user_from_token()
    
    # بررسی وجود کاربر
    if not user:
        return None, api_error("invalid user or token expired", http_status=401)
    
    # بررسی رول ادمین از دیتابیس
    if not is_admin(user):
        current_app.logger.warning(
            f"Access denied: User {user.user_id} with role '{user.role}' tried to access admin resource"
        )
        return None, api_error("access denied: admin role required", http_status=403)
    
    return user, None