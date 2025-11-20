#!/bin/bash
# Phase 1.2 Validation Script
# Validates that all database schema components are properly implemented

set -e

echo "========================================="
echo "Phase 1.2 Validation Script"
echo "Database Schema & Migrations"
echo "========================================="
echo ""

# Color codes
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Counters
PASSED=0
FAILED=0

# Helper function to check result
check_result() {
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ PASS${NC}: $1"
        ((PASSED++))
    else
        echo -e "${RED}✗ FAIL${NC}: $1"
        ((FAILED++))
    fi
}

# Check if we're in the backend directory
if [ ! -f "alembic.ini" ]; then
    echo -e "${RED}Error: Must run from backend directory${NC}"
    exit 1
fi

echo "1. Checking Python files..."
python3 -m py_compile app/core/config.py 2>/dev/null
check_result "config.py syntax"

python3 -m py_compile app/core/database.py 2>/dev/null
check_result "database.py syntax"

python3 -m py_compile app/models/company.py 2>/dev/null
check_result "company.py syntax"

python3 -m py_compile app/models/filing.py 2>/dev/null
check_result "filing.py syntax"

python3 -m py_compile app/models/user.py 2>/dev/null
check_result "user.py syntax"

python3 -m py_compile app/models/audit.py 2>/dev/null
check_result "audit.py syntax"

python3 -m py_compile app/main.py 2>/dev/null
check_result "main.py syntax"

echo ""
echo "2. Checking Alembic configuration..."

[ -f "alembic.ini" ]
check_result "alembic.ini exists"

[ -f "alembic/env.py" ]
check_result "alembic/env.py exists"

[ -f "alembic/script.py.mako" ]
check_result "alembic migration template exists"

[ -f "alembic/versions/20251120_0000-initial_schema.py" ]
check_result "Initial migration exists"

echo ""
echo "3. Checking model imports..."
python3 -c "from app.models import Company, Filing, FilingDocument, User, UserAlert, AlertMatch, AuditLog" 2>/dev/null
check_result "All models importable"

echo ""
echo "4. Checking required files..."

[ -f "requirements.txt" ]
check_result "requirements.txt exists"

[ -f "requirements-dev.txt" ]
check_result "requirements-dev.txt exists"

[ -f "Dockerfile" ]
check_result "Dockerfile exists"

[ -f "pytest.ini" ]
check_result "pytest.ini exists"

[ -f "tests/conftest.py" ]
check_result "Test configuration exists"

[ -f "tests/test_models.py" ]
check_result "Model tests exist"

echo ""
echo "5. Checking helper scripts..."

[ -x "scripts/migrate.sh" ]
check_result "migrate.sh is executable"

[ -x "scripts/create_migration.sh" ]
check_result "create_migration.sh is executable"

[ -x "scripts/reset_db.sh" ]
check_result "reset_db.sh is executable"

echo ""
echo "6. Checking migration content..."

# Check that migration includes all tables
grep -q "create_table('companies'" alembic/versions/20251120_0000-initial_schema.py
check_result "Migration includes companies table"

grep -q "create_table('filings'" alembic/versions/20251120_0000-initial_schema.py
check_result "Migration includes filings table"

grep -q "create_table('filing_documents'" alembic/versions/20251120_0000-initial_schema.py
check_result "Migration includes filing_documents table"

grep -q "create_table('users'" alembic/versions/20251120_0000-initial_schema.py
check_result "Migration includes users table"

grep -q "create_table('user_alerts'" alembic/versions/20251120_0000-initial_schema.py
check_result "Migration includes user_alerts table"

grep -q "create_table('alert_matches'" alembic/versions/20251120_0000-initial_schema.py
check_result "Migration includes alert_matches table"

grep -q "create_table('audit_logs'" alembic/versions/20251120_0000-initial_schema.py
check_result "Migration includes audit_logs table"

# Check for materialized views
grep -q "company_filing_stats" alembic/versions/20251120_0000-initial_schema.py
check_result "Migration includes company_filing_stats view"

grep -q "monthly_filing_stats" alembic/versions/20251120_0000-initial_schema.py
check_result "Migration includes monthly_filing_stats view"

grep -q "refresh_materialized_views" alembic/versions/20251120_0000-initial_schema.py
check_result "Migration includes refresh function"

echo ""
echo "========================================="
echo "Validation Results"
echo "========================================="
echo -e "${GREEN}Passed: $PASSED${NC}"
echo -e "${RED}Failed: $FAILED${NC}"
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}✓ Phase 1.2 validation PASSED!${NC}"
    echo ""
    echo "Next steps:"
    echo "1. Start Docker: docker-compose up -d postgres"
    echo "2. Run migrations: alembic upgrade head"
    echo "3. Run tests: pytest"
    echo "4. Start API: uvicorn app.main:app --reload"
    exit 0
else
    echo -e "${RED}✗ Phase 1.2 validation FAILED${NC}"
    echo "Please review the failures above."
    exit 1
fi
