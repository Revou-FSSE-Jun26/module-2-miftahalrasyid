#!/bin/bash
# =============================================================================
# Security Audit Script for RevoShop API
# =============================================================================
# Runs a suite of security checks:
#   1. Secret/credential detection (gitleaks or grep fallback)
#   2. Python dependency vulnerabilities (pip-audit)
#   3. Python static analysis (bandit)
#   4. .env hygiene (not tracked in git, present in .gitignore)
#
# Usage:  ./audit.sh
# Exit code: 0 if all critical checks pass, 1 if any fail.
# =============================================================================

set -uo pipefail

# --- Colors ---
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

FAIL_COUNT=0
WARN_COUNT=0

pass()  { echo -e "${GREEN}[PASS]${NC} $1"; }
warn()  { echo -e "${YELLOW}[WARN]${NC} $1"; WARN_COUNT=$((WARN_COUNT + 1)); }
fail()  { echo -e "${RED}[FAIL]${NC} $1"; FAIL_COUNT=$((FAIL_COUNT + 1)); }
info()  { echo -e "${BLUE}[INFO]${NC} $1"; }
section() { echo -e "\n${BLUE}=== $1 ===${NC}"; }

# =============================================================================
# 1. SECRET / CREDENTIAL DETECTION
# =============================================================================
section "1. Secret & Credential Detection"

if command -v gitleaks >/dev/null 2>&1; then
    info "Running gitleaks..."
    GITLEAKS_CONFIG_FLAG=""
    if [ -f ".gitleaks.toml" ]; then
        GITLEAKS_CONFIG_FLAG="--config .gitleaks.toml"
    fi
    if gitleaks detect --source . $GITLEAKS_CONFIG_FLAG --no-banner --redact 2>/dev/null; then
        pass "gitleaks found no secrets"
    else
        fail "gitleaks detected potential secrets (see output above)"
    fi
else
    warn "gitleaks not installed — falling back to grep (less thorough)"
    info "Install: brew install gitleaks"

    # Patterns for common secrets. Exclude venv, .git, examples, and this script.
    SECRET_HITS=$(grep -rnE \
        -e '(password|passwd|pwd)\s*=\s*["'\''][^"'\'' ]{6,}' \
        -e '(secret|api[_-]?key|token)\s*=\s*["'\''][^"'\'' ]{12,}' \
        -e 'AKIA[0-9A-Z]{16}' \
        -e '-----BEGIN (RSA |EC )?PRIVATE KEY-----' \
        --include='*.py' --include='*.yml' --include='*.yaml' --include='*.json' \
        --exclude-dir=venv --exclude-dir=.git --exclude-dir=__pycache__ \
        --exclude='*.example' --exclude='audit.sh' \
        . 2>/dev/null | grep -viE '(os\.environ|getenv|example|your-|placeholder|<your)')

    if [ -z "$SECRET_HITS" ]; then
        pass "No hardcoded secrets found via grep"
    else
        fail "Potential hardcoded secrets found:"
        echo "$SECRET_HITS"
    fi
fi

# =============================================================================
# 2. PYTHON DEPENDENCY VULNERABILITIES
# =============================================================================
section "2. Dependency Vulnerabilities"

if command -v pip-audit >/dev/null 2>&1; then
    info "Running pip-audit..."
    if pip-audit -r requirements.txt 2>/dev/null; then
        pass "No known vulnerabilities in dependencies"
    else
        warn "pip-audit reported vulnerabilities (review above)"
    fi
else
    warn "pip-audit not installed — skipping dependency scan"
    info "Install: pip install pip-audit"
fi

# =============================================================================
# 3. PYTHON STATIC ANALYSIS (SAST)
# =============================================================================
section "3. Static Code Analysis (bandit)"

if command -v bandit >/dev/null 2>&1; then
    info "Running bandit on app/..."
    # -ll = only report medium+ severity; skip test folders
    if bandit -r app/ -ll -q 2>/dev/null; then
        pass "bandit found no medium/high severity issues"
    else
        warn "bandit reported issues (review above)"
    fi
else
    warn "bandit not installed — skipping static analysis"
    info "Install: pip install bandit"
fi

# =============================================================================
# 4. .ENV HYGIENE
# =============================================================================
section "4. Environment File Hygiene"

# 4a. .env must be in .gitignore
if grep -qE '^\.env$|^\.env\b' .gitignore 2>/dev/null; then
    pass ".env is listed in .gitignore"
else
    fail ".env is NOT in .gitignore — risk of committing secrets"
fi

# 4b. .env must NOT be tracked by git
if git ls-files --error-unmatch .env >/dev/null 2>&1; then
    fail ".env is TRACKED by git — remove it: git rm --cached .env"
else
    pass ".env is not tracked by git"
fi

# 4c. .env must NOT exist in git history
if git log --all --full-history --oneline -- .env 2>/dev/null | grep -q .; then
    fail ".env appears in git history — consider scrubbing with git filter-repo"
else
    pass ".env not found in git history"
fi

# =============================================================================
# SUMMARY
# =============================================================================
section "Summary"
echo -e "Failures: ${RED}${FAIL_COUNT}${NC}   Warnings: ${YELLOW}${WARN_COUNT}${NC}"

if [ "$FAIL_COUNT" -gt 0 ]; then
    echo -e "${RED}Audit failed. Resolve the failures above.${NC}"
    exit 1
else
    echo -e "${GREEN}Audit passed.${NC}"
    exit 0
fi
