# =============================================================
# security.py — Security Utilities (Placeholder)
# Author: Prashan Manandhar (CIHE241182)
# Full implementation coming in Week 8
# =============================================================

from models import db, LoginAttempt
from datetime import datetime


def log_login_attempt(user_id, success, ip_address):
    """
    Records a login attempt to the database.
    Used to detect and audit brute force attacks.

    Args:
        user_id (int): ID of the user attempting login (None if user not found)
        success (bool): True if login succeeded, False if it failed
        ip_address (str): IP address of the request
    """
    attempt = LoginAttempt(
        user_id=user_id,
        success=success,
        ip_address=ip_address,
        timestamp=datetime.utcnow()
    )
    db.session.add(attempt)
    db.session.commit()