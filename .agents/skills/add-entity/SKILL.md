# Add Entity Skill

Scaffold a new entity following the layered FastAPI architecture pattern.

## What This Skill Does

Creates a complete CRUD entity with all required layers:
1. Database Entity (SQLAlchemy)
2. Pydantic Models (Create, Update, Read)
3. Mapper Function
4. Data Service
5. Business Service
6. API Router
7. Dependency Providers
8. Database Migration

## Instructions

You are an assistant helping to scaffold a new entity in this FastAPI boilerplate following strict layered architecture.

### Step 1: Gather Entity Information

Ask the user these questions:

**Question 1: Entity Name**
- Use the AskUserQuestion tool
- Header: "Entity Name"
- Question: "What is the name of the entity you want to create? (e.g., Product, Order, Category)"
- Provide 3-4 common examples as options with descriptions

**Question 2: Entity Fields**
- Ask in a regular message (cannot use AskUserQuestion):
  "Please provide the fields for the {EntityName} entity in the following format:

  field_name: type (options: str, int, float, bool, UUID, datetime)

  Example:
  - name: str
  - price: float
  - quantity: int
  - is_available: bool

  Note: The following fields are automatically added by BaseAuditEntity and should NOT be included:
  - id (UUID, primary key)
  - created_date (datetime)
  - last_modified_date (datetime)
  - created_by_user_id (str)
  - last_modified_by_user_id (str)
  - is_active (bool)"

**Question 3: Relationships**
- Ask in a regular message:
  "Does this entity have any relationships with other tables in the database?

  If yes, please specify the relationships in the following format:
  - relationship_type: entity_name (options: many-to-one, one-to-many, many-to-many)

  Examples:
  - many-to-one: User (an Order belongs to one User)
  - one-to-many: OrderItem (an Order has many OrderItems)
  - many-to-many: Tag (a Product has many Tags, a Tag has many Products)

  Type 'none' if there are no relationships."

**Question 4: Query Parameters**
- Ask in a regular message:
  "What query parameters (filters) should the GET list endpoint support?

  Example for User entity: is_active (bool)

  Please list the field names that should be filterable. Each will create an optional query parameter.
  Type 'none' if no additional filters are needed beyond the standard pagination parameters."

**Question 5: Unique Constraints**
- Ask in a regular message:
  "Which fields should have unique constraints (if any)?

  Fields with unique constraints must have unique values across all rows in the database table.

  Examples:
  - User entity: username, email (both must be unique)
  - Product entity: sku, barcode (both must be unique)
  - Task entity: none (no unique constraints)

  Please list the field names that should be unique, or type 'none' if no fields need unique constraints."

**Question 6: Modifiable Fields in PATCH**
- Ask in a regular message:
  "Which fields should be modifiable in the PATCH (update) endpoint?

  Please list the field names. Note:
  - All fields in the Update model default to empty string ('') or appropriate default
  - is_active is automatically included
  - Do NOT include: id, created_date, created_by_user_id

  Example: first_name, last_name, username, email"

### Step 2: Validate Input

Before proceeding, validate:
- Entity name is in PascalCase format (convert if needed)
- All field types are valid SQLAlchemy/Pydantic types
- No reserved fields are included (id, created_date, etc.)
- At least one field is specified for the entity
- Relationship types are valid (many-to-one, one-to-many, many-to-many)
- Referenced entities exist in the codebase
- Unique constraint fields are valid field names from the entity

### Step 3: Generate File Paths

Calculate the file paths (use snake_case for file names):
- Entity: `src/database/entities/{entity_name}.py`
- Models: `src/models/{entity_name}.py`
- Mapper: `src/mappers/{entity_name}.py`
- Data Service: `src/data_services/{entity_name}_data_service.py`
- Service: `src/services/{entity_name}_service.py`
- Router: `src/api_server/routers/{entity_name}.py`

### Step 4: Create Files in Order

Use the templates in `template.md` to create files in this exact sequence:

1. Entity File (`src/database/entities/{entity_name}.py`)
   - Add `unique=True, index=True` to fields that should have unique constraints
   - Add `index=True` to foreign key fields for query performance
2. Update Entity Module (`src/database/entities/__init__.py`) - **REQUIRED for Alembic migrations**
3. Models File (`src/models/{entity_name}.py`)
4. Mapper File (`src/mappers/{entity_name}.py`)
5. Data Service File (`src/data_services/{entity_name}_data_service.py`)
6. Service File (`src/services/{entity_name}_service.py`)
7. Router File (`src/api_server/routers/{entity_name}.py`)
   - **IMPORTANT**: Set `responses` parameter correctly based on unique constraints:
     - If entity has NO unique constraints: Import `response_404` only
       - GET by ID: `responses=response_404`
       - POST: No responses parameter
       - PATCH: `responses=response_404`
       - DELETE: `responses=response_404`
     - If entity HAS unique constraints: Import `response_404, response_409`
       - GET by ID: `responses=response_404`
       - POST: `responses=response_409`
       - PATCH: `responses=response_404 | response_409`
       - DELETE: `responses=response_404`
8. Update Dependencies (`src/api_server/deps.py`)
9. Update Constants (`src/constants/__init__.py`)
10. Register Router (`src/api_server/main.py`)

See `template.md` for all code templates with placeholders.

**CRITICAL:** Step 2 (updating `src/database/entities/__init__.py`) MUST be completed before running database migrations in Step 6. Alembic needs to be able to import the new entity to detect schema changes.

See `examples/sample.md` for a complete example of a Product entity.

### Step 5: Update Related Entities (if relationships exist)

If the new entity has relationships with existing entities, you may need to update those entities to add the back-reference relationships.

For example, if creating an Order entity with `many-to-one: User`, you should update `UserEntity` to add:

1. Add `TYPE_CHECKING` import at the top (if not already present):
```python
from typing import TYPE_CHECKING
```

2. Add the related entity import inside `TYPE_CHECKING` block:
```python
if TYPE_CHECKING:
    from src.database.entities.order import OrderEntity
```

3. Add `relationship` import (if not already present):
```python
from sqlalchemy.orm import relationship
```

4. Add the back-reference relationship in the entity class:
```python
orders: Mapped[list["OrderEntity"]] = relationship(back_populates="user")
```

**IMPORTANT**: Always use `TYPE_CHECKING` and string forward references to avoid circular import errors at runtime while maintaining proper type checking.

Ask the user if they want to update the related entities with back-references.

### Step 6: Generate Database Migration

After all files are created, run:
```bash
make db_migrate message="add_{entity_name}"
make db_upgrade
```

### Step 7: Validate (Optional)

Run the validation script to check all files were created correctly:
```bash
bash .claude/skills/add-entity/scripts/validate.sh {entity_name}
```

### Step 8: Summary

Provide a summary to the user:
- List all files created
- Show the API endpoints that are now available (GET list, GET by id, POST, PATCH, DELETE)
- List any relationships configured
- Mention if related entities need manual updates for back-references
- Remind them to run `make start` to rebuild the container with the new entity
- Suggest testing the endpoints using the Swagger UI at http://localhost:5000/

## Important Notes

- Always use **snake_case** for: file names, function names, variable names, database table names
- Always use **PascalCase** for: class names, entity names
- Always use **camelCase** for: API endpoint query parameters (aliased from snake_case)
- Follow the exact layer order: Entity → Models → Mapper → Data Service → Service → Router → Dependencies
- Never skip the dependency injection pattern
- All entities must extend `Base` and `BaseAuditEntity`
- All services must extend `BaseService` with proper generic types
- Always include proper type hints for mypy compliance
- Use `Result[T, ErrorResult]` pattern for service methods
- Use pattern matching (`match/case`) in routers for Result handling
- For relationships, use `relationship()` with `back_populates` parameter
- Foreign keys should reference the table name and column (e.g., `ForeignKey("user.id")`)
- **CRITICAL**: Always use `TYPE_CHECKING` to import related entities in entity files to avoid circular imports
  - Import related entities inside `if TYPE_CHECKING:` block
  - Use string forward references in type hints: `Mapped["RelatedEntity"]`
  - This pattern prevents circular import errors at runtime while maintaining type safety
- **CRITICAL**: Set endpoint `responses` parameter correctly based on entity constraints and service behavior:
  - Check if entity has unique constraints (`unique=True` on any fields)
  - GET by ID always returns 404 if not found: `responses=response_404`
  - POST returns 409 conflict ONLY if entity has unique constraints: `responses=response_409`
  - PATCH returns 404 if not found, and 409 ONLY if entity has unique constraints: `responses=response_404` or `responses=response_404 | response_409`
  - DELETE always returns 404 if not found: `responses=response_404`
  - GET list never needs special responses (empty list is valid)
  - Import only the response helpers you need from `src.api_server.responses`

## Error Handling

If you encounter any errors during scaffolding:
1. Read the error message carefully
2. Check if the issue is with imports (ensure correct paths)
3. Verify all type hints are correct
4. Check for typos in entity/field names
5. Ensure proper indentation (4 spaces)
6. For relationship errors, verify the related entity exists and table names match
