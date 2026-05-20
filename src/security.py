"""
security.py — Security Blueprint & Utilities
ICT932 – Cybersecurity Testing and Assurance
Author: Prashan Manandhar (CIHE241182)

Covers: login attempt logging, brute-force lockout detection,
        RBAC access control decorators, and security audit endpoints.
"""

from datetime import datetime, timedelta
from functools import wraps

from flask import Blueprint, render_template, redirect, url_for, flash, current_app
from flask_login import login_required, current_user

from app import db
from models import LoginAttempt, User

security_bp = Blueprint('security', __name__, url_prefix='/security')


# ══════════════════════════════════════════════════════════════════════════════
# Utility functions (imported by auth.py)
# ══════════════════════════════════════════════════════════════════════════════

def log_login_attempt(email: str, ip: str, success: bool, user_id: int = None):
    """Record every login attempt for audit and brute-force detection."""
    attempt = LoginAttempt(
        user_id=user_id,
        email=email,
        ip_address=ip,
        success=success,
        attempted_at=datetime.utcnow()
    )
    db.session.add(attempt)
    db.session.commit()


def is_account_locked(email: str) -> bool:
    """
    Return True if the account should be temporarily locked.

    Locking logic:
    - Count failed attempts in the last LOCKOUT_MINUTES minutes.
    - If count >= MAX_LOGIN_ATTEMPTS, account is locked.
    """
    max_attempts   = current_app.config.get('MAX_LOGIN_ATTEMPTS', 5)
    lockout_minutes = current_app.config.get('LOCKOUT_MINUTES', 15)
    window_start   = datetime.utcnow() - timedelta(minutes=lockout_minutes)

    failed_count = LoginAttempt.query.filter(
        LoginAttempt.email == email,
        LoginAttempt.success == False,         # noqa: E712
        LoginAttempt.attempted_at >= window_start
    ).count()

    return failed_count >= max_attempts


def get_recent_attempts(email: str, minutes: int = 60) -> list:
    """Return recent login attempts for a given email (for display/audit)."""
    window = datetime.utcnow() - timedelta(minutes=minutes)
    return LoginAttempt.query.filter(
        LoginAttempt.email == email,
        LoginAttempt.attempted_at >= window
    ).order_by(LoginAttempt.attempted_at.desc()).all()


# ══════════════════════════════════════════════════════════════════════════════
# RBAC Decorators
# ══════════════════════════════════════════════════════════════════════════════

def role_required(*roles):
    """
    Decorator factory — restrict a route to users with one of the given roles.

    Usage:
        @role_required('teacher')
        @role_required('teacher', 'admin')
    """
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if not current_user.is_authenticated:
                flash('Please log in to continue.', 'warning')
                return redirect(url_for('auth.login'))
            if current_user.role not in roles:
                flash('You do not have permission to access this page.', 'danger')
                return redirect(url_for('game.challenges'))
            return f(*args, **kwargs)
        return decorated
    return decorator


# ══════════════════════════════════════════════════════════════════════════════
# Security Admin Routes (teacher-only)
# ══════════════════════════════════════════════════════════════════════════════

@security_bp.route('/audit-log')
@login_required
@role_required('teacher')
def audit_log():
    """Display recent login attempts — visible to teachers only."""
    attempts = LoginAttempt.query.order_by(
        LoginAttempt.attempted_at.desc()
    ).limit(100).all()

    # Build summary stats
    total      = len(attempts)
    successful = sum(1 for a in attempts if a.success)
    failed     = total - successful

    return render_template('security/audit_log.html',
                           attempts=attempts,
                           total=total,
                           successful=successful,
                           failed=failed)


@security_bp.route('/locked-accounts')
@login_required
@role_required('teacher')
def locked_accounts():
    """Show which email addresses are currently locked out."""
    max_attempts    = current_app.config.get('MAX_LOGIN_ATTEMPTS', 5)
    lockout_minutes = current_app.config.get('LOCKOUT_MINUTES', 15)
    window_start    = datetime.utcnow() - timedelta(minutes=lockout_minutes)

    # Group failed attempts by email within the lockout window
    from sqlalchemy import func
    locked = (
        db.session.query(
            LoginAttempt.email,
            func.count(LoginAttempt.id).label('fail_count')
        )
        .filter(
            LoginAttempt.success == False,          # noqa: E712
            LoginAttempt.attempted_at >= window_start
        )
        .group_by(LoginAttempt.email)
        .having(func.count(LoginAttempt.id) >= max_attempts)
        .all()
    )

    return render_template('security/locked_accounts.html',
                           locked=locked,
                           lockout_minutes=lockout_minutes)
