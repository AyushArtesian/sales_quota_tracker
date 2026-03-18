"""Authentication module for Sales Quota Tracker"""

from auth.manager import (
    check_authentication,
    show_logout_button,
    get_current_user,
    logout_user,
)

__all__ = [
    "check_authentication",
    "show_logout_button", 
    "get_current_user",
    "logout_user",
]