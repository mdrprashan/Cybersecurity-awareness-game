"""
test_security.py — Security Unit Tests
CyberQuest ICT932 – Cybersecurity Testing and Assurance
Author: Prashan Manandhar (CIHE241182)

Tests cover:
  - Login attempt logging
  - Brute-force lockout detection
  - Lockout window timing
  - RBAC route protection
  - Audit log access control
  - Security headers presence
"""

import pytest
from datetime import datetime, timedelta
from conftest import login, logout


# ════════════════════════════════════════════════════════════════════
# LOGIN ATTEMPT LOGGING
# ════════════════════════════════════════════════════════════════════

class TestLoginAttemptLogging:

    def test_failed_attempt_is_logged(self, client, app, db):
        """A failed login attempt is recorded in LoginAttempt table."""
        from models import LoginAttempt
        with app.app_context():
            before = LoginAttempt.query.count()
            client.post('/login', data={
                'email':    'log_test@example.com',
                'password': 'wrongpass'
            })
            after = LoginAttempt.query.count()
        assert after > before

    def test_successful_attempt_is_logged(self, client, app, db, student_user):
        """A successful login attempt is recorded with success=True."""
        from models import LoginAttempt
        with app.app_context():
            client.post('/login', data={
                'email':    'pytest_student@test.com',
                'password': 'Test1234!'
            })
            attempt = LoginAttempt.query.filter_by(
                email='pytest_student@test.com',
                success=True
            ).order_by(LoginAttempt.attempted_at.desc()).first()
            assert attempt is not None
            assert attempt.success is True
        logout(client)

    def test_attempt_records_ip_address(self, client, app, db):
        """Login attempts record the requester's IP address."""
        from models import LoginAttempt
        with app.app_context():
            client.post('/login', data={
                'email':    'ip_test@example.com',
                'password': 'wrongpass'
            })
            attempt = LoginAttempt.query.filter_by(
                email='ip_test@example.com'
            ).order_by(LoginAttempt.attempted_at.desc()).first()
        assert attempt is not None
        assert attempt.ip_address is not None

    def test_attempt_has_timestamp(self, app, db):
        """LoginAttempt records a timestamp automatically."""
        from models import LoginAttempt
        from security import log_login_attempt
        with app.app_context():
            log_login_attempt(email='ts_test@example.com', ip='1.2.3.4', success=False)
            attempt = LoginAttempt.query.filter_by(email='ts_test@example.com').first()
            assert attempt is not None
            assert isinstance(attempt.attempted_at, datetime)


# ════════════════════════════════════════════════════════════════════
# BRUTE-FORCE LOCKOUT
# ════════════════════════════════════════════════════════════════════

class TestBruteForceProtection:

    def test_not_locked_below_threshold(self, app, db):
        """Account is NOT locked below MAX_LOGIN_ATTEMPTS failures."""
        from security import log_login_attempt, is_account_locked
        from models import LoginAttempt
        email = 'notlocked@test.com'
        with app.app_context():
            # Clean slate
            LoginAttempt.query.filter_by(email=email).delete()
            db.session.commit()
            for _ in range(4):  # threshold is 5
                log_login_attempt(email=email, ip='9.9.9.9', success=False)
            assert is_account_locked(email) is False

    def test_locked_at_threshold(self, app, db):
        """Account IS locked once MAX_LOGIN_ATTEMPTS is reached."""
        from security import log_login_attempt, is_account_locked
        from models import LoginAttempt
        email = 'locked_at5@test.com'
        with app.app_context():
            LoginAttempt.query.filter_by(email=email).delete()
            db.session.commit()
            for _ in range(5):
                log_login_attempt(email=email, ip='9.9.9.9', success=False)
            assert is_account_locked(email) is True

    def test_locked_above_threshold(self, app, db):
        """Account stays locked above the threshold."""
        from security import log_login_attempt, is_account_locked
        from models import LoginAttempt
        email = 'locked_above@test.com'
        with app.app_context():
            LoginAttempt.query.filter_by(email=email).delete()
            db.session.commit()
            for _ in range(8):
                log_login_attempt(email=email, ip='9.9.9.9', success=False)
            assert is_account_locked(email) is True

    def test_success_not_counted_in_lockout(self, app, db):
        """Successful attempts are not counted toward lockout."""
        from security import log_login_attempt, is_account_locked
        from models import LoginAttempt
        email = 'success_mixed@test.com'
        with app.app_context():
            LoginAttempt.query.filter_by(email=email).delete()
            db.session.commit()
            for _ in range(3):
                log_login_attempt(email=email, ip='1.1.1.1', success=False)
            log_login_attempt(email=email, ip='1.1.1.1', success=True)
            # Only 3 failures — should NOT be locked
            assert is_account_locked(email) is False

    def test_old_attempts_outside_window_ignored(self, app, db):
        """Attempts older than LOCKOUT_MINUTES window don't count."""
        from security import is_account_locked
        from models import LoginAttempt
        email = 'oldattempts@test.com'
        with app.app_context():
            LoginAttempt.query.filter_by(email=email).delete()
            db.session.commit()
            # Insert 5 attempts timestamped 20 minutes ago (outside 15-min window)
            old_time = datetime.utcnow() - timedelta(minutes=20)
            for _ in range(5):
                attempt = LoginAttempt(
                    email=email, ip_address='2.2.2.2',
                    success=False, attempted_at=old_time
                )
                db.session.add(attempt)
            db.session.commit()
            assert is_account_locked(email) is False

    def test_unknown_email_not_locked(self, app, db):
        """An email with zero attempts is never locked."""
        from security import is_account_locked
        with app.app_context():
            assert is_account_locked('neverbefore@test.com') is False

    def test_lockout_message_shown_on_login(self, client, app, db):
        """Locked account shows lockout flash message on login attempt."""
        from security import log_login_attempt
        from models import LoginAttempt
        email = 'showlockout@test.com'
        with app.app_context():
            LoginAttempt.query.filter_by(email=email).delete()
            db.session.commit()
            for _ in range(5):
                log_login_attempt(email=email, ip='3.3.3.3', success=False)

        response = client.post('/login', data={
            'email': email, 'password': 'anything'
        }, follow_redirects=True)
        assert b'locked' in response.data.lower()


# ════════════════════════════════════════════════════════════════════
# RBAC — ROUTE PROTECTION
# ════════════════════════════════════════════════════════════════════

class TestRBAC:

    def test_unauthenticated_cannot_access_challenges(self, client):
        """Unauthenticated users are redirected away from /challenges."""
        response = client.get('/challenges', follow_redirects=False)
        assert response.status_code in (302, 308)

    def test_unauthenticated_cannot_access_admin(self, client):
        """Unauthenticated users cannot access /admin/."""
        response = client.get('/admin/', follow_redirects=False)
        assert response.status_code in (302, 308)

    def test_unauthenticated_cannot_access_audit_log(self, client):
        """Unauthenticated users cannot access /security/audit-log."""
        response = client.get('/security/audit-log', follow_redirects=False)
        assert response.status_code in (302, 308)

    def test_unauthenticated_cannot_access_progress(self, client):
        """Unauthenticated users cannot access /progress."""
        response = client.get('/progress', follow_redirects=False)
        assert response.status_code in (302, 308)

    def test_student_role_assigned_correctly(self, app, student_user):
        """Student user has role='student'."""
        with app.app_context():
            from models import User
            user = User.query.filter_by(email='pytest_student@test.com').first()
            assert user.role == 'student'
            assert user.is_teacher is False

    def test_teacher_role_assigned_correctly(self, app, teacher_user):
        """Teacher user has role='teacher'."""
        with app.app_context():
            from models import User
            user = User.query.filter_by(email='pytest_teacher@test.com').first()
            assert user.role == 'teacher'
            assert user.is_teacher is True


# ════════════════════════════════════════════════════════════════════
# HTTP SECURITY HEADERS
# ════════════════════════════════════════════════════════════════════

class TestSecurityHeaders:

    def test_x_frame_options_present(self, client):
        """Response includes X-Frame-Options: DENY header."""
        response = client.get('/login')
        assert 'X-Frame-Options' in response.headers
        assert response.headers['X-Frame-Options'] == 'DENY'

    def test_x_content_type_options_present(self, client):
        """Response includes X-Content-Type-Options: nosniff header."""
        response = client.get('/login')
        assert 'X-Content-Type-Options' in response.headers
        assert response.headers['X-Content-Type-Options'] == 'nosniff'

    def test_referrer_policy_present(self, client):
        """Response includes Referrer-Policy header."""
        response = client.get('/login')
        assert 'Referrer-Policy' in response.headers

    def test_content_security_policy_present(self, client):
        """Response includes Content-Security-Policy header."""
        response = client.get('/login')
        assert 'Content-Security-Policy' in response.headers

    def test_server_header_removed(self, client):
        """Server fingerprint header is removed from responses."""
        response = client.get('/login')
        assert 'Server' not in response.headers or \
               response.headers.get('Server', '') == ''


# ════════════════════════════════════════════════════════════════════
# ROLE_REQUIRED DECORATOR
# ════════════════════════════════════════════════════════════════════

class TestRoleRequiredDecorator:

    def test_role_required_function_exists(self, app):
        """role_required decorator is importable from security module."""
        with app.app_context():
            from security import role_required
            assert callable(role_required)

    def test_is_account_locked_function_exists(self, app):
        """is_account_locked is importable and callable."""
        with app.app_context():
            from security import is_account_locked
            assert callable(is_account_locked)

    def test_log_login_attempt_function_exists(self, app):
        """log_login_attempt is importable and callable."""
        with app.app_context():
            from security import log_login_attempt
            assert callable(log_login_attempt)
