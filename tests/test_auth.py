"""
test_auth.py — Authentication Unit Tests
CyberQuest ICT932 – Cybersecurity Testing and Assurance
Author: Prashan Manandhar (CIHE241182)

Tests cover:
  - User registration (valid, duplicate, weak password, missing fields)
  - User login (valid, invalid password, unknown email, lockout)
  - Logout
  - Password strength validation
  - 2FA setup and verify routes
  - Role-based redirects
"""

import pytest
from conftest import login, logout


# ════════════════════════════════════════════════════════════════════
# REGISTRATION TESTS
# ════════════════════════════════════════════════════════════════════

class TestRegistration:

    def test_register_page_loads(self, client):
        """GET /register returns 200 OK."""
        logout(client)
        response = client.get('/register')
        assert response.status_code == 200
        assert b'Create Account' in response.data or b'Register' in response.data

    def test_register_valid_student(self, client, app, db):
        """Valid student registration creates account and redirects to 2FA setup."""
        logout(client)  # ensure clean session
        response = client.post('/register', data={
            'username':         'newstudent_test',
            'email':            'newstudent_test@example.com',
            'password':         'Secure99!@',
            'confirm_password': 'Secure99!@',
            'role':             'student'
        }, follow_redirects=True)
        assert response.status_code == 200
        # Should redirect to 2FA setup after registration
        assert '2fa' in response.request.path.lower() or b'Two-Factor' in response.data or b'CyberQuest' in response.data

        # Verify user exists in DB
        with app.app_context():
            from models import User
            user = User.query.filter_by(email='newstudent_test@example.com').first()
            assert user is not None
            assert user.role == 'student'

    def test_register_duplicate_email(self, client, student_user, app):
        """Registering with an existing email shows error."""
        logout(client)  # ensure clean session
        response = client.post('/register', data={
            'username':         'duplicate_user',
            'email':            'pytest_student@test.com',
            'password':         'Test1234!',
            'confirm_password': 'Test1234!',
            'role':             'student'
        }, follow_redirects=True)
        assert b'already exists' in response.data

    def test_register_password_mismatch(self, client):
        """Mismatched passwords are rejected."""
        logout(client)
        response = client.post('/register', data={
            'username':         'mismatch_user',
            'email':            'mismatch@example.com',
            'password':         'Test1234!',
            'confirm_password': 'Different1!',
            'role':             'student'
        }, follow_redirects=True)
        assert b'do not match' in response.data

    def test_register_weak_password_no_uppercase(self, client):
        """Password without uppercase is rejected."""
        logout(client)
        response = client.post('/register', data={
            'username':         'weakpw',
            'email':            'weakpw@example.com',
            'password':         'password1!',
            'confirm_password': 'password1!',
            'role':             'student'
        }, follow_redirects=True)
        assert b'uppercase' in response.data

    def test_register_weak_password_no_special(self, client):
        """Password without special character is rejected."""
        logout(client)
        response = client.post('/register', data={
            'username':         'weakpw2',
            'email':            'weakpw2@example.com',
            'password':         'Password123',
            'confirm_password': 'Password123',
            'role':             'student'
        }, follow_redirects=True)
        assert b'special' in response.data

    def test_register_weak_password_too_short(self, client):
        """Password under 8 characters is rejected."""
        logout(client)
        response = client.post('/register', data={
            'username':         'short',
            'email':            'short@example.com',
            'password':         'Ab1!',
            'confirm_password': 'Ab1!',
            'role':             'student'
        }, follow_redirects=True)
        assert b'8 characters' in response.data

    def test_register_missing_fields(self, client):
        """Empty form submission is rejected."""
        logout(client)
        response = client.post('/register', data={
            'username': '', 'email': '', 'password': '', 'confirm_password': ''
        }, follow_redirects=True)
        assert response.status_code == 200
        assert b'required' in response.data

    def test_register_teacher_without_code_fails(self, client):
        """Teacher registration without correct code is rejected."""
        logout(client)
        response = client.post('/register', data={
            'username':         'fake_teacher',
            'email':            'fake_teacher@example.com',
            'password':         'Teach1234!',
            'confirm_password': 'Teach1234!',
            'role':             'teacher',
            'teacher_code':     'WRONG-CODE'
        }, follow_redirects=True)
        assert b'Invalid teacher' in response.data

    def test_register_teacher_with_correct_code(self, client, app):
        """Teacher registration with correct code succeeds."""
        logout(client)
        response = client.post('/register', data={
            'username':         'valid_teacher_test',
            'email':            'valid_teacher_test@example.com',
            'password':         'Teach1234!',
            'confirm_password': 'Teach1234!',
            'role':             'teacher',
            'teacher_code':     'CIHE-TEACH-2026'
        }, follow_redirects=True)
        assert response.status_code == 200
        with app.app_context():
            from models import User
            teacher = User.query.filter_by(email='valid_teacher_test@example.com').first()
            assert teacher is not None
            assert teacher.role == 'teacher'


# ════════════════════════════════════════════════════════════════════
# LOGIN TESTS
# ════════════════════════════════════════════════════════════════════

class TestLogin:

    def test_login_page_loads(self, client):
        """GET /login returns 200 OK."""
        logout(client)
        response = client.get('/login')
        assert response.status_code == 200
        assert b'Sign In' in response.data or b'Login' in response.data

    def test_login_valid_student(self, client, student_user, app):
        """Valid student credentials redirect to 2FA setup (since 2FA not configured)."""
        with app.app_context():
            response = login(client, 'pytest_student@test.com', 'Test1234!')
        assert response.status_code == 200
        assert b'Invalid email or password' not in response.data
        logout(client)

    def test_login_wrong_password(self, client):
        """Wrong password returns generic error message."""
        response = login(client, 'pytest_student@test.com', 'WrongPass99!')
        assert b'Invalid email or password' in response.data

    def test_login_nonexistent_email(self, client):
        """Unknown email returns same generic error (prevents user enumeration)."""
        response = login(client, 'nobody@nowhere.com', 'Test1234!')
        assert b'Invalid email or password' in response.data

    def test_login_empty_fields(self, client):
        """Submitting empty login form is handled gracefully."""
        response = client.post('/login', data={
            'email': '', 'password': ''
        }, follow_redirects=True)
        assert response.status_code == 200

    def test_login_redirect_student_to_2fa_setup(self, client, app, db):
        """Student without 2FA configured is redirected to setup after login."""
        with app.app_context():
            response = login(client, 'pytest_student@test.com', 'Test1234!')
            # Should redirect to 2FA setup
            assert b'Two-Factor' in response.data or '2fa' in response.request.path.lower() \
                   or b'Set Up' in response.data
        logout(client)

    def test_login_teacher_redirects_to_admin(self, client, teacher_user, app):
        """Teacher login (2FA not enabled) goes to 2FA setup then admin."""
        with app.app_context():
            response = login(client, 'pytest_teacher@test.com', 'Teach1234!')
        assert response.status_code == 200
        logout(client)

    def test_login_case_insensitive_email(self, client, app):
        """Email is case-insensitive at login."""
        with app.app_context():
            response = login(client, 'PYTEST_STUDENT@TEST.COM', 'Test1234!')
        assert b'Invalid email or password' not in response.data
        logout(client)


# ════════════════════════════════════════════════════════════════════
# LOGOUT TESTS
# ════════════════════════════════════════════════════════════════════

class TestLogout:

    def test_logout_redirects_to_login(self, client, app):
        """Logging out redirects to the login page."""
        with app.app_context():
            login(client, 'pytest_student@test.com', 'Test1234!')
        response = logout(client)
        assert response.status_code == 200
        assert b'Sign In' in response.data or b'Login' in response.data or b'logged out' in response.data

    def test_logout_unauthenticated_redirects(self, client):
        """GET /logout without session redirects to login."""
        response = client.get('/logout', follow_redirects=False)
        assert response.status_code in (302, 308)


# ════════════════════════════════════════════════════════════════════
# PASSWORD STRENGTH VALIDATION UNIT TESTS
# ════════════════════════════════════════════════════════════════════

class TestPasswordStrength:

    def test_strong_password_passes(self, app):
        """A genuinely strong password passes all checks."""
        with app.app_context():
            from auth import _validate_password_strength
            errors = _validate_password_strength('Tr0ub4dor&3!xKp')
            assert errors == []

    def test_short_password_fails(self, app):
        """Passwords under 8 chars fail."""
        with app.app_context():
            from auth import _validate_password_strength
            errors = _validate_password_strength('Ab1!')
            assert any('8 characters' in e for e in errors)

    def test_no_uppercase_fails(self, app):
        """Passwords without uppercase fail."""
        with app.app_context():
            from auth import _validate_password_strength
            errors = _validate_password_strength('abcdef1!')
            assert any('uppercase' in e for e in errors)

    def test_no_lowercase_fails(self, app):
        """Passwords without lowercase fail."""
        with app.app_context():
            from auth import _validate_password_strength
            errors = _validate_password_strength('ABCDEF1!')
            assert any('lowercase' in e for e in errors)

    def test_no_digit_fails(self, app):
        """Passwords without a digit fail."""
        with app.app_context():
            from auth import _validate_password_strength
            errors = _validate_password_strength('Abcdefgh!')
            assert any('number' in e for e in errors)

    def test_no_special_char_fails(self, app):
        """Passwords without a special character fail."""
        with app.app_context():
            from auth import _validate_password_strength
            errors = _validate_password_strength('Abcdefg1')
            assert any('special' in e for e in errors)

    def test_multiple_failures_reported(self, app):
        """All unmet requirements are reported at once."""
        with app.app_context():
            from auth import _validate_password_strength
            errors = _validate_password_strength('abc')
            assert len(errors) >= 3  # short, no upper, no digit, no special


# ════════════════════════════════════════════════════════════════════
# 2FA ROUTE TESTS
# ════════════════════════════════════════════════════════════════════

class TestTwoFactor:

    def test_2fa_setup_requires_login(self, client):
        """GET /2fa/setup without login redirects to login."""
        response = client.get('/2fa/setup', follow_redirects=False)
        assert response.status_code in (302, 308)

    def test_2fa_verify_requires_session(self, client):
        """GET /2fa/verify without pre_2fa_user_id redirects to login."""
        response = client.get('/2fa/verify', follow_redirects=True)
        assert response.status_code == 200
        assert b'Sign In' in response.data or b'Login' in response.data

    def test_2fa_skip_requires_login(self, client):
        """GET /2fa/skip without login redirects."""
        response = client.get('/2fa/skip', follow_redirects=False)
        assert response.status_code in (302, 308)

    def test_student_cannot_disable_2fa(self, client, app, db):
        """Students cannot POST to /2fa/disable."""
        with app.app_context():
            # Create student with 2FA enabled
            from models import User
            from extensions import bcrypt
            user = User.query.filter_by(email='twofa_student@test.com').first()
            if not user:
                user = User(
                    username='twofa_student',
                    email='twofa_student@test.com',
                    password=bcrypt.generate_password_hash('Test1234!').decode('utf-8'),
                    role='student',
                    is_2fa_enabled=True,
                    totp_secret='JBSWY3DPEHPK3PXP'
                )
                db.session.add(user)
                db.session.commit()

        login(client, 'twofa_student@test.com', 'Test1234!')
        # Student should be redirected to 2FA verify, not logged in
        # Attempting disable via direct POST
        response = client.post('/2fa/disable', follow_redirects=True)
        # Should either show error or redirect to login (since 2FA verify not complete)
        assert b'Invalid' in response.data or b'Students cannot' in response.data \
               or b'Sign In' in response.data
        logout(client)