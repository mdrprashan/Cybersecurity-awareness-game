# Threat Model — CyberQuest Cybersecurity Awareness Game

**Document:** `docs/threat_model.md`  
**Author:** Prashan Manandhar (CIHE241182) — Team Lead, Authentication & Security  
**Subject:** ICT932 — Cybersecurity Testing and Assurance  
**Institution:** Crown Institute of Higher Education (CIHE)  
**Date:** May 2026

---

## 1. Overview

This document presents a STRIDE-based threat model for CyberQuest, a web-based cybersecurity awareness game built with Python Flask. The application serves two user roles — students and teachers — and supports features including authentication, 2FA, quiz challenges, scoring, badge rewards, and a teacher dashboard.

The threat model analyses the system for six threat categories defined by the STRIDE framework: **Spoofing, Tampering, Repudiation, Information Disclosure, Denial of Service,** and **Elevation of Privilege**.

---

## 2. System Architecture Summary

```
Browser (Client)
    │
    ▼ HTTPS
Flask App (src/)
    ├── auth.py       — Login, Register, Logout, 2FA
    ├── game.py       — Challenges, Scoring, Badges
    ├── admin.py      — Teacher Dashboard
    ├── security.py   — Login Attempt Logging, RBAC
    └── models.py     — SQLAlchemy ORM
         │
         ▼
SQLite Database (cyberquest.db)
```

**Trust Boundaries:**
- External users (unauthenticated) → Flask login endpoints
- Authenticated students → game and progress routes
- Authenticated teachers → admin dashboard + security audit routes
- Application → SQLite database (same host)

---

## 3. Assets

| Asset | Sensitivity | Description |
|---|---|---|
| User credentials (passwords) | High | Bcrypt-hashed passwords stored in DB |
| TOTP secrets | High | PyOTP secrets for 2FA |
| Session tokens | High | Flask-Login session cookies |
| Student quiz scores | Medium | Per-user progress data |
| Challenge content | Low | Quiz questions and answers |
| Login audit log | Medium | IP addresses, timestamps, attempt results |

---

## 4. STRIDE Threat Analysis

### 4.1 Spoofing

**Threat:** An attacker impersonates a legitimate user by stealing or guessing credentials.

| ID | Threat | Component | Likelihood | Impact |
|---|---|---|---|---|
| S-01 | Credential guessing / brute force on /login | auth.py | High | High |
| S-02 | Session token theft via XSS or network interception | Flask sessions | Medium | High |
| S-03 | TOTP code replay attack (reusing a valid 6-digit code) | auth.py – verify_2fa | Low | Medium |

**Mitigations Implemented:**
- **S-01:** Brute-force lockout after 5 failed attempts within 15 minutes (`security.py – is_account_locked`). All attempts logged to `LoginAttempt` table.
- **S-02:** Flask `SESSION_COOKIE_HTTPONLY=True` and `SESSION_COOKIE_SAMESITE='Lax'` prevent cookie theft via JavaScript. HTTPS enforced in production.
- **S-03:** PyOTP TOTP tokens are time-based (30-second window) and each token is single-use within that window.

---

### 4.2 Tampering

**Threat:** An attacker modifies data in transit or directly in the database.

| ID | Threat | Component | Likelihood | Impact |
|---|---|---|---|---|
| T-01 | SQL injection via login or registration forms | models.py | Medium | Critical |
| T-02 | Score manipulation by intercepting and modifying POST requests | game.py | Medium | Medium |
| T-03 | Direct database file access on server | cyberquest.db | Low | Critical |

**Mitigations Implemented:**
- **T-01:** All database queries use Flask-SQLAlchemy ORM with parameterised queries — raw SQL is never used, eliminating SQLi risk.
- **T-02:** All score calculations are server-side. The client only submits the selected answer; points are calculated in Python, not trusted from form data.
- **T-03:** `cyberquest.db` is stored outside the web root. `.gitignore` excludes it from version control. Production should restrict OS-level file permissions.

---

### 4.3 Repudiation

**Threat:** A user denies having performed an action (e.g. denies failed login attempts).

| ID | Threat | Component | Likelihood | Impact |
|---|---|---|---|---|
| R-01 | User denies repeated failed login attempts | security.py | Medium | Medium |
| R-02 | Teacher denies modifying challenge content | admin.py | Low | Medium |

**Mitigations Implemented:**
- **R-01:** Every login attempt (success or failure) is recorded in the `LoginAttempt` table with email, IP address, timestamp, and outcome. Teachers can view this via `/security/audit-log`.
- **R-02:** Future enhancement — add an admin action log. Currently out of scope for this phase.

---

### 4.4 Information Disclosure

**Threat:** Sensitive information is exposed to unauthorised parties.

| ID | Threat | Component | Likelihood | Impact |
|---|---|---|---|---|
| I-01 | Password exposure via debug mode or error pages | app.py | Medium | Critical |
| I-02 | TOTP secret exposed in QR code URL | auth.py – setup_2fa | Low | High |
| I-03 | Student data exposed to other students | game.py, admin.py | Low | Medium |
| I-04 | Sensitive data in version control (.env, db file) | .gitignore | Medium | High |

**Mitigations Implemented:**
- **I-01:** Flask debug mode is disabled in production (`debug=False`). Generic error pages shown to users; detailed errors only in logs.
- **I-02:** QR code is generated server-side and delivered as a base64 PNG — the raw provisioning URI is not exposed in HTML. The TOTP secret is displayed once and should be stored by the user.
- **I-03:** Flask-Login `@login_required` on all authenticated routes. Student data is scoped by `user_id` foreign key.
- **I-04:** `.gitignore` excludes `*.db`, `.env`, `venv/`, `__pycache__/`. Secret key uses environment variable in production.

---

### 4.5 Denial of Service

**Threat:** The application is made unavailable to legitimate users.

| ID | Threat | Component | Likelihood | Impact |
|---|---|---|---|---|
| D-01 | Account lockout abuse (locking out other users) | auth.py – login | Medium | Medium |
| D-02 | Database exhaustion via mass registration | auth.py – register | Low | Medium |
| D-03 | SQLite file lock under heavy concurrent load | cyberquest.db | Medium | Medium |

**Mitigations Implemented:**
- **D-01:** Lockout is based on email+IP combination. Rate limiting at the reverse proxy level (nginx) is recommended for production. Note: lockout by email alone can be abused to lock out legitimate users — this is a known trade-off.
- **D-02:** Email uniqueness constraint in the database prevents duplicate accounts. CAPTCHA can be added for production.
- **D-03:** SQLite is single-writer by default; PostgreSQL should be used in production for multi-user concurrent load.

---

### 4.6 Elevation of Privilege

**Threat:** A lower-privileged user gains access to higher-privileged functions.

| ID | Threat | Component | Likelihood | Impact |
|---|---|---|---|---|
| E-01 | Student accesses teacher dashboard | admin.py | Medium | High |
| E-02 | Unauthenticated user accesses protected routes | auth.py, game.py | High | High |
| E-03 | Student self-assigns teacher role at registration | auth.py – register | Medium | High |

**Mitigations Implemented:**
- **E-01:** `@role_required('teacher')` decorator in `security.py` protects all admin routes. Verified in `test_security.py`.
- **E-02:** `@login_required` from Flask-Login is applied to all non-public routes. Unauthenticated users are redirected to `/login`.
- **E-03:** Teacher registration requires a secret `teacher_code` (`CIHE-TEACH-2026`). Without it, the role defaults to `student`.

---

## 5. Risk Summary

| Threat ID | Category | Risk Level | Status |
|---|---|---|---|
| S-01 | Spoofing | 🔴 High | ✅ Mitigated |
| S-02 | Spoofing | 🟡 Medium | ✅ Mitigated |
| T-01 | Tampering | 🔴 High | ✅ Mitigated |
| T-02 | Tampering | 🟡 Medium | ✅ Mitigated |
| R-01 | Repudiation | 🟡 Medium | ✅ Mitigated |
| I-01 | Info Disclosure | 🔴 High | ✅ Mitigated |
| I-04 | Info Disclosure | 🟡 Medium | ✅ Mitigated |
| D-01 | DoS | 🟡 Medium | ⚠️ Partially Mitigated |
| D-03 | DoS | 🟡 Medium | ⚠️ Accept (dev scope) |
| E-01 | Elevation | 🔴 High | ✅ Mitigated |
| E-02 | Elevation | 🔴 High | ✅ Mitigated |
| E-03 | Elevation | 🟡 Medium | ✅ Mitigated |

---

## 6. Residual Risks & Future Recommendations

- **CAPTCHA on registration and login** to prevent automated abuse.
- **HTTPS enforcement** via reverse proxy (nginx) with HSTS headers in production.
- **PostgreSQL** to replace SQLite for concurrent production load.
- **Secrets management** via environment variables (`.env` with `python-dotenv`) rather than hardcoded config values.
- **Admin action logging** for teacher dashboard changes (create/edit/delete challenges).
- **Rate limiting** via Flask-Limiter or nginx on `/login` and `/register`.

---

## 7. References

- Microsoft STRIDE Threat Modelling Framework
- OWASP Top 10 (2021) — https://owasp.org/www-project-top-ten/
- NIST SP 800-30 — Guide for Conducting Risk Assessments
- Flask Security Considerations — https://flask.palletsprojects.com/en/3.0.x/security/
