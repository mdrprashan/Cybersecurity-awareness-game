# =============================================================
# auth.py — Authentication Blueprint
# Author: Prashan Manandhar (CIHE241182)
# Features: Register, Login (Remember Me), Logout,
#           Forgot Password, Reset Password, 2FA, RBAC
# =============================================================

from flask import (Blueprint, render_template, redirect,
                   url_for, flash, request, session, make_response)
from flask_login import login_user, logout_user, login_required, current_user
from functools import wraps
from models import db, User
from security import log_login_attempt

auth_bp = Blueprint('auth', __name__)


# =============================================================
# RBAC Decorators
# =============================================================

def student_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('auth.login'))
        if current_user.role != 'student':
            flash('This page is for students only.', 'danger')
            return redirect(url_for('admin.dashboard'))
        return f(*args, **kwargs)
    return decorated_function


def teacher_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('auth.login'))
        if current_user.role != 'teacher':
            flash('This page is for teachers only.', 'danger')
            return redirect(url_for('game.challenges'))
        return f(*args, **kwargs)
    return decorated_function


# =============================================================
# REGISTER
# =============================================================

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

        errors = []
        if not username or len(username) < 3:
            errors.append('Username must be at least 3 characters.')
        if not email or '@' not in email:
            errors.append('Please enter a valid email address.')
        if len(password) < 8:
            errors.append('Password must be at least 8 characters.')
        if password != confirm:
            errors.append('Passwords do not match.')
        if role not in ['student', 'teacher']:
            errors.append('Invalid role selected.')
        if User.query.filter_by(email=email).first():
            errors.append('An account with this email already exists.')
        if User.query.filter_by(username=username).first():
            errors.append('This username is already taken.')

        if errors:
            for error in errors:
                flash(error, 'danger')
            return render_template('register.html', username=username, email=email, role=role)

        from app import bcrypt
        password_hash = bcrypt.generate_password_hash(password).decode('utf-8')
        new_user = User(username=username, email=email,
                        password_hash=password_hash, role=role)
        db.session.add(new_user)
        db.session.commit()

        login_user(new_user)
        flash(f'Account created! Welcome, {username}. Please set up Google Authenticator.', 'success')
        return redirect(url_for('auth.setup_2fa'))

    return render_template('register.html')


# =============================================================
# LOGIN — with Remember Me
# =============================================================

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        if current_user.role == 'teacher':
            return redirect(url_for('admin.dashboard'))
        return redirect(url_for('game.challenges'))

    if request.method == 'POST':
        username    = request.form.get('username', '').strip()
        password    = request.form.get('password', '')
        remember_me = request.form.get('remember_me') == 'on'
        ip          = request.remote_addr

        user = User.query.filter_by(username=username).first()

        if not user:
            log_login_attempt(None, False, ip)
            flash('Invalid username or password.', 'danger')
            return render_template('login.html', username=username)

        from app import bcrypt
        if not bcrypt.check_password_hash(user.password_hash, password):
            user.login_attempts += 1
            db.session.commit()
            log_login_attempt(user.id, False, ip)
            flash('Invalid username or password.', 'danger')
            return render_template('login.html', username=username)

        user.login_attempts = 0
        db.session.commit()
        log_login_attempt(user.id, True, ip)

        session['pre_2fa_user_id']  = user.id
        session['pre_2fa_remember'] = remember_me

        if user.has_2fa_enabled():
            return redirect(url_for('auth.verify_2fa'))
        else:
            login_user(user, remember=remember_me)
            flash(f'Welcome back, {user.username}!', 'success')
            return redirect(url_for('admin.dashboard') if user.role == 'teacher'
                            else url_for('game.challenges'))

    return render_template('login.html')


# =============================================================
# LOGOUT — fixed to properly clear session and cookies
# =============================================================

@auth_bp.route('/logout')
@login_required
def logout():
    """
    Proper logout that:
    1. Captures username before clearing
    2. Calls Flask-Login logout_user() to invalidate the login session
    3. Completely clears the server-side session data
    4. Deletes session and remember_token cookies from the browser
    5. Redirects to login page (not index) so user clearly knows they are logged out
    6. Cache-control headers are handled globally in app.py after_request
    """
    username = current_user.username
    role     = current_user.role

    # Step 1: Flask-Login logout — marks user as anonymous
    logout_user()

    # Step 2: Wipe the entire server-side session
    session.clear()

    # Step 3: Build redirect response
    # Teachers go to login, students go to login — both see the login page
    # This makes it clear to the user they are now logged out
    response = make_response(redirect(url_for('auth.login')))

    # Step 4: Delete cookies from browser
    response.delete_cookie('session')
    response.delete_cookie('remember_token')

    # Step 5: Cache-control to prevent back button from showing protected pages
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate, private'
    response.headers['Pragma']        = 'no-cache'
    response.headers['Expires']       = '0'

    # Flash message will show on the login page
    from flask import get_flashed_messages
    from flask import flash as _flash
    _flash(f'You have been logged out successfully. See you next time, {username}!', 'info')

    return response

# =============================================================
# FORGOT PASSWORD
# =============================================================

@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        user  = User.query.filter_by(email=email).first()

        flash('If an account exists with that email, a password reset link has been sent.', 'info')

        if user:
            token     = generate_reset_token(user.email)
            reset_url = url_for('auth.reset_password', token=token, _external=True)
            send_reset_email(user, reset_url)

        return redirect(url_for('auth.login'))

    return render_template('forgot_password.html')


def generate_reset_token(email):
    from itsdangerous import URLSafeTimedSerializer
    from flask import current_app
    s = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    return s.dumps(email, salt='password-reset-salt')


def verify_reset_token(token, max_age=1800):
    from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature
    from flask import current_app
    s = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    try:
        email = s.loads(token, salt='password-reset-salt', max_age=max_age)
    except (SignatureExpired, BadSignature):
        return None
    return email


def send_reset_email(user, reset_url):
    from flask_mail import Message
    from app import mail
    msg = Message(
        subject='CyberQuest — Password Reset Request',
        recipients=[user.email]
    )
    msg.html = f"""
    <div style="font-family: Arial, sans-serif; max-width: 500px; margin: auto;
                background: #0D1B2A; color: #FFFFFF; padding: 30px; border-radius: 10px;
                border: 2px solid #FFD700;">
        <h2 style="color: #FFD700;">🛡️ CyberQuest Password Reset</h2>
        <p>Hi <strong style="color: #FFD700;">{user.username}</strong>,</p>
        <p>We received a request to reset your password. Click the button below:</p>
        <div style="text-align: center; margin: 30px 0;">
            <a href="{reset_url}"
               style="background-color: #FFD700; color: #0D1B2A; padding: 12px 30px;
                      text-decoration: none; border-radius: 6px; font-weight: bold;">
                Reset My Password
            </a>
        </div>
        <p style="color: #A0B4C8; font-size: 0.9rem;">
            This link expires in <strong style="color: #FFD700;">30 minutes</strong>.<br>
            If you did not request this, you can safely ignore this email.
        </p>
        <hr style="border-color: #2A4A6F;">
        <p style="color: #A0B4C8; font-size: 0.8rem; text-align: center;">
            CyberQuest — ICT932 | Crown Institute of Higher Education (CIHE)
        </p>
    </div>
    """
    mail.send(msg)


# =============================================================
# RESET PASSWORD
# =============================================================

@auth_bp.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    email = verify_reset_token(token)
    if not email:
        flash('The password reset link is invalid or has expired. Please request a new one.', 'danger')
        return redirect(url_for('auth.forgot_password'))

    user = User.query.filter_by(email=email).first()
    if not user:
        flash('User not found.', 'danger')
        return redirect(url_for('auth.forgot_password'))

    if request.method == 'POST':
        password = request.form.get('password', '')
        confirm  = request.form.get('confirm_password', '')

        if len(password) < 8:
            flash('Password must be at least 8 characters.', 'danger')
            return render_template('reset_password.html', token=token)
        if password != confirm:
            flash('Passwords do not match.', 'danger')
            return render_template('reset_password.html', token=token)

        from app import bcrypt
        user.password_hash  = bcrypt.generate_password_hash(password).decode('utf-8')
        user.login_attempts = 0
        db.session.commit()

        flash('Password reset successfully! Please log in with your new password.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('reset_password.html', token=token)


# =============================================================
# 2FA SETUP
# =============================================================

@auth_bp.route('/setup-2fa', methods=['GET', 'POST'])
@login_required
def setup_2fa():
    import pyotp, qrcode, io, base64

    if request.method == 'POST':
        code   = request.form.get('code', '').strip()
        secret = request.form.get('secret', '').strip()

        if pyotp.TOTP(secret).verify(code):
            current_user.totp_secret = secret
            db.session.commit()
            flash('Google Authenticator has been linked to your account!', 'success')
            return redirect(url_for('admin.dashboard') if current_user.role == 'teacher'
                            else url_for('game.challenges'))
        else:
            flash('Invalid code. Please try again.', 'danger')
            return redirect(url_for('auth.setup_2fa'))

    secret = pyotp.random_base32()
    uri    = pyotp.TOTP(secret).provisioning_uri(
                name=current_user.email, issuer_name='CyberQuest')
    buf    = io.BytesIO()
    qrcode.make(uri).save(buf, format='PNG')
    qr_b64 = base64.b64encode(buf.getvalue()).decode('utf-8')

    return render_template('2fa_setup.html', secret=secret, qr_code=qr_b64)


# =============================================================
# 2FA VERIFY
# =============================================================

@auth_bp.route('/verify-2fa', methods=['GET', 'POST'])
def verify_2fa():
    import pyotp

    user_id  = session.get('pre_2fa_user_id')
    remember = session.get('pre_2fa_remember', False)

    if not user_id:
        flash('Session expired. Please log in again.', 'warning')
        return redirect(url_for('auth.login'))

    user = User.query.get(user_id)
    if not user:
        flash('User not found. Please log in again.', 'danger')
        return redirect(url_for('auth.login'))

    if request.method == 'POST':
        code = request.form.get('code', '').strip()
        ip   = request.remote_addr

        if pyotp.TOTP(user.totp_secret).verify(code):
            session.pop('pre_2fa_user_id', None)
            session.pop('pre_2fa_remember', None)
            login_user(user, remember=remember)
            log_login_attempt(user.id, True, ip)
            flash(f'Welcome back, {user.username}!', 'success')
            return redirect(url_for('admin.dashboard') if user.role == 'teacher'
                            else url_for('game.challenges'))
        else:
            user.login_attempts += 1
            db.session.commit()
            log_login_attempt(user.id, False, ip)
            flash('Invalid code. Please check Google Authenticator and try again.', 'danger')

    return render_template('2fa_verify.html', username=user.username)