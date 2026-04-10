#!/bin/bash

# Validation script for add-entity-tests skill
# Usage: bash .claude/skills/add-entity-tests/scripts/validate.sh <entity_name>

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check if entity name is provided
if [ -z "$1" ]; then
    echo -e "${RED}Error: Entity name is required${NC}"
    echo "Usage: bash .claude/skills/add-entity-tests/scripts/validate.sh <entity_name>"
    exit 1
fi

ENTITY_NAME=$1
ENTITY_NAME_UPPER=$(echo "$ENTITY_NAME" | awk -F_ '{for(i=1;i<=NF;i++) printf "%s", toupper(substr($i,1,1)) substr($i,2); print ""}')

echo -e "${BLUE}Validating tests for entity: $ENTITY_NAME (PascalCase: $ENTITY_NAME_UPPER)${NC}"
echo "=========================================================================="

ERRORS=0
WARNINGS=0
TESTS_FOUND=0

# Function to check if file exists
check_file() {
    local file=$1
    local description=$2

    if [ -f "$file" ]; then
        echo -e "${GREEN}✓${NC} $description exists"
        return 0
    else
        echo -e "${RED}✗${NC} $description is missing: $file"
        ((ERRORS++))
        return 1
    fi
}

# Function to check if content exists in file
check_content() {
    local file=$1
    local pattern=$2
    local description=$3

    if [ ! -f "$file" ]; then
        echo -e "${RED}✗${NC} Cannot check $description: file $file does not exist"
        ((ERRORS++))
        return 1
    fi

    if grep -q "$pattern" "$file"; then
        echo -e "${GREEN}✓${NC} $description found"
        return 0
    else
        echo -e "${YELLOW}⚠${NC} $description not found"
        echo -e "  ${YELLOW}Expected pattern: $pattern${NC}"
        ((WARNINGS++))
        return 1
    fi
}

# Function to count tests in file
count_tests() {
    local file=$1

    if [ -f "$file" ]; then
        local count=$(grep -c "^def test_" "$file" || true)
        echo -e "${BLUE}  → $count test(s) found${NC}"
        ((TESTS_FOUND += count))
    fi
}

echo ""
echo "1. Checking test file existence..."
echo "-----------------------------------"

check_file "src/tests/fixtures/${ENTITY_NAME}_fixtures.py" "Fixtures file"
check_file "src/tests/unit/mappers/test_${ENTITY_NAME}_mapper.py" "Mapper tests file"
check_file "src/tests/unit/services/test_${ENTITY_NAME}_service.py" "Service tests file"
check_file "src/tests/unit/routers/test_${ENTITY_NAME}.py" "Router tests file"

echo ""
echo "2. Checking fixtures..."
echo "-----------------------"

check_content "src/tests/fixtures/${ENTITY_NAME}_fixtures.py" "def ${ENTITY_NAME}_id" "Entity ID fixture"
check_content "src/tests/fixtures/${ENTITY_NAME}_fixtures.py" "def ${ENTITY_NAME}_create" "Create model fixture"
check_content "src/tests/fixtures/${ENTITY_NAME}_fixtures.py" "def ${ENTITY_NAME}_update" "Update model fixture"
check_content "src/tests/fixtures/${ENTITY_NAME}_fixtures.py" "def ${ENTITY_NAME}(" "Read model fixture"
check_content "src/tests/fixtures/${ENTITY_NAME}_fixtures.py" "def ${ENTITY_NAME}s" "Model list fixture"
check_content "src/tests/fixtures/${ENTITY_NAME}_fixtures.py" "def ${ENTITY_NAME}_entity" "Entity fixture"
check_content "src/tests/fixtures/${ENTITY_NAME}_fixtures.py" "def ${ENTITY_NAME}_error_result_not_found" "Not found error fixture"
check_content "src/tests/fixtures/${ENTITY_NAME}_fixtures.py" "def ${ENTITY_NAME}_not_found" "Not found problem details fixture"

echo ""
echo "3. Checking mapper tests..."
echo "---------------------------"

check_content "src/tests/unit/mappers/test_${ENTITY_NAME}_mapper.py" "from src.mappers.${ENTITY_NAME} import" "Mapper import"
check_content "src/tests/unit/mappers/test_${ENTITY_NAME}_mapper.py" "def test_to_${ENTITY_NAME}_entity" "Mapper function test"
check_content "src/tests/unit/mappers/test_${ENTITY_NAME}_mapper.py" "assert isinstance(result.id, UUID)" "UUID generation check"
check_content "src/tests/unit/mappers/test_${ENTITY_NAME}_mapper.py" "assert result.is_active is True" "is_active check"
check_content "src/tests/unit/mappers/test_${ENTITY_NAME}_mapper.py" "assert result.created_by_user_id" "Audit field check"
count_tests "src/tests/unit/mappers/test_${ENTITY_NAME}_mapper.py"

echo ""
echo "4. Checking service tests..."
echo "----------------------------"

check_content "src/tests/unit/services/test_${ENTITY_NAME}_service.py" "from src.services.${ENTITY_NAME}_service import" "Service import"
check_content "src/tests/unit/services/test_${ENTITY_NAME}_service.py" "def test_get_page" "get_page test"
count_tests "src/tests/unit/services/test_${ENTITY_NAME}_service.py"

echo ""
echo "5. Checking router tests..."
echo "---------------------------"

ROUTER_FILE="src/tests/unit/routers/test_${ENTITY_NAME}.py"

check_content "$ROUTER_FILE" "from src.services.${ENTITY_NAME}_service import" "Service import"
check_content "$ROUTER_FILE" "def test_get_${ENTITY_NAME}" "GET list test"
check_content "$ROUTER_FILE" "def test_get_.*__validation_error" "GET list validation error test"
check_content "$ROUTER_FILE" "def test_get_${ENTITY_NAME}_by_id" "GET by ID test"
check_content "$ROUTER_FILE" "def test_get_${ENTITY_NAME}_by_id.*not_found" "GET by ID not found test"
check_content "$ROUTER_FILE" "def test_create_${ENTITY_NAME}" "POST create test"
check_content "$ROUTER_FILE" "def test_create_${ENTITY_NAME}.*validation_error" "POST validation error test"
check_content "$ROUTER_FILE" "def test_update_${ENTITY_NAME}" "PATCH update test"
check_content "$ROUTER_FILE" "def test_update_${ENTITY_NAME}.*not_found" "PATCH not found test"
check_content "$ROUTER_FILE" "def test_update_${ENTITY_NAME}.*validation_error" "PATCH validation error test"
check_content "$ROUTER_FILE" "def test_delete_${ENTITY_NAME}" "DELETE test"
check_content "$ROUTER_FILE" "def test_delete_${ENTITY_NAME}.*not_found" "DELETE not found test"
count_tests "$ROUTER_FILE"

echo ""
echo "6. Checking conftest.py registration..."
echo "----------------------------------------"

check_content "src/tests/conftest.py" "src.tests.fixtures.${ENTITY_NAME}_fixtures" "Fixture plugin registration"
check_content "src/tests/conftest.py" "def ${ENTITY_NAME}_data_service" "Data service fixture"
check_content "src/tests/conftest.py" "def ${ENTITY_NAME}_service" "Service fixture"

echo ""
echo "7. Running code quality checks..."
echo "----------------------------------"

# Check if uv is available
if command -v uv &> /dev/null; then
    echo "Running ruff format check..."
    if uv run ruff format --check "src/tests/fixtures/${ENTITY_NAME}_fixtures.py" "src/tests/unit/mappers/test_${ENTITY_NAME}_mapper.py" "src/tests/unit/services/test_${ENTITY_NAME}_service.py" "src/tests/unit/routers/test_${ENTITY_NAME}.py" 2>&1 | grep -q "Would reformat"; then
        echo -e "${YELLOW}⚠${NC} Files need formatting. Run: make pre_commit"
        ((WARNINGS++))
    else
        echo -e "${GREEN}✓${NC} All files are properly formatted"
    fi

    echo ""
    echo "Running ruff linter..."
    if uv run ruff check "src/tests/fixtures/${ENTITY_NAME}_fixtures.py" "src/tests/unit/mappers/test_${ENTITY_NAME}_mapper.py" "src/tests/unit/services/test_${ENTITY_NAME}_service.py" "src/tests/unit/routers/test_${ENTITY_NAME}.py" > /dev/null 2>&1; then
        echo -e "${GREEN}✓${NC} No linting errors found"
    else
        echo -e "${YELLOW}⚠${NC} Linting errors found. Run: make pre_commit"
        ((WARNINGS++))
    fi

    echo ""
    echo "Running mypy type check..."
    if uv run mypy "src/tests/fixtures/${ENTITY_NAME}_fixtures.py" "src/tests/unit/mappers/test_${ENTITY_NAME}_mapper.py" "src/tests/unit/services/test_${ENTITY_NAME}_service.py" "src/tests/unit/routers/test_${ENTITY_NAME}.py" > /dev/null 2>&1; then
        echo -e "${GREEN}✓${NC} Type checking passed"
    else
        echo -e "${YELLOW}⚠${NC} Type checking errors found. Run: make pre_commit"
        ((WARNINGS++))
    fi
else
    echo -e "${YELLOW}⚠${NC} uv not found, skipping code quality checks"
    ((WARNINGS++))
fi

echo ""
echo "8. Running tests..."
echo "-------------------"

if command -v uv &> /dev/null; then
    echo "Running mapper tests..."
    if PYTHONPATH=`pwd` uv run pytest "src/tests/unit/mappers/test_${ENTITY_NAME}_mapper.py" -v > /dev/null 2>&1; then
        echo -e "${GREEN}✓${NC} Mapper tests passed"
    else
        echo -e "${RED}✗${NC} Mapper tests failed"
        echo "  Run: PYTHONPATH=\`pwd\` uv run pytest src/tests/unit/mappers/test_${ENTITY_NAME}_mapper.py -vv"
        ((ERRORS++))
    fi

    echo ""
    echo "Running service tests..."
    if PYTHONPATH=`pwd` uv run pytest "src/tests/unit/services/test_${ENTITY_NAME}_service.py" -v > /dev/null 2>&1; then
        echo -e "${GREEN}✓${NC} Service tests passed"
    else
        echo -e "${RED}✗${NC} Service tests failed"
        echo "  Run: PYTHONPATH=\`pwd\` uv run pytest src/tests/unit/services/test_${ENTITY_NAME}_service.py -vv"
        ((ERRORS++))
    fi

    echo ""
    echo "Running router tests..."
    if PYTHONPATH=`pwd` uv run pytest "src/tests/unit/routers/test_${ENTITY_NAME}.py" -v > /dev/null 2>&1; then
        echo -e "${GREEN}✓${NC} Router tests passed"
    else
        echo -e "${RED}✗${NC} Router tests failed"
        echo "  Run: PYTHONPATH=\`pwd\` uv run pytest src/tests/unit/routers/test_${ENTITY_NAME}.py -vv"
        ((ERRORS++))
    fi
else
    echo -e "${YELLOW}⚠${NC} uv not found, skipping test execution"
    ((WARNINGS++))
fi

echo ""
echo "=========================================================================="
echo "Validation complete!"
echo ""
echo -e "${BLUE}Test Statistics:${NC}"
echo -e "  Total tests found: ${BLUE}$TESTS_FOUND${NC}"
echo ""

if [ $ERRORS -eq 0 ] && [ $WARNINGS -eq 0 ]; then
    echo -e "${GREEN}✓ All checks passed!${NC}"
    echo ""
    echo "Next steps:"
    echo "1. Run: PYTHONPATH=\`pwd\` uv run pytest src/tests/unit/mappers/test_${ENTITY_NAME}_mapper.py src/tests/unit/services/test_${ENTITY_NAME}_service.py src/tests/unit/routers/test_${ENTITY_NAME}.py -vv"
    echo "2. Run: make test"
    echo "3. Add custom test cases if needed"
    exit 0
elif [ $ERRORS -eq 0 ]; then
    echo -e "${YELLOW}⚠ Validation passed with $WARNINGS warning(s)${NC}"
    echo ""
    echo "Consider running: make pre_commit"
    exit 0
else
    echo -e "${RED}✗ Validation failed with $ERRORS error(s) and $WARNINGS warning(s)${NC}"
    exit 1
fi
