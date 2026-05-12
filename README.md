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
| Backend | Python Flask 3.0 |
| Frontend | HTML5, CSS3, JavaScript, Bootstrap 5 |
| Database | SQLite + Flask-SQLAlchemy |
| Auth | Flask-Login + Flask-Bcrypt |
| 2FA | PyOTP (TOTP) + qrcode |
| Testing | Pytest + pytest-flask |
| SAST | Bandit |
| Dependency Scan | pip-audit |
| DAST | OWASP ZAP |
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
│   ├── test_auth.py        # Auth unit tests (Prashan)
│   ├── test_game.py        # Game unit tests (Raju)
│   ├── test_admin.py       # Admin unit tests (Pramesh)
│   └── test_security.py    # Security tests (Susanta)
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
- Login attempt logging for brute force detection
- Protected routes with Flask-Login decorators
- SAST scanning via Bandit
- Dependency vulnerability scanning via pip-audit
- Dynamic security testing via OWASP ZAP baseline scan

---

## 🧪 Running Tests

```bash
pytest tests/ -v
```

---

## 🔄 CI/CD Pipeline

GitHub Actions runs automatically on every push to `dev` or `main`:

| Stage | Tool | Trigger |
|-------|------|---------|
| 1. Build | pip install | All branches |
| 2. Test | Pytest | All branches |
| 3. SAST | Bandit | All branches |
| 4. Dependency Scan | pip-audit | All branches |
| 5. DAST | OWASP ZAP | `main` only |

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

| Week | Goal |
|------|------|
| Week 6 | Project setup, GitHub repo, Flask app, database models |
| Week 7 | Login, register, RBAC, first game category, base template |
| Week 8 | 2FA, phishing quiz, scoring, Bandit scan in pipeline |
| Week 9 | All 15 challenges, badges, progress tracking, pip-audit + ZAP |
| Week 10 | Alpha — full app working, all pipeline stages green |
| Week 11 | Final testing, report writing, screenshots |
| Week 12 | Presentation and live demo |
| Week 13 | Final report submission |

---

## 🤖 AI Tool Declaration

As per ICT932 assessment requirements, AI tools were used to assist with research, code scaffolding, and concept clarification during this project. All final code has been reviewed, tested, and understood by the respective team members responsible for each module.

---

## 📄 License

This project is developed for academic purposes as part of ICT932 — Cybersecurity Testing and Assurance at Crown Institute of Higher Education (CIHE).