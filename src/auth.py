"""
auth.py — Authentication Blueprint
ICT932 – Cybersecurity Testing and Assurance
Author: Prashan Manandhar (CIHE241182)

Covers: login, register, logout, 2FA setup (TOTP) and verification.
"""

import pyotp
import qrcode
import io
import base64
from functools import wraps

from flask import (Blueprint, render_template, redirect, url_for,
                   flash, request, session)
from flask_login import login_user, logout_user, login_required, current_user

from app import db, bcrypt
from models import User
from security import log_login_attempt, is_account_locked

auth_bp = Blueprint('auth', __name__)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _validate_password_strength(password: str) -> list[str]:
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
    """Decorator — restricts route to teacher role."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_teacher:
            flash('Access denied. Teachers only.', 'danger')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated


# ── Register ─────────────────────────────────────────────────────────────────

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('game.challenges'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email    = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        confirm  = request.form.get('confirm_password', '')
        role     = request.form.get('role', 'student')

        # ── Validation ────────────────────────────────────────────────────────
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

        if User.query.filter_by(email=email).first():
            flash('An account with that email already exists.', 'danger')
            return render_template('register.html')

        if User.query.filter_by(username=username).first():
            flash('That username is already taken.', 'danger')
            return render_template('register.html')

        # Only allow teacher role if a special code is provided (basic RBAC guard)
        if role == 'teacher' and request.form.get('teacher_code') != 'CIHE-TEACH-2026':
            flash('Invalid teacher registration code.', 'danger')
            return render_template('register.html')

        # ── Create user ───────────────────────────────────────────────────────
        hashed_pw = bcrypt.generate_password_hash(password).decode('utf-8')
        user = User(username=username, email=email,
                    password=hashed_pw, role=role)
        db.session.add(user)
        db.session.commit()

        flash('Account created successfully! Please log in.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('register.html')


# ── Login ─────────────────────────────────────────────────────────────────────

@auth_bp.route('/login', methods=['GET', 'POST'])
@auth_bp.route('/', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('game.challenges'))

    if request.method == 'POST':
        email    = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        ip       = request.remote_addr

        # ── Brute-force lockout check ─────────────────────────────────────────
        if is_account_locked(email):
            flash('Account temporarily locked due to too many failed attempts. '
                  'Please try again in 15 minutes.', 'danger')
            log_login_attempt(email=email, ip=ip, success=False)
            return render_template('login.html')

        user = User.query.filter_by(email=email).first()

        if user and bcrypt.check_password_hash(user.password, password):
            log_login_attempt(email=email, ip=ip, success=True, user_id=user.id)

            # ── 2FA check ─────────────────────────────────────────────────────
            if user.is_2fa_enabled:
                session['pre_2fa_user_id'] = user.id
                return redirect(url_for('auth.verify_2fa'))

            login_user(user)
            flash(f'Welcome back, {user.username}!', 'success')
            next_page = request.args.get('next')
            return redirect(next_page or url_for('game.challenges'))

        else:
            log_login_attempt(email=email, ip=ip, success=False,
                              user_id=user.id if user else None)
            flash('Invalid email or password.', 'danger')

    return render_template('login.html')


# ── Logout ────────────────────────────────────────────────────────────────────

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))


# ── 2FA Setup ─────────────────────────────────────────────────────────────────

@auth_bp.route('/2fa/setup', methods=['GET', 'POST'])
@login_required
def setup_2fa():
    if request.method == 'POST':
        token = request.form.get('token', '').strip()
        totp  = pyotp.TOTP(current_user.totp_secret)

        if totp.verify(token):
            current_user.is_2fa_enabled = True
            db.session.commit()
            flash('Two-Factor Authentication enabled successfully! 🔐', 'success')
            return redirect(url_for('game.challenges'))
        else:
            flash('Invalid code. Please try again.', 'danger')

    # Generate a new TOTP secret if the user doesn't have one yet
    if not current_user.totp_secret:
        current_user.totp_secret = pyotp.random_base32()
        db.session.commit()

    totp        = pyotp.TOTP(current_user.totp_secret)
    provisioning_uri = totp.provisioning_uri(
        name=current_user.email,
        issuer_name='CyberQuest ICT932'
    )

    # Generate QR code as base64 image
    qr  = qrcode.make(provisioning_uri)
    buf = io.BytesIO()
    qr.save(buf, format='PNG')
    qr_b64 = base64.b64encode(buf.getvalue()).decode('utf-8')

    return render_template('2fa_setup.html',
                           qr_code=qr_b64,
                           secret=current_user.totp_secret)


# ── 2FA Verify ────────────────────────────────────────────────────────────────

@auth_bp.route('/2fa/verify', methods=['GET', 'POST'])
def verify_2fa():
    user_id = session.get('pre_2fa_user_id')
    if not user_id:
        return redirect(url_for('auth.login'))

    user = User.query.get(user_id)
    if not user:
        session.pop('pre_2fa_user_id', None)
        return redirect(url_for('auth.login'))

    if request.method == 'POST':
        token = request.form.get('token', '').strip()
        totp  = pyotp.TOTP(user.totp_secret)

        if totp.verify(token):
            session.pop('pre_2fa_user_id', None)
            login_user(user)
            flash(f'Welcome back, {user.username}! ✅', 'success')
            return redirect(url_for('game.challenges'))
        else:
            flash('Invalid authentication code. Please try again.', 'danger')

    return render_template('2fa_verify.html')


# ── Profile / Disable 2FA ─────────────────────────────────────────────────────

@auth_bp.route('/2fa/disable', methods=['POST'])
@login_required
def disable_2fa():
    current_user.is_2fa_enabled = False
    current_user.totp_secret    = None
    db.session.commit()
    flash('Two-Factor Authentication has been disabled.', 'warning')
    return redirect(url_for('game.challenges'))
