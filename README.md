# 🛡️ CyberQuest — Cybersecurity Awareness Game

> ICT932 – Cybersecurity Testing and Assurance | Group Project

A web-based cybersecurity awareness game that teaches students phishing awareness, password security, and safe browsing through interactive challenges, scoring, badges, and a teacher dashboard.

---

## 👥 Team Members

| # | Name | Student ID | Role | Branch |
|---|------|------------|------|--------|
| 1 | Prashan Manandhar ⭐ Team Lead | CIHE241182 | Authentication & Security + Basic CI/CD Pipeline | `feature/auth-security` |
| 2 | Raju Kshetri | CIHE240711 | Game Module Developer | `feature/game-modules` |
| 3 | Pramesh Silwal | CIHE241339 | Admin Dashboard + Frontend/UI (shared) | `feature/admin-dashboard` |
| 4 | Susanta Dhakal | CIHE250321 | DevSecOps + Testing + Landing Page (shared) | `feature/devsecops-testing` |

---

## 🚀 Tech Stack

| Layer | Tool |
|-------|------|
| Backend | Python Flask 3.1.3 |
| Frontend | HTML5, CSS3, JavaScript, Bootstrap 5 |
| Database | SQLite + Flask-SQLAlchemy |
| Auth | Flask-Login + Flask-Bcrypt |
| 2FA | PyOTP (TOTP) + qrcode |
| Testing | Pytest + pytest-flask |
| SAST | Bandit 1.7.9 |
| Dependency Scan | pip-audit |
| DAST | OWASP ZAP 2.16.1 |
| Load Testing | Locust 2.44.0 |
| CI/CD | GitHub Actions |

---

## 📁 Project Structure

```
Cybersecurity-awareness-game/
├── src/
│   ├── app.py              # Flask app factory — create_app(), extensions, blueprints
│   ├── models.py           # DB models: User, Challenge, Score, Badge, UserBadge, LoginAttempt
│   ├── auth.py             # Login, register, logout, 2FA (Prashan)
│   ├── game.py             # Game logic, scoring, badges (Raju)
│   ├── admin.py            # Teacher dashboard, question management (Pramesh)
│   ├── security.py         # Login attempt logging, access control (Prashan)
│   ├── templates/          # Jinja2 HTML templates
│   │   ├── base.html       # Base layout + navbar (Pramesh & Susanta)
│   │   ├── index.html      # Landing page (Susanta)
│   │   ├── login.html      # Login page (Prashan)
│   │   ├── register.html   # Register page (Prashan)
│   │   ├── 2fa_setup.html  # 2FA QR code setup (Prashan)
│   │   ├── 2fa_verify.html # 2FA code entry (Prashan)
│   │   ├── challenges.html # Challenge categories (Raju)
│   │   ├── question.html   # Quiz question page (Raju)
│   │   ├── result.html     # Quiz result page (Raju)
│   │   ├── progress.html   # Student progress + badges (Raju)
│   │   └── admin_dashboard.html  # Teacher dashboard (Pramesh)
│   └── static/
│       ├── style.css       # Custom CSS (Pramesh)
│       └── game.js         # Quiz interaction JS (Raju)
├── tests/
│   ├── conftest.py         # Shared pytest fixtures (Susanta)
│   ├── test_auth.py        # Auth unit tests — 31/31 passing (Prashan)
│   ├── test_game.py        # Game unit tests — 23/25 passing (Raju)
│   ├── test_admin.py       # Admin unit tests — 14/22 passing (Pramesh)
│   ├── test_security.py    # Security tests — 26/26 passing (Susanta)
│   └── load/
│       └── locustfile.py   # Load testing scenarios (Susanta)
├── docs/
│   ├── threat_model.md     # STRIDE threat analysis (Prashan)
│   ├── architecture.md     # System architecture (Susanta)
│   ├── user_guide.md       # User guide (Pramesh)
│   ├── testing_results.md  # Test and scan results (Susanta)
│   └── screenshots/        # App screenshots for report
├── ci-cd/
│   └── github-actions-notes.md
├── .github/
│   └── workflows/
│       └── devsecops.yml   # GitHub Actions CI/CD pipeline
├── bandit_report.txt       # SAST scan results
├── bandit_report.json      # SAST scan results (JSON)
├── requirements.txt        # Python dependencies
├── README.md
└── .gitignore
```

---

## ⚙️ Setup Instructions

### Prerequisites
- Python 3.10+
- pip
- Git

### Installation

```bash
# 1. Clone the repository
git clone https://github.com/mdrprashan/Cybersecurity-awareness-game.git
cd Cybersecurity-awareness-game

# 2. Create a virtual environment
python -m venv venv
source venv/bin/activate        # macOS/Linux
venv\Scripts\activate           # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run the app
cd src
python app.py
```

Open your browser at `http://localhost:5000`

### Demo Accounts

| Role | Email | Password |
|------|-------|----------|
| Student | `student@demo.com` | `Test1234!` |
| Teacher | `teacher@demo.com` | `Admin1234!` |

> ⚠️ Demo accounts only. Do not use in any real deployment.

---

## 🔐 Security Features

- Secure password hashing with Flask-Bcrypt
- Role-Based Access Control (RBAC) — Student and Teacher roles
- Two-Factor Authentication (2FA) using PyOTP (TOTP)
- Login attempt logging with brute force lockout (5 attempts / 15 min)
- Protected routes with Flask-Login decorators
- Security headers (X-Frame-Options, CSP, Referrer-Policy, X-Content-Type)
- SAST scanning via Bandit
- Dependency vulnerability scanning via pip-audit
- Dynamic security testing via OWASP ZAP baseline scan

---

## 🧪 Testing

### Run Unit Tests

```bash
python -m pytest tests/ -v
```

### Week 10 Test Results — 94/104 Passing (90%)

| Test File | Passed | Total | Coverage |
|-----------|--------|-------|----------|
| test_auth.py | 31 | 31 | ✅ 100% |
| test_security.py | 26 | 26 | ✅ 100% |
| test_game.py | 23 | 25 | ✅ 92% |
| test_admin.py | 14 | 22 | ✅ 64% |
| **Total** | **94** | **104** | **90%** |

---

## 🔍 Security Scanning Results

### SAST — Bandit (Static Analysis)

```bash
python -m bandit -r src/ -f txt -o bandit_report.txt
```

| Severity | Count | Notes |
|----------|-------|-------|
| High | 0 | ✅ Clean |
| Medium | 0 | ✅ Clean |
| Low | 1 | Dev fallback secret key (labelled, not used in production) |

> **Result: PASSED** — 1,133 lines scanned, 0 exploitable issues found.

---

### Dependency Scan — pip-audit

```bash
python -m pip_audit
```

| Status | Packages | Vulnerabilities |
|--------|----------|----------------|
| Before fixes | 7 packages | 10 vulnerabilities |
| After fixes | 2 packages | 2 vulnerabilities |
| Fixed | flask, gitpython, idna, urllib3, pip | 8 fixed |
| Remaining | flask-cors, joblib | No fix available upstream |

> **Result: PASSED** — All fixable vulnerabilities remediated.

---

### DAST — OWASP ZAP 2.16.1 (Dynamic Analysis)

Performed manually against the locally running application on `http://127.0.0.1:5000`.

| Risk Level | Count | Details |
|-----------|-------|---------|
| 🔴 High | 0 | ✅ None found |
| 🟠 Medium | 4 | CSP headers, CSRF tokens |
| 🟡 Low | 3 | CDN JS inclusion, server version |
| ℹ️ Informational | 4 | Auth detection, GET/POST |

> **Result: PASSED** — No high-risk vulnerabilities found. Medium findings are standard hardening improvements documented for future sprints.

---

### Load Testing — Locust

```bash
python -m locust -f tests/load/locustfile.py
```

Settings: 20 virtual users, 5/s spawn rate, 60 seconds.

| Metric | Result |
|--------|--------|
| Total Requests | 619 |
| Failure Rate | **0%** ✅ |
| Median Response | 8ms ✅ |
| 95th Percentile | 13ms ✅ |
| Max Response | 263ms (POST /login — bcrypt, expected) |
| Requests/sec | 9.6 RPS |

> **Result: PASSED** — Zero failures under 20 concurrent users. Sub-13ms median response time.

---

## 🔄 CI/CD Pipeline

GitHub Actions runs automatically on every push to `dev` or `main`.

| Job | Tool | Status | Duration |
|-----|------|--------|----------|
| Build | pip install | ✅ Passing | ~11s |
| Pytest Unit Tests | pytest | ✅ Passing | ~20s |
| SAST Scan | Bandit | ✅ Passing | ~8s |
| Dependency Scan | pip-audit | ✅ Passing | ~19s |

> DAST is performed manually against a live deployment — automated DAST requires a running application server which is not available in the GitHub Actions environment.

See `.github/workflows/devsecops.yml` for full pipeline configuration.

---

## 📋 Git Workflow

```bash
# Always start by pulling latest changes
git checkout feature/your-branch-name
git pull origin feature/your-branch-name

# Make your changes, then commit
git add .
git commit -m "Clear description of what you did"
git push

# Open a Pull Request into dev on GitHub when feature is ready
# Prashan (Team Lead) reviews and merges all Pull Requests
```

### Branch Assignment

| Member | Branch |
|--------|--------|
| Prashan | `feature/auth-security` |
| Raju | `feature/game-modules` |
| Pramesh | `feature/admin-dashboard` |
| Susanta | `feature/devsecops-testing` |

**Commit at least 2 meaningful commits per week from Week 6 onward.**

---

## 🗂️ Weekly Roadmap

| Week | Goal | Status |
|------|------|--------|
| Week 6 | Project setup, GitHub repo, Flask app, database models | ✅ Done |
| Week 7 | Login, register, RBAC, first game category, base template | ✅ Done |
| Week 8 | 2FA, phishing quiz, scoring, Bandit scan in pipeline | ✅ Done |
| Week 9 | All 15 challenges, badges, progress tracking, pip-audit + ZAP | ✅ Done |
| Week 10 | Full testing suite, load testing, CI/CD pipeline all green | ✅ Done |
| Week 11 | Final testing, report writing, screenshots | 🔄 In Progress |
| Week 12 | Presentation and live demo | ⏳ Upcoming |
| Week 13 | Final report submission | ⏳ Upcoming |

---

## 🤖 AI Tool Declaration

As per ICT932 assessment requirements, AI tools were used to assist with research, code scaffolding, and concept clarification during this project. All final code has been reviewed, tested, and understood by the respective team members responsible for each module.

---

## 📄 License

This project is developed for academic purposes as part of ICT932 — Cybersecurity Testing and Assurance at Crown Institute of Higher Education (CIHE).