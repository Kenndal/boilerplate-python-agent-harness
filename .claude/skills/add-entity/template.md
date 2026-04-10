# Entity Scaffolding Templates

This file contains all code templates for scaffolding a new entity. Replace placeholders as follows:

- `{EntityName}` - PascalCase entity name (e.g., Product, OrderItem)
- `{entity_name}` - snake_case entity name (e.g., product, order_item)
- `{entity_name_plural}` - snake_case plural (e.g., products, order_items)
- `{table_name}` - lowercase snake_case table name (same as entity_name)
- `{fields}` - Entity field definitions
- `{create_fields}` - Pydantic Create model fields
- `{update_fields}` - Pydantic Update model fields
- `{field_mappings}` - Mapper field assignments
- `{query_params}` - Service method query parameters
- `{query_param_definitions}` - Router query parameter definitions
- `{query_param_args}` - Service method arguments for filters
- `{filter_logic}` - Filter building logic in service
- `{ENTITY_PREFIX}` - Constant name for entity prefix (e.g., PRODUCTS_PREFIX)

## 1. Entity File Template

### Without Relationships

**File:** `src/database/entities/{entity_name}.py`

```python
from uuid import UUID

from sqlalchemy.orm import Mapped, mapped_column

from src.database.entities.base import Base, BaseAuditEntity


class {EntityName}Entity(Base, BaseAuditEntity):
    __tablename__ = "{table_name}"

    id: Mapped[UUID] = mapped_column(primary_key=True, index=True)
    {fields}
```

### With Relationships

**File:** `src/database/entities/{entity_name}.py`

```python
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database.entities.base import Base, BaseAuditEntity

if TYPE_CHECKING:
    {relationship_imports}


class {EntityName}Entity(Base, BaseAuditEntity):
    __tablename__ = "{table_name}"

    id: Mapped[UUID] = mapped_column(primary_key=True, index=True)
    {fields}
    {foreign_key_fields}

    # Relationships
    {relationships}
```

**Relationship Notes:**
- **many-to-one**: Add foreign key field `{related_entity}_id: Mapped[UUID] = mapped_column(ForeignKey("{related_table}.id"))` and relationship `{related_entity}: Mapped["{RelatedEntity}Entity"] = relationship(back_populates="{entity_name_plural}")`
- **one-to-many**: Add relationship `{related_entity_plural}: Mapped[list["{RelatedEntity}Entity"]] = relationship(back_populates="{entity_name}")`
- **many-to-many**: Create association table and relationships (see SQLAlchemy docs)
- Use `{table_name}` as lowercase snake_case of entity name
- Generate fields from user input with appropriate `Mapped[]` type hints
- Add `unique=True, index=True` for fields that should be unique
- Add `index=True` for fields that will be frequently queried
- **IMPORTANT**: Always use `TYPE_CHECKING` to import related entities to avoid circular imports at runtime
  - Import related entity classes inside `if TYPE_CHECKING:` block
  - Use string literals (forward references) in `Mapped` type hints: `Mapped["RelatedEntity"]`
  - This pattern satisfies type checkers (mypy, ty) without causing circular import errors

## 1.5. Update Entity __init__.py Template

**CRITICAL:** This step MUST be completed before running database migrations. Alembic needs to import the entity to detect schema changes.

**File:** `src/database/entities/__init__.py`

Add import for the new entity:

```python
from src.database.entities.{entity_name} import {EntityName}Entity
```

Add entity to `__all__` export list:

```python
__all__ = ["Base", ..., "{EntityName}Entity"]
```

**Complete example after adding ProductEntity:**

```python
# flake8: noqa F401
from src.database.entities.base import Base
from src.database.entities.product import ProductEntity

__all__ = ["Base", "ProductEntity"]
```

**Notes:**
- Keep imports sorted alphabetically by module name
- Add the entity class name to `__all__` list in alphabetical order
- The `# flake8: noqa F401` comment suppresses "imported but unused" warnings (these imports are needed for Alembic)

## 2. Models File Template

### Without Relationships

**File:** `src/models/{entity_name}.py`

```python
from uuid import UUID

from pydantic import ConfigDict

from src.models.base import BaseAudit, BaseModelWithConfig


class {EntityName}Create(BaseModelWithConfig):
    {create_fields}


class {EntityName}Update(BaseModelWithConfig):
    {update_fields}


class {EntityName}({EntityName}Create, BaseAudit):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    is_active: bool
```

### With Relationships (Many-to-One)

**File:** `src/models/{entity_name}.py`

```python
from uuid import UUID

from pydantic import ConfigDict

from src.models.base import BaseAudit, BaseModelWithConfig
{relationship_model_imports}


class {EntityName}Create(BaseModelWithConfig):
    {create_fields}
    {foreign_key_id_fields}


class {EntityName}Update(BaseModelWithConfig):
    {update_fields}


class {EntityName}({EntityName}Create, BaseAudit):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    is_active: bool
    {nested_relationship_fields}
```

**Model Notes:**
- For **many-to-one**: Include foreign key UUID in Create model (e.g., `user_id: UUID`), optionally include nested related model in read model
- For **one-to-many**: Optionally include nested list in read model (e.g., `order_items: list[OrderItem] = []`)
- `{EntityName}Create`: All user-provided fields (required) + foreign key IDs
- `{EntityName}Update`: Only modifiable fields with defaults (e.g., `field: str = ""`)
- Always include `is_active: bool = True` in Update model
- Read model inherits from Create and BaseAudit

## 3. Mapper File Template

### Without Relationships

**File:** `src/mappers/{entity_name}.py`

```python
import uuid

from src.database.entities.{entity_name} import {EntityName}Entity
from src.models.{entity_name} import {EntityName}Create


def to_{entity_name}_entity(model: {EntityName}Create, user_id: str) -> {EntityName}Entity:
    return {EntityName}Entity(
        id=uuid.uuid4(),
        {field_mappings},
        is_active=True,
        created_by_user_id=user_id,
        last_modified_by_user_id=user_id,
    )
```

### With Relationships

**File:** `src/mappers/{entity_name}.py`

```python
import uuid

from src.database.entities.{entity_name} import {EntityName}Entity
from src.models.{entity_name} import {EntityName}Create


def to_{entity_name}_entity(model: {EntityName}Create, user_id: str) -> {EntityName}Entity:
    return {EntityName}Entity(
        id=uuid.uuid4(),
        {field_mappings},
        {foreign_key_mappings},
        is_active=True,
        created_by_user_id=user_id,
        last_modified_by_user_id=user_id,
    )
```

**Mapper Notes:**
- Map each field from `model.field_name` to entity
- For many-to-one relationships, map foreign key: `{related_entity}_id=model.{related_entity}_id`
- Always set `is_active=True` for new entities
- Set both `created_by_user_id` and `last_modified_by_user_id` to `user_id`

## 4. Data Service File Template

**File:** `src/data_services/{entity_name}_data_service.py`

```python
from sqlalchemy.orm import Session

from src.data_services.crud import Crud
from src.database.entities.{entity_name} import {EntityName}Entity
from src.models.{entity_name} import {EntityName}Create, {EntityName}Update


class {EntityName}DataService(Crud[{EntityName}Entity, {EntityName}Create, {EntityName}Update]):
    def __init__(self, session: Session) -> None:
        super().__init__(
            session=session,
            entity_type={EntityName}Entity,
        )
```

## 5. Service File Template

**File:** `src/services/{entity_name}_service.py`

```python
from result import Result

from src.data_services.filters import EqualsFilter
from src.data_services.{entity_name}_data_service import {EntityName}DataService
from src.database.entities.{entity_name} import {EntityName}Entity
from src.models.base import ModelList
from src.models.enums.sort_direction import SortDirection
from src.models.error_result import ErrorResult
from src.models.{entity_name} import {EntityName}, {EntityName}Create, {EntityName}Update
from src.services.base_service import BaseService


class {EntityName}Service(BaseService[{EntityName}Entity, {EntityName}, {EntityName}Create, {EntityName}Update]):
    data_service: {EntityName}DataService
    CREATE_UNIQUE_VALIDATION_MSG = "{model_class} with given {unique_fields} already exists"
    UPDATE_UNIQUE_VALIDATION_MSG = "{model_class} with given {unique_fields} already exists"
    model_class = {EntityName}

    def get_page(
        self,
        page_number: int,
        page_size: int,
        omit_pagination: bool,
        {query_params},
        sort_by: str | None = None,
        sort_direction: SortDirection = SortDirection.ascending,
    ) -> Result[ModelList[{EntityName}], ErrorResult]:
        filters = []
        {filter_logic}

        return super().get_page(
            page_number=page_number,
            page_size=page_size,
            omit_pagination=omit_pagination,
            filters=filters,
            sort_by=sort_by,
            sort_direction=sort_direction,
        )
```

**Service Notes:**
- Add query parameters from user input as optional parameters with `| None = None` type hints
- Build filters using `EqualsFilter` for each query parameter (if not None)
- Update unique validation messages based on unique fields
- For relationships, consider adding filter support for foreign key IDs

## 6. Router File Template

### Router Without Unique Constraints

**File:** `src/api_server/routers/{entity_name}.py`

Use this template when the entity has **NO unique constraints** (no fields with `unique=True`):

```python
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from result import Err, Ok
from starlette.status import HTTP_201_CREATED, HTTP_204_NO_CONTENT

from src.api_server.deps import get_{entity_name}_service
from src.api_server.helpers.error_response import http_exception_from_error
from src.api_server.responses import response_404
from src.constants import (
    DEFAULT_PAGE_NUMBER,
    DEFAULT_PAGE_SIZE,
    OMIT_PAGINATION,
    PAGE_NUMBER,
    PAGE_SIZE,
    SORT_BY,
    SORT_DIRECTION,
    {ENTITY_PREFIX},
)
from src.mappers.{entity_name} import to_{entity_name}_entity
from src.models.base import ModelList
from src.models.enums.sort_direction import SortDirection
from src.models.{entity_name} import {EntityName}, {EntityName}Create, {EntityName}Update
from src.services.{entity_name}_service import {EntityName}Service

router = APIRouter(prefix=f"/{{{ENTITY_PREFIX}}}")


@router.get("/", response_model=ModelList[{EntityName}])
def get_{entity_name_plural}(
    page_number: int = Query(default=DEFAULT_PAGE_NUMBER, alias=PAGE_NUMBER, gt=0),
    page_size: int = Query(default=DEFAULT_PAGE_SIZE, alias=PAGE_SIZE, gt=0),
    omit_pagination: bool = Query(default=False, alias=OMIT_PAGINATION),
    {query_param_definitions},
    sort_by: str | None = Query(default=None, alias=SORT_BY),
    sort_direction: SortDirection = Query(default=SortDirection.ascending, alias=SORT_DIRECTION),
    {entity_name}_service: {EntityName}Service = Depends(get_{entity_name}_service),
) -> ModelList[{EntityName}]:
    match {entity_name}_service.get_page(page_number, page_size, omit_pagination, {query_param_args}, sort_by, sort_direction):
        case Ok(result):
            return result
        case Err(error):
            raise http_exception_from_error(error)
        case _:
            raise http_exception_from_error()


@router.get("/{{{entity_name}_id}}", response_model={EntityName}, responses=response_404)
def get_{entity_name}_by_id({entity_name}_id: UUID, {entity_name}_service: {EntityName}Service = Depends(get_{entity_name}_service)) -> {EntityName}:
    match {entity_name}_service.get_by_id({entity_name}_id):
        case Ok(result):
            return result
        case Err(error):
            raise http_exception_from_error(error)
        case _:
            raise http_exception_from_error()


@router.post("/", response_model={EntityName}, status_code=HTTP_201_CREATED)
def create_{entity_name}(
    {entity_name}: {EntityName}Create,
    {entity_name}_service: {EntityName}Service = Depends(get_{entity_name}_service),
    # Note: In real implementation, you would get user_id from authentication context
    current_user_id: str = "system",  # Placeholder for actual user authentication
) -> {EntityName}:
    match {entity_name}_service.create({entity_name}, to_{entity_name}_entity, current_user_id):  # ty: ignore[invalid-argument-type]
        case Ok(result):
            return result
        case Err(error):
            raise http_exception_from_error(error)
        case _:
            raise http_exception_from_error()


@router.patch("/{{{entity_name}_id}}", response_model={EntityName}, responses=response_404)
def update_{entity_name}(
    {entity_name}_id: UUID,
    {entity_name}: {EntityName}Update,
    {entity_name}_service: {EntityName}Service = Depends(get_{entity_name}_service),
    # Note: In real implementation, you would get user_id from authentication context
    current_user_id: str = "system",  # Placeholder for actual user authentication
) -> {EntityName}:
    match {entity_name}_service.update({entity_name}_id, {entity_name}, current_user_id):
        case Ok(result):
            return result
        case Err(error):
            raise http_exception_from_error(error)
        case _:
            raise http_exception_from_error()


@router.delete("/{{{entity_name}_id}}", status_code=HTTP_204_NO_CONTENT, responses=response_404)
def delete_{entity_name}({entity_name}_id: UUID, {entity_name}_service: {EntityName}Service = Depends(get_{entity_name}_service)) -> None:
    match {entity_name}_service.delete({entity_name}_id):
        case Err(error):
            raise http_exception_from_error(error)
```

### Router With Unique Constraints

**File:** `src/api_server/routers/{entity_name}.py`

Use this template when the entity has **unique constraints** (fields with `unique=True`):

Change the import to include both response_404 and response_409:
```python
from src.api_server.responses import response_404, response_409
```

Update these endpoints:

```python
@router.post("/", response_model={EntityName}, status_code=HTTP_201_CREATED, responses=response_409)
def create_{entity_name}(
    {entity_name}: {EntityName}Create,
    {entity_name}_service: {EntityName}Service = Depends(get_{entity_name}_service),
    current_user_id: str = "system",
) -> {EntityName}:
    match {entity_name}_service.create({entity_name}, to_{entity_name}_entity, current_user_id):  # ty: ignore[invalid-argument-type]
        case Ok(result):
            return result
        case Err(error):
            raise http_exception_from_error(error)
        case _:
            raise http_exception_from_error()


@router.patch("/{{{entity_name}_id}}", response_model={EntityName}, responses=response_404 | response_409)
def update_{entity_name}(
    {entity_name}_id: UUID,
    {entity_name}: {EntityName}Update,
    {entity_name}_service: {EntityName}Service = Depends(get_{entity_name}_service),
    current_user_id: str = "system",
) -> {EntityName}:
    match {entity_name}_service.update({entity_name}_id, {entity_name}, current_user_id):
        case Ok(result):
            return result
        case Err(error):
            raise http_exception_from_error(error)
        case _:
            raise http_exception_from_error()
```

**Router Notes:**
- Use proper pluralization for list endpoint function name (ask user if unclear)
- Add query parameters from user input with appropriate Query() definitions
- All router parameters use snake_case
- **CRITICAL**: Set `responses` parameter correctly based on entity constraints and service method behavior:
  - **GET list** (`get_page`) - No special responses needed (empty list is valid)
  - **GET by ID** (`get_by_id`) - Always use `responses=response_404` (can return 404 if not found)
  - **POST** (`create`) - Use `responses=response_409` ONLY if entity has unique constraints
  - **PATCH** (`update`) - Use `responses=response_404` if no unique constraints, or `responses=response_404 | response_409` if unique constraints exist
  - **DELETE** (`delete`) - Always use `responses=response_404` (can return 404 if not found)
- Check entity definition for `unique=True` on any fields to determine if 409 responses are needed
- Import only the response helpers you need: `response_404` always, `response_409` only if unique constraints exist

## 8. Update Dependencies Template

**File:** `src/api_server/deps.py`

Add to the end of the file:

```python


def get_{entity_name}_data_service(db_session: Session = Depends(get_db)) -> {EntityName}DataService:
    return {EntityName}DataService(session=db_session)


def get_{entity_name}_service({entity_name}_data_service: {EntityName}DataService = Depends(get_{entity_name}_data_service)) -> {EntityName}Service:
    return {EntityName}Service(data_service={entity_name}_data_service)
```

Add imports at the top:

```python
from src.data_services.{entity_name}_data_service import {EntityName}DataService
from src.services.{entity_name}_service import {EntityName}Service
```

## 9. Update Constants Template

**File:** `src/constants/__init__.py`

Add the entity prefix constant:

```python
{ENTITY_PREFIX} = "{entity_name_plural}"
```

## 10. Register Router Template

**File:** `src/api_server/main.py`

Add import after existing router imports:

```python
from src.api_server.routers import {entity_name}
```

Add router registration in `build_app()` function after existing routers:

```python
    _app.include_router({entity_name}.router, tags=["{entity_name_plural}"], prefix=f"/{VERSION_PREFIX}")
```
