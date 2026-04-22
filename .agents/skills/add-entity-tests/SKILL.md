# Add Entity Tests Skill

Generate comprehensive unit tests for an entity and all its layers (fixtures, mapper tests, service tests, router tests).

## What This Skill Does

Creates complete test coverage for an entity including:
1. Test fixtures (entity instances, create/update models, error results)
2. Mapper unit tests (model to entity transformation)
3. Service layer unit tests (get_page, get_by_id, create, update, delete)
4. Router layer unit tests (all endpoints with success and error cases)
5. Updates conftest.py with necessary fixture plugins

## Critical Patterns (Read Before Generating)

These patterns must be followed exactly — deviating causes test failures:

- `ModelList` uses `items` and `total` ONLY (NOT `data`, `total_count`, `page_number`, `page_size`)
- `ErrorStatus` uses `NOT_FOUND_ERROR` and `BAD_REQUEST` (NOT `NOT_FOUND`, `VALIDATION_ERROR`)
- `ErrorResult` uses `details` parameter (NOT `message`)
- Service fixtures must be defined in `conftest.py` with a real `session` (NOT a MagicMock)
- Mock `get_by_page` returning a tuple `([entities], count)` (NOT `get_page`)
- Filters use `field=EntityType.field_name` (NOT `field_name="string"`)
- Filter assertions check `filter.field == EntityType.field_name`
- Use explicit datetime values (NOT `datetime.now()`)
- All fixtures use `scope="session"` for performance
- Never use `**model_dump()` in fixtures — always assign fields explicitly

## Instructions

You are an assistant helping to create comprehensive unit tests for an entity in this FastAPI boilerplate.

### Step 1: Gather Entity Information

Ask the user:

**Question 1: Entity Name**
- Use the AskUserQuestion tool
- Header: "Entity Name"
- Question: "Which entity would you like to create tests for?"
- Provide 3-4 options based on entities found in `src/database/entities/` (or allow custom input)

**Question 2: Custom Filters**
- Ask in a regular message:
  "Does the entity's service layer have any custom query parameters (filters)?

  For example, Task has 'is_completed' and 'user_id' filters in the get_page method.

  Please list the filter names and their types (e.g., is_completed: bool, user_id: UUID).
  Type 'none' if there are no custom filters beyond standard pagination."

**Question 3: Unique Constraints**
- Ask in a regular message:
  "Does the entity have any unique constraints that should be tested?

  For example, User might have unique constraints on 'username' and 'email'.

  Please list the fields with unique constraints.
  Type 'none' if there are no unique constraints to test."

**Question 4: Additional Test Cases**
- Ask in a regular message:
  "Are there any additional custom test cases you'd like to include?

  For example:
  - Custom validation logic
  - Business rule edge cases
  - Relationship-specific tests

  Type 'none' if you only want standard CRUD test coverage."

### Step 2: Validate Input

Before proceeding, validate:
- Entity exists in `src/database/entities/{entity_name}.py`
- Models exist in `src/models/{entity_name}.py`
- Service exists in `src/services/{entity_name}_service.py`
- Router exists in `src/api_server/routers/{entity_name}.py`
- Entity name is in snake_case format

If any files are missing, inform the user and suggest running the "add-entity" skill first.

### Step 3: Read Existing Files

Read the following files to understand the entity structure:
1. Entity file: `src/database/entities/{entity_name}.py`
2. Models file: `src/models/{entity_name}.py`
3. Mapper file: `src/mappers/{entity_name}.py`
4. Service file: `src/services/{entity_name}_service.py`
5. Router file: `src/api_server/routers/{entity_name}.py`

Extract:
- Entity field names and types
- Create model fields (for fixtures)
- Update model fields (for fixtures)
- Mapper function name and field mappings
- Custom query parameters in service.get_page()
- Router endpoint patterns
- Foreign key relationships (if any)

### Step 4: Generate File Paths

Calculate the file paths:
- Fixtures: `src/tests/fixtures/{entity_name}_fixtures.py`
- Mapper tests: `src/tests/unit/mappers/test_{entity_name}_mapper.py`
- Service tests: `src/tests/unit/services/test_{entity_name}_service.py`
- Router tests: `src/tests/unit/routers/test_{entity_name}.py`

### Step 5: Create Test Files in Order

Use the templates in `template.md` to create files in this exact sequence:

1. **Fixtures File** (`src/tests/fixtures/{entity_name}_fixtures.py`)
   - UUID fixtures for entity ID (and user_id if entity has FK relationships)
   - Create model fixture with sample data
   - Update model fixture with sample data
   - Entity model fixture (read model) with explicit audit fields
   - Entity list fixture (ModelList)
   - Entity entity fixture (database entity)
   - Error result fixtures (not_found with simple message, already_exists if needed)
   - ProblemDetails fixtures for HTTP error responses
   - All fixtures use `scope="session"` for performance

2. **Mapper Tests File** (`src/tests/unit/mappers/test_{entity_name}_mapper.py`)
   - Test mapper function transforms create model to entity correctly
   - Test UUID is generated and not None
   - Test UUID uniqueness across multiple calls
   - Test all fields are mapped properly
   - Test audit fields are set correctly
   - Test foreign key fields are mapped (if entity has relationships) - separate test

3. **Service Tests File** (`src/tests/unit/services/test_{entity_name}_service.py`)
   - Test get_page with all filters (if any) - verify filter objects in detail
   - Test get_page without filters - verify empty filter list
   - Test get_page with partial filters (if multiple filters) - verify correct filters passed
   - Use `assert result == Ok(ModelList[...])` for result assertions
   - Additional custom service method tests (if any)

4. **Router Tests File** (`src/tests/unit/routers/test_{entity_name}.py`) — use Unit Test Style:
   - Call router functions directly by importing them
   - Pass service dependency as parameter using `mocker.patch.object(service_instance, "method", ...)`
   - Test GET list endpoint (success, with filters if any, validation error)
   - Test GET by ID endpoint (success, not found)
   - Test POST create endpoint (success, validation error, conflict if unique constraints)
   - Test PATCH update endpoint (success, not found, validation error, conflict if unique constraints)
   - Test DELETE endpoint (success, not found)

5. **Update conftest.py**
   - Add fixture plugin: `"src.tests.fixtures.{entity_name}_fixtures"`
   - Add `{entity_name}_data_service` fixture (real session, not mock)
   - Add `{entity_name}_service` fixture

See `template.md` for all code templates with placeholders.

See `examples/sample.md` for a complete Task entity example with all correct patterns.

### Step 6: Run Tests

After all files are created, run the tests:
```bash
PYTHONPATH=`pwd` uv run pytest src/tests/unit/mappers/test_{entity_name}_mapper.py -vv
PYTHONPATH=`pwd` uv run pytest src/tests/unit/services/test_{entity_name}_service.py -vv
PYTHONPATH=`pwd` uv run pytest src/tests/unit/routers/test_{entity_name}.py -vv
```

Or run all tests:
```bash
make test
```

### Step 7: Validate (Optional)

Run the validation script to check all files were created correctly:
```bash
bash .claude/skills/add-entity-tests/scripts/validate.sh {entity_name}
```

### Step 8: Summary

Provide a summary to the user:
- List all test files created
- Show test coverage statistics (number of tests per file)
- Show the command to run entity-specific tests
- Mention if any custom test cases were skipped and need manual implementation
- Suggest running `make test` to ensure all tests pass

## Important Notes

- Always use **snake_case** for: file names, function names, variable names, fixture names
- Always use **PascalCase** for: class names, model names
- Follow pytest conventions:
  - Test function names start with `test_`
  - Use descriptive test names: `test_{method}` for success, `test_{method}__{condition}` for errors
  - Use Arrange-Act-Assert pattern with comments
  - Use `mocker.patch.object()` for mocking dependencies
- All fixtures use `scope="session"` for performance (not `scope="module"`)
- Use `@pytest.mark.filterwarnings("ignore::UserWarning")` for intentional validation errors
- Router tests mock the service layer (not data service)
- Service tests mock the data service layer
- Unit-style router tests:
  - Call router functions directly
  - Pass dependencies as parameters
  - Verify with `assert result == expected` and `service.method.assert_called_once_with()`
  - Check HTTPException details in error cases
- All tests must have proper type hints for mypy compliance
- Test both success and failure paths for each endpoint/method

## Test Naming Conventions

- Success cases: `test_{method_name}`
- Error cases: `test_{method_name}__{error_condition}`
- Examples:
  - `test_get_tasks` - happy path
  - `test_get_tasks__validation_error` - bad query params
  - `test_get_task_by_id__task_not_found` - 404 case
  - `test_create_task__validation_error` - invalid payload
  - `test_update_task__conflict` - unique constraint violation

## Fixture Naming Conventions

- Entity ID: `{entity_name}_id`
- Create model: `{entity_name}_create`
- Update model: `{entity_name}_update`
- Read model: `{entity_name}`
- List of models: `{entity_name}s` (plural)
- Database entity: `{entity_name}_entity`
- Error results: `{entity_name}_error_result_{error_type}`
- Problem details: `{entity_name}_{error_type}` (e.g., `task_not_found`)

## Error Handling

If you encounter any errors during scaffolding:
1. Ensure the entity files exist (run add-entity skill first if needed)
2. Verify filters use `field=EntityType.field_name` (not `field_name="string"`)
3. Check that `ErrorResult` uses `details` (not `message`)
4. Check that `ErrorStatus` uses `NOT_FOUND_ERROR` / `BAD_REQUEST`
5. Verify `ModelList` uses `items` and `total` only
6. Confirm `get_by_page` is mocked (not `get_page`), returning `([entities], count)` tuple
7. Check service fixtures are defined in `conftest.py` with real `session`
8. Compare your implementation with `examples/sample.md` (Task entity canonical reference)