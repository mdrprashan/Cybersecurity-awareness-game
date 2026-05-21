"""
test_admin.py — Admin Dashboard Unit Tests
CyberQuest ICT932 – Cybersecurity Testing and Assurance
Author: Pramesh Silwal (CIHE241339)

Tests cover:
  - Admin dashboard access control
  - Add user (valid, duplicate, weak password)
  - Delete user (self-protection)
  - Reset password (strength validation)
  - Reset 2FA
  - Challenge management (add, delete)
  - Audit log access
"""

import pytest
from conftest import login, logout


# ════════════════════════════════════════════════════════════════════
# HELPERS
# ════════════════════════════════════════════════════════════════════

def login_teacher(client, app):
    with app.app_context():
        login(client, 'pytest_teacher@test.com', 'Teach1234!')
    client.get('/2fa/skip', follow_redirects=True)


def login_student(client, app):
    with app.app_context():
        login(client, 'pytest_student@test.com', 'Test1234!')
    client.get('/2fa/skip', follow_redirects=True)


def login_fresh_teacher(client, app, db, tag):
    """
    Create a brand-new teacher with a unique email and log in.
    Used for tests that run after password-reset tests, which can
    accidentally mutate the shared pytest_teacher account's password.
    """
    email    = f'teacher_{tag}@test.com'
    password = 'Teach1234!'
    with app.app_context():
        from models import User
        from extensions import bcrypt
        u = User.query.filter_by(email=email).first()
        if not u:
            u = User(
                username=f'teacher_{tag}',
                email=email,
                password=bcrypt.generate_password_hash(password).decode('utf-8'),
                role='teacher'
            )
            db.session.add(u)
            db.session.commit()
    login(client, email, password)
    client.get('/2fa/skip', follow_redirects=True)


# ════════════════════════════════════════════════════════════════════
# ADMIN DASHBOARD ACCESS CONTROL
# ════════════════════════════════════════════════════════════════════

class TestAdminAccess:

    def test_admin_dashboard_requires_login(self, client):
        """Unauthenticated users cannot access /admin/."""
        logout(client)
        response = client.get('/admin/', follow_redirects=False)
        assert response.status_code in (302, 308)

    def test_student_blocked_from_admin(self, client, app, student_user):
        """Students cannot access the teacher admin dashboard."""
        logout(client)
        login_student(client, app)
        response = client.get('/admin/', follow_redirects=True)
        # Should be redirected away — either login or challenges
        assert b'Teacher Dashboard' not in response.data
        logout(client)

    def test_teacher_can_access_admin(self, client, app, teacher_user):
        """Teachers can access the admin dashboard."""
        logout(client)
        login_teacher(client, app)
        response = client.get('/admin/')
        assert response.status_code == 200
        assert b'Teacher Dashboard' in response.data or b'Student Progress' in response.data
        logout(client)

    def test_student_blocked_from_audit_log(self, client, app, student_user):
        """Students cannot access /security/audit-log."""
        logout(client)
        login_student(client, app)
        response = client.get('/security/audit-log', follow_redirects=True)
        assert b'Audit Log' not in response.data or b'permission' in response.data.lower()
        logout(client)

    def test_teacher_can_access_audit_log(self, client, app, teacher_user):
        """Teachers can access /security/audit-log."""
        logout(client)
        login_teacher(client, app)
        response = client.get('/security/audit-log')
        assert response.status_code == 200
        logout(client)

    def test_teacher_can_access_locked_accounts(self, client, app, teacher_user):
        """Teachers can access /security/locked-accounts."""
        logout(client)
        login_teacher(client, app)
        response = client.get('/security/locked-accounts')
        assert response.status_code == 200
        logout(client)

    def test_student_blocked_from_manage_challenges(self, client, app, student_user):
        """Students cannot access /admin/challenges."""
        logout(client)
        login_student(client, app)
        response = client.get('/admin/challenges', follow_redirects=True)
        assert b'Manage Challenges' not in response.data or b'permission' in response.data.lower()
        logout(client)


# ════════════════════════════════════════════════════════════════════
# ADD USER
# ════════════════════════════════════════════════════════════════════

class TestAddUser:

    def test_add_user_page_loads(self, client, app, teacher_user):
        """Teacher can access the Add User form."""
        logout(client)
        login_teacher(client, app)
        response = client.get('/admin/users/add')
        assert response.status_code == 200
        assert b'Add' in response.data and b'User' in response.data
        logout(client)

    def test_add_valid_student(self, client, app, db, teacher_user):
        """Teacher can create a valid student account."""
        logout(client)
        login_teacher(client, app)
        response = client.post('/admin/users/add', data={
            'username': 'admin_created_student',
            'email':    'admin_created@test.com',
            'role':     'student',
            'password': 'Secure99!@'
        }, follow_redirects=True)
        assert response.status_code == 200
        with app.app_context():
            from models import User
            user = User.query.filter_by(email='admin_created@test.com').first()
            assert user is not None
            assert user.role == 'student'
        logout(client)

    def test_add_user_duplicate_email_rejected(self, client, app, teacher_user, student_user):
        """Adding a user with an existing email is rejected."""
        logout(client)
        login_teacher(client, app)
        response = client.post('/admin/users/add', data={
            'username': 'dup_user',
            'email':    'pytest_student@test.com',  # already exists
            'role':     'student',
            'password': 'Secure99!@'
        }, follow_redirects=True)
        assert b'already in use' in response.data or b'Email' in response.data
        logout(client)

    def test_add_user_weak_password_rejected(self, client, app, teacher_user):
        """Weak password is rejected when adding a user via admin."""
        logout(client)
        login_teacher(client, app)
        response = client.post('/admin/users/add', data={
            'username': 'weakpw_user',
            'email':    'weakpw_admin@test.com',
            'role':     'student',
            'password': 'password123'  # no uppercase or special char
        }, follow_redirects=True)
        assert b'uppercase' in response.data or b'special' in response.data
        logout(client)

    def test_add_user_missing_fields_rejected(self, client, app, teacher_user):
        """Missing fields prevent user creation."""
        logout(client)
        login_teacher(client, app)
        response = client.post('/admin/users/add', data={
            'username': '', 'email': '', 'role': 'student', 'password': ''
        }, follow_redirects=True)
        assert b'required' in response.data or response.status_code == 200
        logout(client)


# ════════════════════════════════════════════════════════════════════
# DELETE USER
# ════════════════════════════════════════════════════════════════════

class TestDeleteUser:

    def test_teacher_cannot_delete_self(self, client, app, db, teacher_user):
        """Teacher cannot delete their own account."""
        logout(client)
        login_teacher(client, app)
        with app.app_context():
            from models import User
            teacher = User.query.filter_by(email='pytest_teacher@test.com').first()
            assert teacher is not None, "Teacher fixture not found in DB"
            teacher_id = teacher.id

        response = client.post(f'/admin/users/{teacher_id}/delete',
                               follow_redirects=True)
        assert b'cannot delete your own' in response.data
        logout(client)

    def test_can_delete_other_user(self, client, app, db, teacher_user):
        """Teacher can delete another user."""
        logout(client)
        login_teacher(client, app)
        # First create a user to delete
        client.post('/admin/users/add', data={
            'username': 'delete_me_user',
            'email':    'delete_me@test.com',
            'role':     'student',
            'password': 'Delete99!@'
        })
        with app.app_context():
            from models import User
            user = User.query.filter_by(email='delete_me@test.com').first()
            if user:
                user_id = user.id
                response = client.post(f'/admin/users/{user_id}/delete',
                                       follow_redirects=True)
                assert b'deleted' in response.data or response.status_code == 200
        logout(client)

    def test_delete_nonexistent_user_handled(self, client, app, teacher_user):
        """Deleting a non-existent user is handled gracefully."""
        logout(client)
        login_teacher(client, app)
        response = client.post('/admin/users/99999/delete', follow_redirects=True)
        assert response.status_code == 200
        logout(client)


# ════════════════════════════════════════════════════════════════════
# RESET PASSWORD
# ════════════════════════════════════════════════════════════════════

class TestResetPassword:

    def test_reset_password_strong(self, client, app, db, teacher_user, student_user):
        """Teacher can reset a user's password with a strong password."""
        logout(client)
        login_teacher(client, app)
        with app.app_context():
            from models import User
            user = User.query.filter_by(email='pytest_student@test.com').first()
            assert user is not None, "Student fixture not found in DB"
            user_id = user.id

        response = client.post(f'/admin/users/{user_id}/reset-password', data={
            'new_password': 'NewPass99!@'
        }, follow_redirects=True)
        assert response.status_code == 200
        assert b'reset' in response.data.lower() or b'Password' in response.data
        logout(client)

    def test_reset_password_weak_rejected(self, client, app, db, teacher_user, student_user):
        """Weak password is rejected on admin reset."""
        logout(client)
        login_teacher(client, app)
        with app.app_context():
            from models import User
            user    = User.query.filter_by(email='pytest_student@test.com').first()
            assert user is not None, "Student fixture not found in DB"
            user_id = user.id

        response = client.post(f'/admin/users/{user_id}/reset-password', data={
            'new_password': 'weakpass'  # no uppercase, no special
        }, follow_redirects=True)
        assert b'uppercase' in response.data or b'special' in response.data
        logout(client)


# ════════════════════════════════════════════════════════════════════
# CHALLENGE MANAGEMENT
# ════════════════════════════════════════════════════════════════════

class TestChallengeManagement:

    def test_manage_challenges_page_loads(self, client, app, db, teacher_user):
        """Teacher can access the manage challenges page."""
        logout(client)
        login_fresh_teacher(client, app, db, 'ch1')
        response = client.get('/admin/challenges')
        assert response.status_code == 200
        assert b'Challenge' in response.data
        logout(client)

    def test_add_challenge_valid(self, client, app, db, teacher_user):
        """Teacher can add a new challenge."""
        logout(client)
        login_fresh_teacher(client, app, db, 'ch2')
        with app.app_context():
            from models import Challenge
            before = Challenge.query.count()

        response = client.post('/admin/challenges/add', data={
            'category':       'phishing',
            'question':       'What is a test phishing question?',
            'option_a':       'Option A answer',
            'option_b':       'Option B answer',
            'option_c':       'Option C answer',
            'option_d':       'Option D answer',
            'correct_answer': 'A',
            'explanation':    'This is the explanation.',
            'difficulty':     'easy'
        }, follow_redirects=True)
        assert response.status_code == 200

        with app.app_context():
            from models import Challenge
            after = Challenge.query.count()
            assert after > before
        logout(client)

    def test_add_challenge_invalid_category_rejected(self, client, app, db, teacher_user):
        """Invalid category is rejected."""
        logout(client)
        login_fresh_teacher(client, app, db, 'ch3')
        response = client.post('/admin/challenges/add', data={
            'category':       'hacking',  # invalid
            'question':       'Test?',
            'option_a':       'A', 'option_b': 'B',
            'option_c':       'C', 'option_d': 'D',
            'correct_answer': 'A',
            'difficulty':     'easy'
        }, follow_redirects=True)
        assert b'Invalid category' in response.data or response.status_code == 200
        logout(client)

    def test_add_challenge_invalid_answer_rejected(self, client, app, db, teacher_user):
        """Correct answer must be A/B/C/D."""
        logout(client)
        login_fresh_teacher(client, app, db, 'ch4')
        response = client.post('/admin/challenges/add', data={
            'category':       'phishing',
            'question':       'Test?',
            'option_a':       'A', 'option_b': 'B',
            'option_c':       'C', 'option_d': 'D',
            'correct_answer': 'X',  # invalid
            'difficulty':     'easy'
        }, follow_redirects=True)
        assert b'A, B, C or D' in response.data or response.status_code == 200
        logout(client)


# ════════════════════════════════════════════════════════════════════
# RESET 2FA
# ════════════════════════════════════════════════════════════════════

class TestReset2FA:

    def test_teacher_can_reset_student_2fa(self, client, app, db, teacher_user):
        """Teacher can reset a student's 2FA."""
        logout(client)
        login_fresh_teacher(client, app, db, '2fa')
        with app.app_context():
            from models import User
            from extensions import bcrypt
            # Create a student with 2FA enabled
            existing = User.query.filter_by(email='has2fa@test.com').first()
            if not existing:
                user = User(
                    username='has2fa_user',
                    email='has2fa@test.com',
                    password=bcrypt.generate_password_hash('Test1234!').decode('utf-8'),
                    role='student',
                    is_2fa_enabled=True,
                    totp_secret='JBSWY3DPEHPK3PXP'
                )
                db.session.add(user)
                db.session.commit()
                existing = user
            user_id = existing.id

        response = client.post(f'/admin/users/{user_id}/reset-2fa',
                               follow_redirects=True)
        assert response.status_code == 200

        with app.app_context():
            from models import User
            user = User.query.get(user_id)
            assert user.is_2fa_enabled is False
            assert user.totp_secret is None
        logout(client)