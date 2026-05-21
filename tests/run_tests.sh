#!/bin/bash
# ─────────────────────────────────────────────────────────────────────────────
# run_tests.sh — CyberQuest Complete Test Suite Runner
# ICT932 – Cybersecurity Testing and Assurance
#
# Usage (from project root):
#   bash run_tests.sh
#
# Produces results in: test_results/
# ─────────────────────────────────────────────────────────────────────────────

set -e
PROJECT_ROOT="$(cd "$(dirname "$0")" && pwd)"
RESULTS_DIR="$PROJECT_ROOT/test_results"
SRC_DIR="$PROJECT_ROOT/src"
TESTS_DIR="$PROJECT_ROOT/tests"

mkdir -p "$RESULTS_DIR"

echo ""
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║       CYBERQUEST ICT932 — FULL TEST SUITE                   ║"
echo "║       Crown Institute of Higher Education (CIHE)            ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

# ── 1. UNIT TESTS (pytest) ────────────────────────────────────────────────────
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  [1/3] UNIT TESTS — pytest"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

cd "$PROJECT_ROOT"

# Run pytest with verbose output and save to file
python -m pytest tests/ \
    -v \
    --tb=short \
    --no-header \
    -p no:cacheprovider \
    --junit-xml="$RESULTS_DIR/unit_test_results.xml" \
    2>&1 | tee "$RESULTS_DIR/unit_test_results.txt"

echo ""
echo "✅ Unit test results saved to: test_results/unit_test_results.txt"
echo ""

# ── 2. SECURITY SCAN (Bandit SAST) ───────────────────────────────────────────
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  [2/3] SECURITY CODE SCAN — Bandit (SAST)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Text report for reading
python -m bandit \
    -r "$SRC_DIR" \
    --exclude "$SRC_DIR/__pycache__" \
    -l \
    -ii \
    2>&1 | tee "$RESULTS_DIR/bandit_report.txt"

# JSON report for detailed analysis
python -m bandit \
    -r "$SRC_DIR" \
    --exclude "$SRC_DIR/__pycache__" \
    -f json \
    -o "$RESULTS_DIR/bandit_report.json" \
    2>/dev/null || true

echo ""
echo "✅ Bandit report saved to: test_results/bandit_report.txt"
echo ""

# ── 3. DEPENDENCY VULNERABILITY SCAN (pip-audit) ─────────────────────────────
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  [3/3] DEPENDENCY SCAN — pip-audit"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

python -m pip_audit \
    -r "$PROJECT_ROOT/requirements.txt" \
    2>&1 | tee "$RESULTS_DIR/pip_audit_report.txt" || true

echo ""
echo "✅ pip-audit report saved to: test_results/pip_audit_report.txt"
echo ""

# ── SUMMARY ───────────────────────────────────────────────────────────────────
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║  ALL TESTS COMPLETE — Results in: test_results/             ║"
echo "╠══════════════════════════════════════════════════════════════╣"
echo "║  unit_test_results.txt   — pytest output                    ║"
echo "║  unit_test_results.xml   — JUnit XML (for CI/CD)            ║"
echo "║  bandit_report.txt       — SAST security scan               ║"
echo "║  bandit_report.json      — SAST detailed JSON               ║"
echo "║  pip_audit_report.txt    — Dependency CVE scan              ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""
echo "For LOAD TESTING, run separately:"
echo "  pip install locust"
echo "  cd load && locust -f locustfile.py --host=http://127.0.0.1:5000"
echo "  Then open: http://localhost:8089"
echo ""
