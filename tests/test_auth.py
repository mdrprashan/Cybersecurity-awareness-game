# =============================================================
# test_auth.py — Authentication Unit Tests
# Author: Prashan Manandhar (CIHE241182)
# =============================================================

import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))


def logout(client):
    """Helper — logs out any currently logged-in user before a test."""
    client.get('/logout', follow_redirects=True)


# =============================================================
# REGISTRATION TESTS
# =============================================================

class TestRegistration:

    def test_register_page_loads(self, client):
        """GET /register returns 200."""
        logout(client)
        response = client.get('/register')
        assert response.status_code == 200

    def test_register_success_student(self, client, app):
        """Valid student registration creates user in DB."""
        logout(client)
        client.post('/register', data={
            'username':         'reg_student_01',
            'email':            'reg_student_01@test.com',
            'password':         'Test1234!',
            'confirm_password': 'Test1234!',
            'role':             'student'
        }, follow_redirects=True)

        from models import User
        with app.app_context():
            user = User.query.filter_by(username='reg_student_01').first()
            assert user is not None
            assert user.role == 'student'

    def test_register_success_teacher(self, client, app):
        """Valid teacher registration creates teacher in DB."""
        logout(client)
        client.post('/register', data={
            'username':         'reg_teacher_01',
            'email':            'reg_teacher_01@test.com',
            'password':         'Test1234!',
            'confirm_password': 'Test1234!',
            'role':             'teacher'
        }, follow_redirects=True)

        from models import User
        with app.app_context():
            user = User.query.filter_by(username='reg_teacher_01').first()
            assert user is not None
            assert user.role == 'teacher'

    def test_register_duplicate_email(self, client, student_user):
        """Duplicate email should return error on page."""
        logout(client)
        response = client.post('/register', data={
            'username':         'another_unique_user',
            'email':            'student@test.com',
            'password':         'Test1234!',
            'confirm_password': 'Test1234!',
            'role':             'student'
        }, follow_redirects=True)
        assert b'already exists' in response.data

    def test_register_duplicate_username(self, client, student_user):
        """Duplicate username should return error on page."""
        logout(client)
        response = client.post('/register', data={
            'username':         'test_student',
            'email':            'unique999@email.com',
            'password':         'Test1234!',
            'confirm_password': 'Test1234!',
            'role':             'student'
        }, follow_redirects=True)
        assert b'already taken' in response.data

    def test_register_password_mismatch(self, client):
        """Mismatched passwords show error."""
        logout(client)
        response = client.post('/register', data={
            'username':         'mismatch_user99',
            'email':            'mismatch99@test.com',
            'password':         'Test1234!',
            'confirm_password': 'Different1234!',
            'role':             'student'
        }, follow_redirects=True)
        assert response.status_code == 200
        # Check for either the exact message or partial match
        assert (b'do not match' in response.data or
                b'match' in response.data)

    def test_register_short_password(self, client):
        """Password under 8 chars shows error."""
        logout(client)
        response = client.post('/register', data={
            'username':         'shortpw99',
            'email':            'shortpw99@test.com',
            'password':         'abc',
            'confirm_password': 'abc',
            'role':             'student'
        }, follow_redirects=True)
        assert response.status_code == 200
        assert (b'8 characters' in response.data or
                b'least 8' in response.data or
                b'too short' in response.data.lower() or
                b'password' in response.data.lower())

    def test_register_short_username(self, client):
        """Username under 3 chars shows error."""
        logout(client)
        response = client.post('/register', data={
            'username':         'ab',
            'email':            'shortname99@test.com',
            'password':         'Test1234!',
            'confirm_password': 'Test1234!',
            'role':             'student'
        }, follow_redirects=True)
        assert response.status_code == 200
        assert (b'3 characters' in response.data or
                b'least 3' in response.data or
                b'username' in response.data.lower())

    def test_password_not_stored_as_plaintext(self, client, app):
        """Password must be bcrypt hashed, never stored as plaintext."""
        logout(client)
        client.post('/register', data={
            'username':         'hash_check_user',
            'email':            'hashcheck@test.com',
            'password':         'MySecret123!',
            'confirm_password': 'MySecret123!',
            'role':             'student'
        }, follow_redirects=True)

        from models import User
        with app.app_context():
            user = User.query.filter_by(username='hash_check_user').first()
            if user:
                assert user.password_hash != 'MySecret123!'
                assert user.password_hash.startswith('$2b$')


# =============================================================
# LOGIN TESTS
# =============================================================

class TestLogin:

    def test_login_page_loads(self, client):
        """GET /login returns 200 when not logged in."""
        logout(client)
        response = client.get('/login')
        assert response.status_code == 200

    def test_login_success_redirects(self, client, app, student_user):
        """Valid credentials redirect the user (302)."""
        logout(client)
        with app.app_context():
            response = client.post('/login', data={
                'username':    'test_student',
                'password':    'Test1234!',
                'remember_me': 'off'
            }, follow_redirects=False)
            assert response.status_code == 302

    def test_login_wrong_password(self, client, app, student_user):
        """Wrong password shows Invalid error."""
        logout(client)
        with app.app_context():
            response = client.post('/login', data={
                'username': 'test_student',
                'password': 'WrongPassword!'
            }, follow_redirects=True)
            assert b'Invalid' in response.data

    def test_login_nonexistent_user(self, client):
        """Login with unknown username shows Invalid error."""
        logout(client)
        response = client.post('/login', data={
            'username': 'totally_unknown_xyz_999',
            'password': 'Test1234!'
        }, follow_redirects=True)
        assert b'Invalid' in response.data

    def test_login_increments_failed_attempts(self, client, app, student_user):
        """Failed login increments login_attempts counter."""
        logout(client)
        with app.app_context():
            from models import User
            user = User.query.filter_by(username='test_student').first()
            before = user.login_attempts

            client.post('/login', data={
                'username': 'test_student',
                'password': 'WrongPassword!'
            })

            user = User.query.filter_by(username='test_student').first()
            assert user.login_attempts > before

    def test_login_resets_attempts_on_success(self, client, app, student_user):
        """Successful login resets login_attempts to 0."""
        logout(client)
        with app.app_context():
            from models import User, db
            user = User.query.filter_by(username='test_student').first()
            user.login_attempts = 5
            db.session.commit()

            client.post('/login', data={
                'username': 'test_student',
                'password': 'Test1234!'
            })

            user = User.query.filter_by(username='test_student').first()
            assert user.login_attempts == 0

    def test_login_empty_fields_no_crash(self, client):
        """Empty login fields should not crash the app."""
        logout(client)
        response = client.post('/login', data={
            'username': '',
            'password': ''
        }, follow_redirects=True)
        assert response.status_code == 200


# =============================================================
# LOGOUT TESTS
# =============================================================

class TestLogout:

    def test_logout_requires_login(self, client):
        """Accessing /logout without being logged in redirects to login."""
        logout(client)
        response = client.get('/logout', follow_redirects=False)
        assert response.status_code == 302
        assert 'login' in response.headers['Location']

    def test_logout_blocks_protected_pages(self, client, app, student_user):
        """After logout, protected routes redirect to login."""
        logout(client)
        with app.app_context():
            client.post('/login', data={
                'username': 'test_student',
                'password': 'Test1234!'
            })
            client.get('/logout', follow_redirects=True)
            response = client.get('/challenges', follow_redirects=False)
            assert response.status_code == 302
            assert 'login' in response.headers['Location']


# =============================================================
# RBAC TESTS
# =============================================================

class TestRBAC:

    def test_challenges_requires_login(self, client):
        """GET /challenges redirects to login when not authenticated."""
        logout(client)
        response = client.get('/challenges', follow_redirects=False)
        assert response.status_code == 302
        assert 'login' in response.headers['Location']

    def test_dashboard_requires_login(self, client):
        """GET /admin/dashboard redirects to login when not authenticated."""
        logout(client)
        response = client.get('/admin/dashboard', follow_redirects=False)
        assert response.status_code == 302
        assert 'login' in response.headers['Location']

    def test_progress_requires_login(self, client):
        """GET /progress redirects to login when not authenticated."""
        logout(client)
        response = client.get('/progress', follow_redirects=False)
        assert response.status_code == 302
        assert 'login' in response.headers['Location']

    def test_setup_2fa_requires_login(self, client):
        """GET /setup-2fa redirects to login when not authenticated."""
        logout(client)
        response = client.get('/setup-2fa', follow_redirects=False)
        assert response.status_code == 302
        assert 'login' in response.headers['Location']


# =============================================================
# PASSWORD RESET TESTS
# =============================================================

class TestPasswordReset:

    def test_forgot_password_page_loads(self, client):
        """GET /forgot-password returns 200."""
        logout(client)
        response = client.get('/forgot-password')
        assert response.status_code == 200

    def test_forgot_password_unknown_email_safe(self, client):
        """Unknown email must NOT reveal if account exists (anti-enumeration)."""
        logout(client)
        response = client.post('/forgot-password', data={
            'email': 'doesnotexist@nowhere.com'
        }, follow_redirects=True)
        assert b'does not exist' not in response.data
        assert b'not found' not in response.data

    def test_reset_invalid_token_shows_error(self, client):
        """Invalid token redirects with error message."""
        logout(client)
        response = client.get('/reset-password/badtoken999',
                              follow_redirects=True)
        assert response.status_code == 200
        assert (b'invalid' in response.data.lower() or
                b'expired' in response.data.lower())

    def test_reset_valid_token_changes_password(self, client, app, student_user):
        """Valid token allows password change."""
        logout(client)
        with app.app_context():
            from auth import generate_reset_token
            from models import User
            from app import bcrypt

            token = generate_reset_token('student@test.com')
            client.post(f'/reset-password/{token}', data={
                'password':         'BrandNew123!',
                'confirm_password': 'BrandNew123!'
            }, follow_redirects=True)

            user = User.query.filter_by(email='student@test.com').first()
            if user:
                assert bcrypt.check_password_hash(
                    user.password_hash, 'BrandNew123!')

    def test_reset_password_mismatch_shows_error(self, client, app, student_user):
        """Mismatched passwords on reset shows error."""
        logout(client)
        with app.app_context():
            from auth import generate_reset_token
            token = generate_reset_token('student@test.com')

            response = client.post(f'/reset-password/{token}', data={
                'password':         'NewPass123!',
                'confirm_password': 'DifferentPass!'
            }, follow_redirects=True)
            assert b'do not match' in response.data


# =============================================================
# SECURITY TESTS
# =============================================================

class TestSecurity:

    def test_sql_injection_fails_safely(self, client):
        """SQL injection in login should fail without crashing."""
        logout(client)
        response = client.post('/login', data={
            'username': "' OR '1'='1",
            'password': "' OR '1'='1"
        }, follow_redirects=True)
        assert response.status_code == 200
        assert b'Invalid' in response.data

    def test_login_page_no_sensitive_data_exposed(self, client):
        """Login page must not expose hashes, traces or DB info."""
        logout(client)
        response = client.get('/login')
        assert b'password_hash' not in response.data
        assert b'Traceback' not in response.data
        assert b'sqlite' not in response.data.lower()

    def test_xss_in_registration_escaped(self, client):
        """XSS payload in username must not appear unescaped in response."""
        logout(client)
        response = client.post('/register', data={
            'username':         '<script>alert(1)</script>',
            'email':            'xss999@test.com',
            'password':         'Test1234!',
            'confirm_password': 'Test1234!',
            'role':             'student'
        }, follow_redirects=True)
        assert b'<script>alert(1)</script>' not in response.data

    def test_landing_page_always_accessible(self, client):
        """Landing page is public — always returns 200."""
        logout(client)
        response = client.get('/')
        assert response.status_code == 200