# Add Entity Tests Skill

A Claude Code skill for generating comprehensive unit tests for FastAPI entities.

## Important: Read CORRECTIONS.md First

**Before using this skill, read `CORRECTIONS.md` for common patterns and errors to avoid.**

The Task entity tests (`src/tests/{fixtures,unit}/task*`) serve as the canonical reference implementation. When in doubt, follow those patterns exactly.

## What It Does

This skill automatically generates complete test coverage for an entity including:

- **Test Fixtures**: Reusable test data (create/update models, entities, error fixtures)
- **Mapper Tests**: Unit tests for model to entity transformation
- **Service Tests**: Unit tests for service layer methods (get_page with/without filters)
- **Router Tests**: Integration tests for all API endpoints (GET, POST, PATCH, DELETE)
- **Error Cases**: Tests for validation errors, not found, and conflict scenarios

## Prerequisites

The entity must already exist with the following files:
- `src/database/entities/{entity_name}.py`
- `src/models/{entity_name}.py`
- `src/mappers/{entity_name}.py`
- `src/services/{entity_name}_service.py`
- `src/api_server/routers/{entity_name}.py`

If the entity doesn't exist yet, use the `add-entity` skill first.

## Usage

1. **Invoke the skill** (in Claude Code):
   ```
   Can you run the add-entity-tests skill for the Product entity?
   ```

2. **Answer the prompts**:
   - Entity name (e.g., "product")
   - Custom filters/query parameters (e.g., "is_active: bool")
   - Unique constraints (e.g., "username, email")
   - Additional custom test cases (optional)

3. **Review generated files**:
   - `src/tests/fixtures/{entity_name}_fixtures.py`
   - `src/tests/unit/mappers/test_{entity_name}_mapper.py`
   - `src/tests/unit/services/test_{entity_name}_service.py`
   - `src/tests/unit/routers/test_{entity_name}.py`

4. **Run validation** (optional):
   ```bash
   bash .claude/skills/add-entity-tests/scripts/validate.sh product
   ```

5. **Run tests**:
   ```bash
   PYTHONPATH=`pwd` uv run pytest src/tests/unit/mappers/test_product_mapper.py -vv
   PYTHONPATH=`pwd` uv run pytest src/tests/unit/services/test_product_service.py -vv
   PYTHONPATH=`pwd` uv run pytest src/tests/unit/routers/test_product.py -vv
   ```

   Or run all tests:
   ```bash
   make test
   ```

## Example

For a User entity with:
- Fields: `first_name`, `last_name`, `username`, `email`
- Filter: `is_active: bool`
- Unique: `username`, `email`

The skill generates:
- 10 fixtures (user_id, user_create, user_update, user, users, user_entity, error fixtures)
- 1 mapper test (model to entity transformation)
- 2 service tests (with/without is_active filter)
- 10 router tests (success and error cases for all endpoints)

## Test Coverage

### Mapper Layer Tests
- ✓ Model to entity transformation
- ✓ UUID generation
- ✓ Field mapping validation
- ✓ Audit fields (created_by_user_id, last_modified_by_user_id, is_active)

### Service Layer Tests
- ✓ `get_page` with custom filters
- ✓ `get_page` without filters
- ✓ Custom service methods (if specified)

### Router Layer Tests
- ✓ GET list - success
- ✓ GET list - validation error
- ✓ GET by ID - success
- ✓ GET by ID - not found
- ✓ POST create - success
- ✓ POST create - validation error
- ✓ POST create - conflict (if unique constraints)
- ✓ PATCH update - success
- ✓ PATCH update - not found
- ✓ PATCH update - validation error
- ✓ PATCH update - conflict (if unique constraints)
- ✓ DELETE - success
- ✓ DELETE - not found

## File Structure

```
.claude/skills/add-entity-tests/
├── SKILL.md                    # Main skill instructions
├── CORRECTIONS.md              # Common errors and corrections (READ THIS FIRST!)
├── template.md                 # Code templates
├── examples/
│   └── sample.md              # Complete User entity example
├── scripts/
│   └── validate.sh            # Validation script
└── README.md                  # This file
```

## Common Patterns (from CORRECTIONS.md)

**Critical patterns to follow** (see CORRECTIONS.md for full details):

1. **ModelList**: Use `items` and `total` ONLY
   ```python
   ModelList[Task](items=[task], total=1)  # ✓ CORRECT
   ModelList[Task](data=[task], total_count=1)  # ✗ WRONG
   ```

2. **ErrorStatus**: Use correct enum values
   ```python
   ErrorStatus.NOT_FOUND_ERROR  # ✓ CORRECT
   ErrorStatus.NOT_FOUND  # ✗ WRONG
   ```

3. **ErrorResult**: Use `details` parameter
   ```python
   ErrorResult(status=..., details="...")  # ✓ CORRECT
   ErrorResult(status=..., message="...")  # ✗ WRONG
   ```

4. **Data Service**: Mock `get_by_page` returning tuple
   ```python
   mocker.patch.object(DataService, "get_by_page", return_value=([entity], 1))  # ✓ CORRECT
   mock.get_page.return_value = Ok([entity])  # ✗ WRONG
   ```

5. **Filters**: Use entity field objects, not strings
   ```python
   EqualsFilter(field=TaskEntity.is_completed, value=True)  # ✓ CORRECT
   EqualsFilter(field_name="is_completed", value=True)  # ✗ WRONG
   ```

**See CORRECTIONS.md for complete list and examples.**

## Tips

1. **Run after creating an entity**: Use this skill immediately after the `add-entity` skill
2. **Customize fixtures**: Adjust sample data in fixtures to match your domain
3. **Add custom tests**: Extend generated tests with business logic validations
4. **Keep tests updated**: Re-run when entity structure changes
5. **Run pre-commit**: Ensure generated code passes linting and type checking

## Validation Script

The validation script checks:
- ✓ All test files exist
- ✓ Required fixtures are present
- ✓ Mapper tests exist and validate transformations
- ✓ Service tests exist
- ✓ Router tests cover all endpoints
- ✓ conftest.py is updated
- ✓ Code passes ruff format/lint
- ✓ Code passes mypy type checking
- ✓ Tests execute successfully

Run it after generating tests:
```bash
bash .claude/skills/add-entity-tests/scripts/validate.sh <entity_name>
```

## Troubleshooting

**Error: Tests failing during generation**
1. **FIRST**: Check `CORRECTIONS.md` for the exact error pattern
2. Compare your code with Task entity tests (canonical reference)
3. Verify you're using correct patterns (ModelList fields, ErrorStatus enums, etc.)
4. Check that filter usage follows `field=EntityType.field_name` pattern

**Error: Entity files not found**
- Run the `add-entity` skill first to create the entity

**Error: AttributeError about 'get_page' vs 'get_by_page'**
- Use `get_by_page` (the correct method name)
- See CORRECTIONS.md section 5

**Error: ValidationError about ModelList fields**
- Use `items` and `total` only (not `data`, `total_count`, etc.)
- See CORRECTIONS.md section 1

**Error: Filter initialization errors**
- Use `field=EntityType.field_name` not `field_name="string"`
- See CORRECTIONS.md sections 6-7

**Error: ErrorResult errors**
- Use `details` not `message`
- Use `ErrorStatus.NOT_FOUND_ERROR` not `ErrorStatus.NOT_FOUND`
- See CORRECTIONS.md sections 2-3

**Error: Type checking fails**
- Ensure all fixtures have proper type hints
- Check that entity fields match between files
- Verify service fixtures are in conftest.py

**Warning: Linting errors**
- Run `make pre_commit` to auto-fix most issues
- Manually fix any remaining issues

## Related Skills

- `add-entity`: Create a new entity with all layers
