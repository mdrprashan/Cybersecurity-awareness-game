"""
auth.py — Authentication Blueprint
ICT932 – Cybersecurity Testing and Assurance
Author: Prashan Manandhar (CIHE241182)

Security fixes applied:
  - disable_2fa: students blocked, teacher-only
  - setup_2fa: students with 2FA already enabled are blocked from resetting their own secret
  - verify_2fa: uses db.session.get() instead of deprecated User.query.get()
  - TOTP verify uses valid_window=1 to handle clock drift (±30s)
"""

import pyotp
import qrcode
import io
import base64
from functools import wraps

from flask import (Blueprint, render_template, redirect, url_for,
                   flash, request, session)
from flask_login import login_user, logout_user, login_required, current_user

from extensions import db, bcrypt
from models import User
from security import log_login_attempt, is_account_locked

auth_bp = Blueprint('auth', __name__)

# Valid answer choices — used for input validation
VALID_ANSWERS = {'A', 'B', 'C', 'D'}


def _validate_password_strength(password: str) -> list:
    """Return a list of unmet password requirements."""
    errors = []
    if len(password) < 8:
        errors.append('Password must be at least 8 characters.')
    if not any(c.isupper() for c in password):
        errors.append('Password must contain at least one uppercase letter.')
    if not any(c.islower() for c in password):
        errors.append('Password must contain at least one lowercase letter.')
    if not any(c.isdigit() for c in password):
        errors.append('Password must contain at least one number.')
    if not any(c in '!@#$%^&*()_+-=[]{};\':\"\\|,.<>/?`~' for c in password):
        errors.append('Password must contain at least one special character.')
    return errors


def teacher_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_teacher:
            flash('Access denied. Teachers only.', 'danger')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated


def _home_for(user):
    """Return the correct home URL for a given user role."""
    return url_for('admin.dashboard') if user.is_teacher else url_for('game.challenges')


# ── Register ──────────────────────────────────────────────────────────────────

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(_home_for(current_user))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email    = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        confirm  = request.form.get('confirm_password', '')
        role     = request.form.get('role', 'student')

        if not username or not email or not password:
            flash('All fields are required.', 'danger')
            return render_template('register.html')

        if password != confirm:
            flash('Passwords do not match.', 'danger')
            return render_template('register.html')

        pw_errors = _validate_password_strength(password)
        if pw_errors:
            for err in pw_errors:
                flash(err, 'danger')
            return render_template('register.html')

        # SECURITY: generic messages prevent username/email enumeration
        if User.query.filter_by(email=email).first():
            flash('An account with that email already exists.', 'danger')
            return render_template('register.html')

        if User.query.filter_by(username=username).first():
            flash('That username is already taken.', 'danger')
            return render_template('register.html')

        if role == 'teacher' and request.form.get('teacher_code') != 'CIHE-TEACH-2026':
            flash('Invalid teacher registration code.', 'danger')
            return render_template('register.html')

        hashed_pw = bcrypt.generate_password_hash(password).decode('utf-8')
        user = User(username=username, email=email, password=hashed_pw, role=role)
        db.session.add(user)
        db.session.commit()

        # Auto-login and redirect straight to 2FA setup
        login_user(user)
        flash(f'Welcome to CyberQuest, {user.username}! 🎉 '
              'Please set up Two-Factor Authentication to secure your account.', 'success')
        return redirect(url_for('auth.setup_2fa'))

    return render_template('register.html')


# ── Login ─────────────────────────────────────────────────────────────────────

@auth_bp.route('/login', methods=['GET', 'POST'])
@auth_bp.route('/', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(_home_for(current_user))

    if request.method == 'POST':
        email    = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        remember = request.form.get('remember') == 'on'
        ip       = request.remote_addr

        # Brute-force lockout check
        if is_account_locked(email):
            flash('Account temporarily locked after too many failed attempts. '
                  'Try again in 15 minutes.', 'danger')
            log_login_attempt(email=email, ip=ip, success=False)
            return render_template('login.html')

        user = User.query.filter_by(email=email).first()

        if user and bcrypt.check_password_hash(user.password, password):
            log_login_attempt(email=email, ip=ip, success=True, user_id=user.id)

            # 2FA already configured → verify before completing login
            if user.is_2fa_enabled:
                session['pre_2fa_user_id'] = user.id
                session['pre_2fa_remember'] = remember
                return redirect(url_for('auth.verify_2fa'))

            # 2FA not configured → login and prompt setup
            login_user(user, remember=remember)
            flash(f'Welcome back, {user.username}! 👋', 'success')
            flash('🔐 Please set up Two-Factor Authentication to secure your account.', 'warning')
            return redirect(url_for('auth.setup_2fa'))

        else:
            # SECURITY: identical message whether email exists or not
            log_login_attempt(email=email, ip=ip, success=False,
                              user_id=user.id if user else None)
            flash('Invalid email or password.', 'danger')

    return render_template('login.html')


# ── Logout ────────────────────────────────────────────────────────────────────

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('auth.login'))


# ── 2FA Setup ─────────────────────────────────────────────────────────────────

@auth_bp.route('/2fa/setup', methods=['GET', 'POST'])
@login_required
def setup_2fa():
    # SECURITY FIX: students who already have 2FA enabled cannot reset their own secret
    # Only teachers can reset student 2FA (via the admin dashboard)
    if not current_user.is_teacher and current_user.is_2fa_enabled:
        flash('Your 2FA is already active. Contact your teacher if you need to reset it.', 'info')
        return redirect(url_for('game.challenges'))

    if request.method == 'POST':
        token = request.form.get('token', '').strip()

        # Validate token is 6 digits before querying TOTP
        if not token.isdigit() or len(token) != 6:
            flash('Please enter a valid 6-digit code.', 'danger')
            return redirect(url_for('auth.setup_2fa'))

        totp = pyotp.TOTP(current_user.totp_secret)
        # valid_window=1 allows ±30s clock drift
        if totp.verify(token, valid_window=1):
            current_user.is_2fa_enabled = True
            db.session.commit()
            flash('🔐 Two-Factor Authentication enabled! Your account is now fully secured.', 'success')
            return redirect(_home_for(current_user))
        else:
            flash('Invalid verification code — please try again.', 'danger')

    if not current_user.totp_secret:
        current_user.totp_secret = pyotp.random_base32()
        db.session.commit()

    totp = pyotp.TOTP(current_user.totp_secret)
    provisioning_uri = totp.provisioning_uri(
        name=current_user.email, issuer_name='CyberQuest ICT932')

    qr  = qrcode.make(provisioning_uri)
    buf = io.BytesIO()
    qr.save(buf, format='PNG')
    qr_b64 = base64.b64encode(buf.getvalue()).decode('utf-8')

    return render_template('2fa_setup.html',
                           qr_code=qr_b64,
                           secret=current_user.totp_secret)


# ── 2FA Skip ──────────────────────────────────────────────────────────────────

@auth_bp.route('/2fa/skip')
@login_required
def skip_2fa():
    """Lets the user skip 2FA setup and go to their home page."""
    flash('You skipped 2FA setup. You will be prompted again on next login.', 'info')
    return redirect(_home_for(current_user))


# ── 2FA Verify ────────────────────────────────────────────────────────────────

@auth_bp.route('/2fa/verify', methods=['GET', 'POST'])
def verify_2fa():
    user_id = session.get('pre_2fa_user_id')
    if not user_id:
        return redirect(url_for('auth.login'))

    # SECURITY FIX: use db.session.get() — User.query.get() is deprecated
    user = db.session.get(User, user_id)
    if not user:
        session.pop('pre_2fa_user_id', None)
        return redirect(url_for('auth.login'))

    if request.method == 'POST':
        token = request.form.get('token', '').strip()

        if not token.isdigit() or len(token) != 6:
            flash('Please enter a valid 6-digit code.', 'danger')
            return render_template('2fa_verify.html')

        totp = pyotp.TOTP(user.totp_secret)
        if totp.verify(token, valid_window=1):
            remember = session.pop('pre_2fa_remember', False)
            session.pop('pre_2fa_user_id', None)
            login_user(user, remember=remember)
            flash(f'Welcome back, {user.username}! ✅', 'success')
            return redirect(_home_for(user))
        else:
            flash('Invalid authentication code. Please try again.', 'danger')

    return render_template('2fa_verify.html')


# ── Disable 2FA — TEACHER ONLY ────────────────────────────────────────────────

@auth_bp.route('/2fa/disable', methods=['POST'])
@login_required
def disable_2fa():
    # SECURITY FIX: students cannot disable their own 2FA
    # Only teachers can do this for themselves; student 2FA is reset via admin dashboard
    if not current_user.is_teacher:
        flash('Students cannot disable 2FA. Ask your teacher to reset it for you.', 'danger')
        return redirect(url_for('game.challenges'))

    current_user.is_2fa_enabled = False
    current_user.totp_secret    = None
    db.session.commit()
    flash('Two-Factor Authentication has been disabled. '
          'You will be prompted to set it up again on next login.', 'warning')
    return redirect(_home_for(current_user))
