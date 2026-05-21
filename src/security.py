"""
security.py — Security Blueprint & Utilities
ICT932 – Cybersecurity Testing and Assurance
Author: Prashan Manandhar (CIHE241182)
"""

from datetime import datetime, timedelta
from functools import wraps

from flask import Blueprint, render_template, redirect, url_for, flash, current_app
from flask_login import login_required, current_user

from extensions import db
from models import LoginAttempt, User

security_bp = Blueprint('security', __name__, url_prefix='/security')


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
    """Return True if too many failed attempts occurred within the lockout window."""
    max_attempts    = current_app.config.get('MAX_LOGIN_ATTEMPTS', 5)
    lockout_minutes = current_app.config.get('LOCKOUT_MINUTES', 15)
    window_start    = datetime.utcnow() - timedelta(minutes=lockout_minutes)

    failed_count = LoginAttempt.query.filter(
        LoginAttempt.email == email,
        LoginAttempt.success == False,
        LoginAttempt.attempted_at >= window_start
    ).count()

    return failed_count >= max_attempts


def get_recent_attempts(email: str, minutes: int = 60) -> list:
    window = datetime.utcnow() - timedelta(minutes=minutes)
    return LoginAttempt.query.filter(
        LoginAttempt.email == email,
        LoginAttempt.attempted_at >= window
    ).order_by(LoginAttempt.attempted_at.desc()).all()


def role_required(*roles):
    """Decorator — restrict a route to users with one of the given roles."""
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


@security_bp.route('/audit-log')
@login_required
@role_required('teacher')
def audit_log():
    attempts   = LoginAttempt.query.order_by(LoginAttempt.attempted_at.desc()).limit(100).all()
    total      = len(attempts)
    successful = sum(1 for a in attempts if a.success)
    failed     = total - successful
    return render_template('security/audit_log.html',
                           attempts=attempts, total=total,
                           successful=successful, failed=failed)


@security_bp.route('/locked-accounts')
@login_required
@role_required('teacher')
def locked_accounts():
    max_attempts    = current_app.config.get('MAX_LOGIN_ATTEMPTS', 5)
    lockout_minutes = current_app.config.get('LOCKOUT_MINUTES', 15)
    window_start    = datetime.utcnow() - timedelta(minutes=lockout_minutes)

    from sqlalchemy import func
    locked = (
        db.session.query(
            LoginAttempt.email,
            func.count(LoginAttempt.id).label('fail_count')
        )
        .filter(LoginAttempt.success == False,
                LoginAttempt.attempted_at >= window_start)
        .group_by(LoginAttempt.email)
        .having(func.count(LoginAttempt.id) >= max_attempts)
        .all()
    )
    return render_template('security/locked_accounts.html',
                           locked=locked, lockout_minutes=lockout_minutes)
