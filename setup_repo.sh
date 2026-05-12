#!/bin/bash
# ────────────────────────────────────────────────────────────
# CyberQuest — GitHub Repository Setup Script
# Run this ONCE after cloning your empty GitHub repo locally
# Usage: bash setup_repo.sh
# ────────────────────────────────────────────────────────────

echo "🛡️  Setting up CyberQuest repository structure..."

# ── Folder structure ──────────────────────────────────────
mkdir -p src/templates
mkdir -p src/static
mkdir -p tests
mkdir -p docs/screenshots
mkdir -p ci-cd
mkdir -p .github/workflows

# ── src/ placeholder files ────────────────────────────────
cat > src/app.py << 'EOF'
from flask import Flask
from models import db

app = Flask(__name__)
app.config['SECRET_KEY'] = 'change-this-secret-key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///cyberquest.db'
db.init_app(app)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
EOF

touch src/models.py
touch src/routes.py
touch src/auth.py
touch src/game.py
touch src/admin.py
touch src/security.py

# ── tests/ placeholder files ──────────────────────────────
touch tests/__init__.py
touch tests/test_auth.py
touch tests/test_game.py
touch tests/test_admin.py
touch tests/test_security.py

# ── docs/ placeholder files ───────────────────────────────
cat > docs/threat_model.md << 'EOF'
# Threat Model — CyberQuest

## Overview
This document outlines identified threats and mitigations for the CyberQuest system.

## STRIDE Analysis

| Threat | Description | Mitigation |
|--------|-------------|------------|
| Spoofing | Unauthorised login | bcrypt + 2FA |
| Tampering | Modifying scores | Server-side validation |
| Repudiation | Denying actions | Login attempt logging |
| Information Disclosure | Data leaks | RBAC, no debug in prod |
| Denial of Service | Flooding login | Rate limiting (future) |
| Elevation of Privilege | Student → Teacher | Role-checked decorators |

## To be completed by: Member 1
EOF

cat > docs/architecture.md << 'EOF'
# System Architecture — CyberQuest

## Overview
CyberQuest is a Flask-based web application with SQLite database storage.

## Components
- **Frontend**: HTML, CSS (Bootstrap), JavaScript
- **Backend**: Python Flask
- **Database**: SQLite
- **Auth**: Flask-Login + Flask-Bcrypt + PyOTP
- **CI/CD**: GitHub Actions

## To be completed by: Member 4
EOF

touch docs/user_guide.md
touch docs/testing_results.md

# ── ci-cd notes ───────────────────────────────────────────
cat > ci-cd/github-actions-notes.md << 'EOF'
# GitHub Actions — Notes

## Pipeline stages
1. Build — install dependencies
2. Test — run pytest
3. SAST — Bandit scan
4. Dependency Scan — pip-audit
5. DAST — OWASP ZAP (main branch only)

## How to view results
- Go to GitHub → Actions tab → select a workflow run
- Download artifacts (bandit-report, pip-audit-report, zap-report)

## To be completed by: Member 4
EOF

# ── requirements.txt ──────────────────────────────────────
cat > requirements.txt << 'EOF'
flask==3.0.3
flask-login==0.6.3
flask-sqlalchemy==3.1.1
flask-bcrypt==1.0.1
pyotp==2.9.0
pytest==8.2.2
bandit==1.7.9
pip-audit==2.7.3
EOF

# ── GitHub Actions workflow ────────────────────────────────
cp devsecops.yml .github/workflows/devsecops.yml 2>/dev/null || echo "⚠️  Copy devsecops.yml manually to .github/workflows/"

echo ""
echo "✅  Folder structure created."
echo ""
echo "── Next steps ──────────────────────────────────────"
echo "1. git init"
echo "2. git remote add origin https://github.com/YOUR-USERNAME/cybersecurity-awareness-game.git"
echo "3. git checkout -b dev"
echo "4. git add ."
echo "5. git commit -m 'Initial project structure and setup'"
echo "6. git push -u origin dev"
echo ""
echo "7. On GitHub: set dev as default branch (optional)"
echo "8. Enable branch protection on main:"
echo "   Settings → Branches → Add rule → main"
echo "   ✅ Require pull request reviews before merging"
echo "   ✅ Require status checks to pass"
echo ""
echo "9. Add teammates as collaborators:"
echo "   Settings → Collaborators → Add people"
echo ""
echo "10. Create your feature branch:"
echo "    git checkout -b feature/auth-security"
echo "    git push -u origin feature/auth-security"
echo ""
echo "🛡️  CyberQuest is ready to go!"
