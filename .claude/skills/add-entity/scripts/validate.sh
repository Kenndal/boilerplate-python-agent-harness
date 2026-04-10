#!/bin/bash

# Validation script for add-entity skill
# Usage: bash .claude/skills/add-entity/scripts/validate.sh <entity_name>

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if entity name is provided
if [ -z "$1" ]; then
    echo -e "${RED}Error: Entity name is required${NC}"
    echo "Usage: bash .claude/skills/add-entity/scripts/validate.sh <entity_name>"
    exit 1
fi

ENTITY_NAME=$1
ENTITY_NAME_UPPER=$(echo "$ENTITY_NAME" | awk '{print toupper(substr($0,1,1)) tolower(substr($0,2))}')

echo "Validating entity: $ENTITY_NAME (PascalCase: $ENTITY_NAME_UPPER)"
echo "=================================================="

ERRORS=0
WARNINGS=0

# Function to check if file exists
check_file() {
    local file=$1
    local description=$2

    if [ -f "$file" ]; then
        echo -e "${GREEN}✓${NC} $description exists"
    else
        echo -e "${RED}✗${NC} $description is missing: $file"
        ((ERRORS++))
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
        return
    fi

    if grep -q "$pattern" "$file"; then
        echo -e "${GREEN}✓${NC} $description found in $file"
    else
        echo -e "${RED}✗${NC} $description not found in $file"
        echo -e "  ${YELLOW}Expected pattern: $pattern${NC}"
        ((ERRORS++))
    fi
}

echo ""
echo "1. Checking file existence..."
echo "------------------------------"

check_file "src/database/entities/${ENTITY_NAME}.py" "Entity file"
check_file "src/models/${ENTITY_NAME}.py" "Models file"
check_file "src/mappers/${ENTITY_NAME}.py" "Mapper file"
check_file "src/data_services/${ENTITY_NAME}_data_service.py" "Data service file"
check_file "src/services/${ENTITY_NAME}_service.py" "Service file"
check_file "src/api_server/routers/${ENTITY_NAME}.py" "Router file"

echo ""
echo "2. Checking entity definition..."
echo "---------------------------------"

check_content "src/database/entities/${ENTITY_NAME}.py" "class ${ENTITY_NAME_UPPER}Entity" "Entity class definition"
check_content "src/database/entities/${ENTITY_NAME}.py" "__tablename__ = \"${ENTITY_NAME}\"" "Table name definition"
check_content "src/database/entities/${ENTITY_NAME}.py" "BaseAuditEntity" "BaseAuditEntity inheritance"

echo ""
echo "3. Checking Pydantic models..."
echo "-------------------------------"

check_content "src/models/${ENTITY_NAME}.py" "class ${ENTITY_NAME_UPPER}Create" "Create model"
check_content "src/models/${ENTITY_NAME}.py" "class ${ENTITY_NAME_UPPER}Update" "Update model"
check_content "src/models/${ENTITY_NAME}.py" "class ${ENTITY_NAME_UPPER}(" "Read model"

echo ""
echo "4. Checking mapper..."
echo "---------------------"

check_content "src/mappers/${ENTITY_NAME}.py" "def to_${ENTITY_NAME}_entity" "Mapper function"
check_content "src/mappers/${ENTITY_NAME}.py" "${ENTITY_NAME_UPPER}Entity" "Entity import in mapper"

echo ""
echo "5. Checking data service..."
echo "---------------------------"

check_content "src/data_services/${ENTITY_NAME}_data_service.py" "class ${ENTITY_NAME_UPPER}DataService" "Data service class"
check_content "src/data_services/${ENTITY_NAME}_data_service.py" "Crud\[${ENTITY_NAME_UPPER}Entity" "Crud inheritance"

echo ""
echo "6. Checking service..."
echo "----------------------"

check_content "src/services/${ENTITY_NAME}_service.py" "class ${ENTITY_NAME_UPPER}Service" "Service class"
check_content "src/services/${ENTITY_NAME}_service.py" "BaseService\[" "BaseService inheritance"
check_content "src/services/${ENTITY_NAME}_service.py" "model_class = ${ENTITY_NAME_UPPER}" "model_class attribute"

echo ""
echo "7. Checking router..."
echo "---------------------"

check_content "src/api_server/routers/${ENTITY_NAME}.py" "@router.get" "GET endpoints"
check_content "src/api_server/routers/${ENTITY_NAME}.py" "@router.post" "POST endpoint"
check_content "src/api_server/routers/${ENTITY_NAME}.py" "@router.patch" "PATCH endpoint"
check_content "src/api_server/routers/${ENTITY_NAME}.py" "@router.delete" "DELETE endpoint"

echo ""
echo "8. Checking dependencies registration..."
echo "-----------------------------------------"

check_content "src/api_server/deps.py" "def get_${ENTITY_NAME}_data_service" "Data service dependency"
check_content "src/api_server/deps.py" "def get_${ENTITY_NAME}_service" "Service dependency"
check_content "src/api_server/deps.py" "from src.data_services.${ENTITY_NAME}_data_service import ${ENTITY_NAME_UPPER}DataService" "Data service import"
check_content "src/api_server/deps.py" "from src.services.${ENTITY_NAME}_service import ${ENTITY_NAME_UPPER}Service" "Service import"

echo ""
echo "9. Checking router registration..."
echo "-----------------------------------"

check_content "src/api_server/main.py" "from src.api_server.routers import ${ENTITY_NAME}" "Router import"
check_content "src/api_server/main.py" "${ENTITY_NAME}.router" "Router registration"

echo ""
echo "10. Running code quality checks..."
echo "-----------------------------------"

# Check if uv is available
if command -v uv &> /dev/null; then
    echo "Running ruff format check..."
    if uv run ruff format --check "src/database/entities/${ENTITY_NAME}.py" "src/models/${ENTITY_NAME}.py" "src/mappers/${ENTITY_NAME}.py" "src/data_services/${ENTITY_NAME}_data_service.py" "src/services/${ENTITY_NAME}_service.py" "src/api_server/routers/${ENTITY_NAME}.py" 2>&1 | grep -q "Would reformat"; then
        echo -e "${YELLOW}⚠${NC} Files need formatting. Run: make pre_commit"
        ((WARNINGS++))
    else
        echo -e "${GREEN}✓${NC} All files are properly formatted"
    fi

    echo ""
    echo "Running ruff linter..."
    if uv run ruff check "src/database/entities/${ENTITY_NAME}.py" "src/models/${ENTITY_NAME}.py" "src/mappers/${ENTITY_NAME}.py" "src/data_services/${ENTITY_NAME}_data_service.py" "src/services/${ENTITY_NAME}_service.py" "src/api_server/routers/${ENTITY_NAME}.py" > /dev/null 2>&1; then
        echo -e "${GREEN}✓${NC} No linting errors found"
    else
        echo -e "${YELLOW}⚠${NC} Linting errors found. Run: make pre_commit"
        ((WARNINGS++))
    fi
else
    echo -e "${YELLOW}⚠${NC} uv not found, skipping code quality checks"
    ((WARNINGS++))
fi

echo ""
echo "=================================================="
echo "Validation complete!"
echo ""

if [ $ERRORS -eq 0 ] && [ $WARNINGS -eq 0 ]; then
    echo -e "${GREEN}✓ All checks passed!${NC}"
    echo ""
    echo "Next steps:"
    echo "1. Run: make db_migrate message=\"add_${ENTITY_NAME}\""
    echo "2. Run: make db_upgrade"
    echo "3. Run: make start"
    echo "4. Test endpoints at: http://localhost:5000/docs"
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
