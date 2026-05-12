# 🛡️ CyberQuest — Cybersecurity Awareness Game

> ICT932 – Cybersecurity Testing and Assurance | Group Project

A web-based cybersecurity awareness game that teaches students phishing awareness, password security, social engineering, and safe browsing through interactive challenges, scoring, badges, and a teacher dashboard.

---

## 👥 Team Members

| Member | Role | Branch |
|--------|------|--------|
| Member 1 (Team Lead) | Authentication & Security | `feature/auth-security` |
| Member 2 | Game Module Developer | `feature/game-modules` |
| Member 3 | Admin Dashboard & Frontend/UI | `feature/admin-dashboard` |
| Member 4 | DevSecOps & Testing | `feature/devsecops-testing` |

---

## 🚀 Tech Stack

| Layer | Tool |
|-------|------|
| Backend | Python Flask |
| Frontend | HTML, CSS, JavaScript, Bootstrap |
| Database | SQLite |
| Auth | Flask-Login + Flask-Bcrypt |
| 2FA | PyOTP |
| Testing | Pytest |
| SAST | Bandit |
| Dependency Scan | pip-audit |
| DAST | OWASP ZAP |
| CI/CD | GitHub Actions |

---

## 📁 Project Structure

```
cybersecurity-awareness-game/
├── src/
│   ├── app.py              # Main Flask application entry point
│   ├── models.py           # Database models (User, Challenge, Score)
│   ├── routes.py           # General routes
│   ├── auth.py             # Login, register, 2FA (Member 1)
│   ├── game.py             # Game logic, scoring, badges (Member 2)
│   ├── admin.py            # Teacher dashboard (Member 3)
│   ├── security.py         # Security logging, access control (Member 1)
│   ├── templates/          # HTML templates (Jinja2)
│   └── static/             # CSS, JS, images
├── tests/
│   ├── test_auth.py
│   ├── test_game.py
│   ├── test_admin.py
│   └── test_security.py
├── docs/
│   ├── threat_model.md
│   ├── architecture.md
│   ├── user_guide.md
│   ├── testing_results.md
│   └── screenshots/
├── ci-cd/
│   └── github-actions-notes.md
├── .github/
│   └── workflows/
│       └── devsecops.yml
├── requirements.txt
├── README.md
└── .gitignore
```

---

## ⚙️ Setup Instructions

### Prerequisites
- Python 3.10+
- pip

### Installation

```bash
# 1. Clone the repository
git clone https://github.com/YOUR-USERNAME/cybersecurity-awareness-game.git
cd cybersecurity-awareness-game

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

### Test Accounts (Demo)

| Role | Username | Password |
|------|----------|----------|
| Student | `student@demo.com` | `Test1234!` |
| Teacher | `teacher@demo.com` | `Admin1234!` |

> ⚠️ These are demo accounts only. Change before any deployment.

---

## 🔐 Security Features

- Secure registration with bcrypt password hashing
- Role-Based Access Control (RBAC): Student and Teacher roles
- Two-Factor Authentication (2FA) using PyOTP (TOTP)
- Login attempt logging
- Protected routes with Flask-Login
- SAST via Bandit
- Dependency scanning via pip-audit
- DAST via OWASP ZAP baseline scan

---

## 🧪 Running Tests

```bash
pytest tests/ -v
```

---

## 🔄 CI/CD Pipeline

GitHub Actions runs automatically on every push to `dev` or `main`:

1. **Build** — Install dependencies
2. **Test** — Run Pytest
3. **SAST** — Bandit security scan
4. **Dependency Scan** — pip-audit
5. **DAST** — OWASP ZAP baseline scan (on `main` only)

See `.github/workflows/devsecops.yml` for full pipeline config.

---

## 📋 Git Workflow

```bash
# Always start from dev
git checkout dev
git pull origin dev

# Create your feature branch
git checkout -b feature/your-name-feature

# Make changes, then commit
git add .
git commit -m "Brief description of what you did"
git push origin feature/your-name-feature

# Open a Pull Request to dev on GitHub
```

**Commit at least 2 meaningful commits per week from Week 6 onward.**

---

## 🗂️ Weekly Roadmap

| Week | Goal |
|------|------|
| Week 6 | Project setup, GitHub repo, initial Flask app |
| Week 7 | Login, registration, roles, basic game page |
| Week 8 | 2FA, phishing quiz, scoring, Bandit scan |
| Week 9 | 15 challenges, badges, progress tracking |
| Week 10 | Alpha — full game + CI/CD pipeline |
| Week 11 | Final testing, report prep, screenshots |
| Week 12 | Presentation and live demo |
| Week 13 | Final report submission |

---

## 🤖 AI Tool Declaration

As per ICT932 assessment requirements, AI tools were used for research, brainstorming, and concept clarification during this project. All final report content and code have been written and reviewed by team members.

---

## 📄 License

This project is developed for academic purposes as part of ICT932 at Crown Institute of Higher Education (CIHE).
