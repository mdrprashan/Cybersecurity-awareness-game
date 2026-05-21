"""
locustfile.py — Load & Performance Testing
CyberQuest ICT932 – Cybersecurity Testing and Assurance

Tests simulate realistic user behaviour:
  - StudentUser: Login → browse challenges → answer questions → view progress
  - TeacherUser: Login → view admin dashboard → check audit log

Run with:
  locust -f locustfile.py --host=http://127.0.0.1:5000

Then open: http://localhost:8089
  - Number of users: 20
  - Spawn rate:      5 per second
  - Run time:        60 seconds
"""

import random
from locust import HttpUser, task, between, events


# ════════════════════════════════════════════════════════════════════
# STUDENT USER BEHAVIOUR
# ════════════════════════════════════════════════════════════════════

class StudentUser(HttpUser):
    """
    Simulates a student:
      1. Login → bypass 2FA setup
      2. Browse challenge categories
      3. Try answering questions
      4. View progress and results
      5. Logout
    """
    weight       = 4          # 80% of virtual users are students
    wait_time    = between(1, 3)  # realistic think time between requests

    CATEGORIES   = ['phishing', 'password', 'browsing']
    CREDENTIALS  = [
        {'email': 'student@demo.com',       'password': 'Test1234!'},
        {'email': 'pytest_student@test.com', 'password': 'Test1234!'},
    ]

    def on_start(self):
        """Log in at the start of each simulated user session."""
        creds = random.choice(self.CREDENTIALS)
        response = self.client.post('/login', data={
            'email':    creds['email'],
            'password': creds['password']
        }, allow_redirects=True)

        # Skip 2FA setup if redirected there
        if '/2fa' in response.url:
            self.client.get('/2fa/skip', allow_redirects=True)

    def on_stop(self):
        """Log out at end of session."""
        self.client.get('/logout')

    @task(3)
    def view_challenges_home(self):
        """Browse the challenges home page."""
        self.client.get('/challenges', name='/challenges')

    @task(3)
    def view_challenge_category(self):
        """Browse a random challenge category."""
        category = random.choice(self.CATEGORIES)
        self.client.get(f'/challenge/{category}', name='/challenge/[category]')

    @task(2)
    def view_progress(self):
        """View the progress page."""
        self.client.get('/progress', name='/progress')

    @task(1)
    def view_results(self):
        """View the results/summary page."""
        self.client.get('/result', name='/result')

    @task(2)
    def submit_answer(self):
        """Submit an answer to a random challenge (IDs 1–15)."""
        challenge_id = random.randint(1, 15)
        answer       = random.choice(['A', 'B', 'C', 'D'])
        self.client.post(
            f'/answer/{challenge_id}',
            data={'answer': answer},
            allow_redirects=True,
            name='/answer/[id]'
        )


# ════════════════════════════════════════════════════════════════════
# TEACHER USER BEHAVIOUR
# ════════════════════════════════════════════════════════════════════

class TeacherUser(HttpUser):
    """
    Simulates a teacher/admin:
      1. Login → bypass 2FA setup
      2. View admin dashboard
      3. Check audit log and locked accounts
      4. Manage challenges
      5. Logout
    """
    weight    = 1          # 20% of virtual users are teachers
    wait_time = between(2, 5)

    def on_start(self):
        response = self.client.post('/login', data={
            'email':    'teacher@demo.com',
            'password': 'Admin1234!'
        }, allow_redirects=True)
        if '/2fa' in response.url:
            self.client.get('/2fa/skip', allow_redirects=True)

    def on_stop(self):
        self.client.get('/logout')

    @task(4)
    def view_admin_dashboard(self):
        """Load the admin dashboard (heaviest DB query)."""
        self.client.get('/admin/', name='/admin/')

    @task(2)
    def view_audit_log(self):
        """Check the security audit log."""
        self.client.get('/security/audit-log', name='/security/audit-log')

    @task(1)
    def view_locked_accounts(self):
        """Check for locked accounts."""
        self.client.get('/security/locked-accounts', name='/security/locked-accounts')

    @task(1)
    def view_manage_challenges(self):
        """Browse the challenge management page."""
        self.client.get('/admin/challenges', name='/admin/challenges')


# ════════════════════════════════════════════════════════════════════
# UNAUTHENTICATED USER (tests public pages only)
# ════════════════════════════════════════════════════════════════════

class UnauthenticatedUser(HttpUser):
    """
    Simulates a visitor browsing public pages (login, register).
    Tests that unauthenticated requests are handled fast.
    """
    weight    = 1
    wait_time = between(1, 2)

    @task(3)
    def view_login_page(self):
        """Load the login page."""
        self.client.get('/login', name='/login')

    @task(1)
    def view_register_page(self):
        """Load the register page."""
        self.client.get('/register', name='/register')

    @task(1)
    def attempt_protected_page(self):
        """
        Try to access a protected route — should get a fast redirect (not error).
        Tests that auth middleware responds quickly.
        """
        with self.client.get('/challenges', allow_redirects=False,
                             catch_response=True, name='/challenges [unauth]') as r:
            if r.status_code in (302, 308):
                r.success()   # correct behaviour — fast redirect
            else:
                r.failure(f'Expected redirect, got {r.status_code}')


# ════════════════════════════════════════════════════════════════════
# EVENTS — print summary stats
# ════════════════════════════════════════════════════════════════════

@events.quitting.add_listener
def on_quitting(environment, **kwargs):
    """Print a summary when the load test ends."""
    stats = environment.stats.total
    print("\n" + "="*60)
    print("  CYBERQUEST LOAD TEST SUMMARY")
    print("="*60)
    print(f"  Total Requests  : {stats.num_requests}")
    print(f"  Failures        : {stats.num_failures}")
    print(f"  Avg Response    : {stats.avg_response_time:.0f} ms")
    print(f"  Min Response    : {stats.min_response_time:.0f} ms")
    print(f"  Max Response    : {stats.max_response_time:.0f} ms")
    print(f"  95th Percentile : {stats.get_response_time_percentile(0.95):.0f} ms")
    print(f"  Requests/sec    : {stats.total_rps:.2f}")
    print("="*60)
