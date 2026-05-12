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
