# Entity Test Templates

This file contains all code templates for generating entity tests. Replace placeholders as follows:

- `{EntityName}` - PascalCase entity name (e.g., Product, OrderItem)
- `{entity_name}` - snake_case entity name (e.g., product, order_item)
- `{entity_name_plural}` - snake_case plural (e.g., products, order_items)
- `{ENTITY_PREFIX}` - Constant name for entity prefix (e.g., PRODUCTS_PREFIX)
- `{fields}` - Entity field definitions for fixtures
- `{create_fields}` - Sample data for Create model fixture
- `{update_fields}` - Sample data for Update model fixture
- `{query_params}` - Custom query parameters/filters
- `{filter_test_name}` - Test name for filter (e.g., with_is_active_filter)
- `{filter_args}` - Filter arguments for service.get_page()

## 1. Fixtures File Template

**File:** `src/tests/fixtures/{entity_name}_fixtures.py`

```python
import uuid
from datetime import datetime, timezone

import pytest

from src.database.entities.{entity_name} import {EntityName}Entity
from src.models.base import ModelList
from src.models.enums.error_status import ErrorStatus
from src.models.error_result import ErrorResult
from src.models.problem_details import ProblemDetails
from src.models.{entity_name} import {EntityName}, {EntityName}Create, {EntityName}Update


@pytest.fixture(scope="session")
def {entity_name}_id() -> uuid.UUID:
    return uuid.uuid4()


{foreign_key_fixtures}


@pytest.fixture(scope="session")
def {entity_name}_create({foreign_key_params}) -> {EntityName}Create:
    return {EntityName}Create(
        {create_fields}
    )


@pytest.fixture(scope="session")
def {entity_name}_update() -> {EntityName}Update:
    return {EntityName}Update(
        {update_fields}
    )


@pytest.fixture(scope="session")
def {entity_name}({entity_name}_id: uuid.UUID, {foreign_key_params}) -> {EntityName}:
    return {EntityName}(
        id={entity_name}_id,
        {explicit_fields}
        is_active=True,
        created_date=datetime(2024, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
        last_modified_date=datetime(2024, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
        created_by_user_id=str({first_fk_id}),
        last_modified_by_user_id=str({first_fk_id}),
    )


@pytest.fixture(scope="session")
def {entity_name}s({entity_name}: {EntityName}) -> ModelList[{EntityName}]:
    return ModelList(
        items=[{entity_name}],
        total=1,
    )


@pytest.fixture(scope="session")
def {entity_name}_entity({entity_name}_id: uuid.UUID, {foreign_key_params}) -> {EntityName}Entity:
    return {EntityName}Entity(
        id={entity_name}_id,
        {explicit_fields}
        is_active=True,
        created_date=datetime.now(timezone.utc),
        last_modified_date=datetime.now(timezone.utc),
        created_by_user_id=str({first_fk_id}),
        last_modified_by_user_id=str({first_fk_id}),
    )


@pytest.fixture(scope="session")
def {entity_name}_error_result_not_found() -> ErrorResult:
    return ErrorResult(
        status=ErrorStatus.NOT_FOUND_ERROR,
        details="{EntityName} not found",
    )


@pytest.fixture(scope="session")
def {entity_name}_not_found({entity_name}_error_result_not_found: ErrorResult) -> ProblemDetails:
    return ProblemDetails(
        type="about:blank",
        title="Not Found",
        status=404,
        detail={entity_name}_error_result_not_found.details,
        instance="string",
    )
```

**Fixture Notes:**
- All fixtures use `scope="session"` for performance (NOT `scope="module"`)
- Generate sample data for create/update fixtures based on entity fields
- For string fields: use realistic sample data (e.g., "Sample Task", "sample@example.com")
- For numeric fields: use simple values (e.g., 100, 10.5)
- For boolean fields: use False for create, True for update (or vice versa)
- For UUID foreign keys: create separate fixtures (e.g., `user_id`) and reference them
- For datetime fields: use `datetime.now(timezone.utc)` explicitly in fixtures
- For audit fields: set explicitly in fixtures (created_date, last_modified_date, created_by_user_id, last_modified_by_user_id)
- Keep create fixture data different from update fixture data for test clarity
- Error messages should be simple (e.g., "Task not found" not "Task with id {id} not found")
- ProblemDetails should include `type="about:blank"` and `instance="string"`

**Placeholder Replacements:**
- `{foreign_key_fixtures}`: If entity has FK relationships, add fixtures like:
  ```python
  @pytest.fixture(scope="session")
  def user_id() -> uuid.UUID:
      return uuid.uuid4()
  ```
- `{foreign_key_params}`: If entity has FK, add params like `user_id: uuid.UUID`
- `{explicit_fields}`: List all entity fields explicitly (don't use **model_dump())
- `{first_fk_id}`: Use the first foreign key ID fixture for audit fields (e.g., `user_id`)

## 2. Mapper Tests File Template

**File:** `src/tests/unit/mappers/test_{entity_name}_mapper.py`

```python
import uuid

from src.mappers.{entity_name} import to_{entity_name}_entity
from src.models.{entity_name} import {EntityName}Create


def test_to_{entity_name}_entity({entity_name}_create: {EntityName}Create) -> None:
    # Arrange
    user_id = str(uuid.uuid4())

    # Act
    result = to_{entity_name}_entity({entity_name}_create, user_id)

    # Assert
    assert result.id is not None
    assert isinstance(result.id, uuid.UUID)
    {field_assertions}
    assert result.is_active is True
    assert result.created_by_user_id == user_id
    assert result.last_modified_by_user_id == user_id


def test_to_{entity_name}_entity__generates_unique_id({entity_name}_create: {EntityName}Create) -> None:
    # Arrange
    user_id = str(uuid.uuid4())

    # Act
    result1 = to_{entity_name}_entity({entity_name}_create, user_id)
    result2 = to_{entity_name}_entity({entity_name}_create, user_id)

    # Assert
    assert result1.id != result2.id
```

### Add This Test Only If Entity Has Foreign Keys

```python
def test_to_{entity_name}_entity__maps_foreign_key({entity_name}_create: {EntityName}Create) -> None:
    # Arrange
    user_id = str(uuid.uuid4())

    # Act
    result = to_{entity_name}_entity({entity_name}_create, user_id)

    # Assert
    {foreign_key_assertions}
```

**Mapper Test Notes:**
- **Three tests**: basic mapping, UUID uniqueness, foreign key mapping (if applicable)
- `{field_assertions}` should check each field: `assert result.field_name == {entity_name}_create.field_name`
- `{foreign_key_assertions}` should check FK fields and types:
  ```python
  assert result.{related_entity}_id == {entity_name}_create.{related_entity}_id
  assert isinstance(result.{related_entity}_id, uuid.UUID)
  ```
- Always verify UUID is generated (not None) and is correct type
- Test UUID uniqueness with multiple calls
- Always verify audit fields are set correctly
- Use `user_id = str(uuid.uuid4())` in Arrange section (NOT fixture)
- No need to mock anything - mapper is a pure transformation function
- Import `uuid` module (not `from uuid import UUID`)

## 3. Service Tests File Template

**File:** `src/tests/unit/services/test_{entity_name}_service.py`

### With Custom Filters (e.g., is_active, is_completed)

```python
from pytest_mock import MockerFixture
from result import Ok

from src.data_services.filters import EqualsFilter
from src.data_services.{entity_name}_data_service import {EntityName}DataService
from src.database.entities.{entity_name} import {EntityName}Entity
from src.models.base import ModelList
from src.models.enums.sort_direction import SortDirection
from src.models.{entity_name} import {EntityName}
from src.services.{entity_name}_service import {EntityName}Service


def test_get_page_with_filters(
    {entity_name}_service: {EntityName}Service,
    {entity_name}_entity: {EntityName}Entity,
    {entity_name}: {EntityName},
    mocker: MockerFixture,
) -> None:
    # Arrange
    mocker.patch.object(
        {EntityName}DataService,
        "get_by_page",
        return_value=([{entity_name}_entity], 1),
    )

    # Act
    result = {entity_name}_service.get_page(
        page_number=1,
        page_size=10,
        omit_pagination=False,
        {filter_args},
        sort_by=None,
        sort_direction=SortDirection.ascending,
    )

    # Assert
    assert result == Ok(ModelList[{EntityName}](items=[{entity_name}], total=1))

    # Verify filters were passed correctly
    {EntityName}DataService.get_by_page.assert_called_once()  # ty: ignore[has-type]
    call_args = {EntityName}DataService.get_by_page.call_args  # ty: ignore[has-type]
    filters = call_args.kwargs["filters"]  # ty: ignore[index]
    assert len(filters) == {filter_count}
    {filter_assertions}


def test_get_page_without_filters(
    {entity_name}_service: {EntityName}Service,
    {entity_name}_entity: {EntityName}Entity,
    {entity_name}: {EntityName},
    mocker: MockerFixture,
) -> None:
    # Arrange
    mocker.patch.object(
        {EntityName}DataService,
        "get_by_page",
        return_value=([{entity_name}_entity], 1),
    )

    # Act
    result = {entity_name}_service.get_page(
        page_number=1,
        page_size=10,
        omit_pagination=False,
        {no_filter_args},
        sort_by=None,
        sort_direction=SortDirection.ascending,
    )

    # Assert
    assert result.is_ok()
    result_value = result.unwrap()
    assert result_value.items[0].id == {entity_name}.id
    assert result_value.total == 1

    # Verify no filters were passed
    {EntityName}DataService.get_by_page.assert_called_once()  # ty: ignore[has-type]
    call_args = {EntityName}DataService.get_by_page.call_args  # ty: ignore[has-type]
    filters = call_args.kwargs["filters"]  # ty: ignore[index]
    assert len(filters) == 0


def test_get_page_with_partial_filters(
    {entity_name}_service: {EntityName}Service,
    {entity_name}_entity: {EntityName}Entity,
    {entity_name}: {EntityName},
    mocker: MockerFixture,
) -> None:
    # Arrange
    mocker.patch.object(
        {EntityName}DataService,
        "get_by_page",
        return_value=([{entity_name}_entity], 1),
    )

    # Act - only pass {first_filter} filter
    result = {entity_name}_service.get_page(
        page_number=1,
        page_size=10,
        omit_pagination=False,
        {partial_filter_args},
        sort_by=None,
        sort_direction=SortDirection.ascending,
    )

    # Assert
    assert result.is_ok()
    result_value = result.unwrap()
    assert result_value.items[0].id == {entity_name}.id
    assert result_value.total == 1

    # Verify only {first_filter} filter was passed
    {EntityName}DataService.get_by_page.assert_called_once()  # ty: ignore[has-type]
    call_args = {EntityName}DataService.get_by_page.call_args  # ty: ignore[has-type]
    filters = call_args.kwargs["filters"]  # ty: ignore[index]
    assert len(filters) == 1
    assert isinstance(filters[0], EqualsFilter)
    assert filters[0].field == "{first_filter}"
    assert filters[0].value is {first_filter_value}
```

### Without Custom Filters

If entity has no custom filters beyond pagination, only create the `test_get_page_without_filters` test.

**Service Test Notes:**
- **Three tests if entity has filters**: with_filters, without_filters, with_partial_filters
- **One test if no filters**: only without_filters
- Mock the `get_by_page` method on `{EntityName}DataService` class (not instance)
- Use `mocker.patch.object()` for clean mocking
- Use `.is_ok()` and `.unwrap()` pattern (NOT `assert result == Ok(...)`)
- **Verify filters in detail**: check count, type, field names, and values
- Use `call_args.kwargs["filters"]` to inspect passed filters
- Filter assertions example:
  ```python
  assert any(isinstance(f, EqualsFilter) and f.field == "is_active" and f.value is True for f in filters)
  ```
- Include sort_by and sort_direction parameters in get_page calls
- `{filter_args}`: e.g., `is_active=True, is_completed=False`
- `{no_filter_args}`: e.g., `is_active=None, is_completed=None`
- `{partial_filter_args}`: e.g., `is_active=True, is_completed=None`
- `{filter_count}`: Number of filters (e.g., 2 for is_active + is_completed)
- `{filter_assertions}`: List of assertions checking each filter
- Add fixtures to conftest.py:
  ```python
  @pytest.fixture
  def {entity_name}_data_service(session: Session) -> {EntityName}DataService:
      return {EntityName}DataService(session=session)


  @pytest.fixture
  def {entity_name}_service({entity_name}_data_service: {EntityName}DataService) -> {EntityName}Service:
      return {EntityName}Service(data_service={entity_name}_data_service)
  ```

## 4. Router Tests File Template

**File:** `src/tests/unit/routers/test_{entity_name}.py`

### 4A. Unit Test Style (Recommended - Test Router Functions Directly)

```python
import uuid

from fastapi import HTTPException
import pytest
from pytest_mock import MockerFixture
from result import Err, Ok
from starlette.status import (
    HTTP_400_BAD_REQUEST,
    HTTP_404_NOT_FOUND,
)

from src.api_server.routers.{entity_name} import (
    create_{entity_name},
    delete_{entity_name},
    get_{entity_name}_by_id,
    get_{entity_name}s,
    update_{entity_name},
)
from src.models.base import ModelList
from src.models.enums.error_status import ErrorStatus
from src.models.enums.sort_direction import SortDirection
from src.models.error_result import ErrorResult
from src.models.{entity_name} import {EntityName}, {EntityName}Create, {EntityName}Update
from src.services.{entity_name}_service import {EntityName}Service


def test_get_{entity_name}s(
    mocker: MockerFixture, {entity_name}_service: {EntityName}Service, {entity_name}s: ModelList[{EntityName}]
) -> None:
    # Arrange
    mocker.patch.object({entity_name}_service, "get_page", return_value=Ok({entity_name}s))

    # Act
    result = get_{entity_name}s(
        page_number=1,
        page_size=10,
        omit_pagination=False,
        {filter_args_none},
        sort_by=None,
        sort_direction=SortDirection.ascending,
        {entity_name}_service={entity_name}_service,
    )

    # Assert
    assert result == {entity_name}s
    assert result.total == 1
    assert len(result.items) == 1
    {entity_name}_service.get_page.assert_called_once_with(  # ty: ignore[has-type]
        1, 10, False, {filter_values_none}, None, SortDirection.ascending
    )


def test_get_{entity_name}s_with_filters(
    mocker: MockerFixture, {entity_name}_service: {EntityName}Service, {entity_name}s: ModelList[{EntityName}]
) -> None:
    # Arrange
    mocker.patch.object({entity_name}_service, "get_page", return_value=Ok({entity_name}s))

    # Act
    result = get_{entity_name}s(
        page_number=1,
        page_size=10,
        omit_pagination=False,
        {filter_args_with_values},
        sort_by="{first_field}",
        sort_direction=SortDirection.descending,
        {entity_name}_service={entity_name}_service,
    )

    # Assert
    assert result == {entity_name}s
    {entity_name}_service.get_page.assert_called_once_with(  # ty: ignore[has-type]
        1, 10, False, {filter_values}, "{first_field}", SortDirection.descending
    )


@pytest.mark.filterwarnings("ignore::UserWarning")
def test_get_{entity_name}s__validation_error(
    mocker: MockerFixture, {entity_name}_service: {EntityName}Service
) -> None:
    # Arrange
    error = ErrorResult(status=ErrorStatus.BAD_REQUEST, details="Validation failed")
    mocker.patch.object({entity_name}_service, "get_page", return_value=Err(error))

    # Act & Assert
    with pytest.raises(HTTPException) as exc_info:
        get_{entity_name}s(
            page_number=1,
            page_size=10,
            omit_pagination=False,
            {filter_args_none},
            sort_by=None,
            sort_direction=SortDirection.ascending,
            {entity_name}_service={entity_name}_service,
        )

    assert exc_info.value.status_code == HTTP_400_BAD_REQUEST
    assert exc_info.value.detail == error.details


def test_get_{entity_name}_by_id(
    mocker: MockerFixture, {entity_name}_service: {EntityName}Service, {entity_name}_id: uuid.UUID, {entity_name}: {EntityName}
) -> None:
    # Arrange
    mocker.patch.object({entity_name}_service, "get_by_id", return_value=Ok({entity_name}))

    # Act
    result = get_{entity_name}_by_id({entity_name}_id={entity_name}_id, {entity_name}_service={entity_name}_service)

    # Assert
    assert result == {entity_name}
    {entity_name}_service.get_by_id.assert_called_once_with({entity_name}_id)  # ty: ignore[has-type]


def test_get_{entity_name}_by_id__{entity_name}_not_found(
    mocker: MockerFixture,
    {entity_name}_service: {EntityName}Service,
    {entity_name}_id: uuid.UUID,
    {entity_name}_error_result_not_found: ErrorResult,
) -> None:
    # Arrange
    mocker.patch.object(
        {entity_name}_service, "get_by_id", return_value=Err({entity_name}_error_result_not_found)
    )

    # Act & Assert
    with pytest.raises(HTTPException) as exc_info:
        get_{entity_name}_by_id({entity_name}_id={entity_name}_id, {entity_name}_service={entity_name}_service)

    assert exc_info.value.status_code == HTTP_404_NOT_FOUND
    assert exc_info.value.detail == {entity_name}_error_result_not_found.details


def test_create_{entity_name}(
    mocker: MockerFixture,
    {entity_name}_service: {EntityName}Service,
    {entity_name}_create: {EntityName}Create,
    {entity_name}: {EntityName},
) -> None:
    # Arrange
    current_user_id = "test-user-id"
    mocker.patch.object({entity_name}_service, "create", return_value=Ok({entity_name}))

    # Act
    result = create_{entity_name}(
        {entity_name}={entity_name}_create, {entity_name}_service={entity_name}_service, current_user_id=current_user_id
    )

    # Assert
    assert result == {entity_name}
    {entity_name}_service.create.assert_called_once()  # ty: ignore[has-type]
    call_args = {entity_name}_service.create.call_args  # ty: ignore[has-type]
    assert call_args[0][0] == {entity_name}_create  # ty: ignore[index]
    assert call_args[0][2] == current_user_id  # ty: ignore[index]


@pytest.mark.filterwarnings("ignore::UserWarning")
def test_create_{entity_name}__validation_error(
    mocker: MockerFixture, {entity_name}_service: {EntityName}Service, {entity_name}_create: {EntityName}Create
) -> None:
    # Arrange
    current_user_id = "test-user-id"
    error = ErrorResult(status=ErrorStatus.BAD_REQUEST, details="Validation failed")
    mocker.patch.object({entity_name}_service, "create", return_value=Err(error))

    # Act & Assert
    with pytest.raises(HTTPException) as exc_info:
        create_{entity_name}(
            {entity_name}={entity_name}_create, {entity_name}_service={entity_name}_service, current_user_id=current_user_id
        )

    assert exc_info.value.status_code == HTTP_400_BAD_REQUEST
    assert exc_info.value.detail == error.details


def test_update_{entity_name}(
    mocker: MockerFixture,
    {entity_name}_service: {EntityName}Service,
    {entity_name}_id: uuid.UUID,
    {entity_name}_update: {EntityName}Update,
    {entity_name}: {EntityName},
) -> None:
    # Arrange
    current_user_id = "test-user-id"
    mocker.patch.object({entity_name}_service, "update", return_value=Ok({entity_name}))

    # Act
    result = update_{entity_name}(
        {entity_name}_id={entity_name}_id,
        {entity_name}={entity_name}_update,
        {entity_name}_service={entity_name}_service,
        current_user_id=current_user_id,
    )

    # Assert
    assert result == {entity_name}
    {entity_name}_service.update.assert_called_once_with(
        {entity_name}_id, {entity_name}_update, current_user_id
    )  # ty: ignore[has-type]


def test_update_{entity_name}__{entity_name}_not_found(
    mocker: MockerFixture,
    {entity_name}_service: {EntityName}Service,
    {entity_name}_id: uuid.UUID,
    {entity_name}_update: {EntityName}Update,
    {entity_name}_error_result_not_found: ErrorResult,
) -> None:
    # Arrange
    current_user_id = "test-user-id"
    mocker.patch.object(
        {entity_name}_service, "update", return_value=Err({entity_name}_error_result_not_found)
    )

    # Act & Assert
    with pytest.raises(HTTPException) as exc_info:
        update_{entity_name}(
            {entity_name}_id={entity_name}_id,
            {entity_name}={entity_name}_update,
            {entity_name}_service={entity_name}_service,
            current_user_id=current_user_id,
        )

    assert exc_info.value.status_code == HTTP_404_NOT_FOUND
    assert exc_info.value.detail == {entity_name}_error_result_not_found.details


@pytest.mark.filterwarnings("ignore::UserWarning")
def test_update_{entity_name}__validation_error(
    mocker: MockerFixture,
    {entity_name}_service: {EntityName}Service,
    {entity_name}_id: uuid.UUID,
    {entity_name}_update: {EntityName}Update,
) -> None:
    # Arrange
    current_user_id = "test-user-id"
    error = ErrorResult(status=ErrorStatus.BAD_REQUEST, details="Validation failed")
    mocker.patch.object({entity_name}_service, "update", return_value=Err(error))

    # Act & Assert
    with pytest.raises(HTTPException) as exc_info:
        update_{entity_name}(
            {entity_name}_id={entity_name}_id,
            {entity_name}={entity_name}_update,
            {entity_name}_service={entity_name}_service,
            current_user_id=current_user_id,
        )

    assert exc_info.value.status_code == HTTP_400_BAD_REQUEST
    assert exc_info.value.detail == error.details


def test_delete_{entity_name}(
    mocker: MockerFixture, {entity_name}_service: {EntityName}Service, {entity_name}_id: uuid.UUID
) -> None:
    # Arrange
    mocker.patch.object({entity_name}_service, "delete", return_value=Ok(None))

    # Act
    result = delete_{entity_name}({entity_name}_id={entity_name}_id, {entity_name}_service={entity_name}_service)

    # Assert
    assert result is None
    {entity_name}_service.delete.assert_called_once_with({entity_name}_id)  # ty: ignore[has-type]


def test_delete_{entity_name}__{entity_name}_not_found(
    mocker: MockerFixture,
    {entity_name}_service: {EntityName}Service,
    {entity_name}_id: uuid.UUID,
    {entity_name}_error_result_not_found: ErrorResult,
) -> None:
    # Arrange
    mocker.patch.object(
        {entity_name}_service, "delete", return_value=Err({entity_name}_error_result_not_found)
    )

    # Act & Assert
    with pytest.raises(HTTPException) as exc_info:
        delete_{entity_name}({entity_name}_id={entity_name}_id, {entity_name}_service={entity_name}_service)

    assert exc_info.value.status_code == HTTP_404_NOT_FOUND
    assert exc_info.value.detail == {entity_name}_error_result_not_found.details
```

### 4B. Integration Test Style (Alternative - Use TestClient)

```python
from uuid import UUID

import pytest
from pytest_mock import MockerFixture
from result import Err, Ok
from starlette.status import (
    HTTP_200_OK,
    HTTP_201_CREATED,
    HTTP_204_NO_CONTENT,
    HTTP_400_BAD_REQUEST,
    HTTP_404_NOT_FOUND,
    HTTP_409_CONFLICT,
)
from starlette.testclient import TestClient

from src.constants import {ENTITY_PREFIX}, VERSION_PREFIX
from src.models.base import ModelList
from src.models.error_result import ErrorResult
from src.models.problem_details import ProblemDetails
from src.models.{entity_name} import {EntityName}, {EntityName}Create, {EntityName}Update
from src.services.{entity_name}_service import {EntityName}Service
from src.tests.utils import is_expected_result_json

{ENTITY_NAME}_URL = f"/{VERSION_PREFIX}/{{{ENTITY_PREFIX}}}"


def test_get_{entity_name_plural}(
    client: TestClient,
    {entity_name}s: ModelList[{EntityName}],
    mocker: MockerFixture,
) -> None:
    # Arrange
    mocker.patch.object(
        {EntityName}Service,
        "get_page",
        return_value=Ok({entity_name}s),
    )

    # Act
    response = client.get({ENTITY_NAME}_URL)

    # Assert
    assert response.status_code == HTTP_200_OK
    assert is_expected_result_json(response.json(), {entity_name}s)


def test_get_{entity_name_plural}__validation_error(client: TestClient) -> None:
    # Act
    response = client.get(f"{{{ENTITY_NAME}_URL}}?pageNumber=True&pageSize=kek&omitPagination=2")

    # Assert
    assert response.status_code == HTTP_400_BAD_REQUEST


def test_get_{entity_name}_by_id(
    client: TestClient,
    {entity_name}_id: UUID,
    {entity_name}: {EntityName},
    mocker: MockerFixture,
) -> None:
    # Arrange
    mocker.patch.object(
        {EntityName}Service,
        "get_by_id",
        return_value=Ok({entity_name}),
    )

    # Act
    response = client.get(f"{{{ENTITY_NAME}_URL}}/{{{entity_name}_id}}")

    # Assert
    assert response.status_code == HTTP_200_OK
    assert is_expected_result_json(response.json(), {entity_name})


def test_get_{entity_name}_by_id__{entity_name}_not_found(
    client: TestClient,
    {entity_name}_error_result_not_found: ErrorResult,
    {entity_name}_id: UUID,
    {entity_name}_not_found: ProblemDetails,
    mocker: MockerFixture,
) -> None:
    # Arrange
    mocker.patch.object(
        {EntityName}Service,
        "get_by_id",
        return_value=Err({entity_name}_error_result_not_found),
    )

    # Act
    response = client.get(f"{{{ENTITY_NAME}_URL}}/{{{entity_name}_id}}")

    # Assert
    assert response.status_code == HTTP_404_NOT_FOUND
    assert is_expected_result_json(response.json(), {entity_name}_not_found)


def test_create_{entity_name}(
    client: TestClient,
    {entity_name}_create: {EntityName}Create,
    {entity_name}: {EntityName},
    mocker: MockerFixture,
) -> None:
    # Arrange
    mocker.patch.object({EntityName}Service, "create", return_value=Ok({entity_name}))

    # Act
    response = client.post({ENTITY_NAME}_URL, json={entity_name}_create.model_dump())

    # Assert
    assert response.status_code == HTTP_201_CREATED
    assert is_expected_result_json(response.json(), {entity_name})


@pytest.mark.filterwarnings("ignore::UserWarning")
def test_create_{entity_name}__validation_error(client: TestClient, {entity_name}_create: {EntityName}Create) -> None:
    # Arrange
    {entity_name}_create.{first_field_name} = 1  # type: ignore[assignment]

    # Act
    response = client.post({ENTITY_NAME}_URL, json={entity_name}_create.model_dump())

    # Assert
    assert response.status_code == HTTP_400_BAD_REQUEST


def test_update_{entity_name}(
    client: TestClient, {entity_name}_id: UUID, {entity_name}_update: {EntityName}Update, {entity_name}: {EntityName}, mocker: MockerFixture
) -> None:
    # Arrange
    mocker.patch.object({EntityName}Service, "update", return_value=Ok({entity_name}))

    # Act
    response = client.patch(f"{{{ENTITY_NAME}_URL}}/{{{entity_name}_id}}", json={entity_name}_update.model_dump())

    # Assert
    assert response.status_code == HTTP_200_OK
    assert is_expected_result_json(response.json(), {entity_name})


def test_update_{entity_name}__{entity_name}_not_found(
    client: TestClient,
    {entity_name}_id: UUID,
    {entity_name}_update: {EntityName}Update,
    {entity_name}_error_result_not_found: ErrorResult,
    {entity_name}_not_found: ProblemDetails,
    mocker: MockerFixture,
) -> None:
    # Arrange
    mocker.patch.object({EntityName}Service, "update", return_value=Err({entity_name}_error_result_not_found))

    # Act
    response = client.patch(f"{{{ENTITY_NAME}_URL}}/{{{entity_name}_id}}", json={entity_name}_update.model_dump())

    # Assert
    assert response.status_code == HTTP_404_NOT_FOUND
    assert is_expected_result_json(response.json(), {entity_name}_not_found)


@pytest.mark.filterwarnings("ignore::UserWarning")
def test_update_{entity_name}__validation_error(client: TestClient, {entity_name}_id: UUID, {entity_name}_update: {EntityName}Update) -> None:
    # Arrange
    {entity_name}_update.{first_field_name} = 1  # type: ignore[assignment]

    # Act
    response = client.patch(f"{{{ENTITY_NAME}_URL}}/{{{entity_name}_id}}", json={entity_name}_update.model_dump())

    # Assert
    assert response.status_code == HTTP_400_BAD_REQUEST


def test_delete_{entity_name}(client: TestClient, {entity_name}_id: UUID, mocker: MockerFixture) -> None:
    # Arrange
    mocker.patch.object(
        {EntityName}Service,
        "delete",
        return_value=Ok(None),
    )
    # Act
    response = client.delete(f"{{{ENTITY_NAME}_URL}}/{{{entity_name}_id}}")

    # Assert
    assert response.status_code == HTTP_204_NO_CONTENT


def test_delete_{entity_name}__{entity_name}_not_found(
    client: TestClient,
    {entity_name}_id: UUID,
    {entity_name}_error_result_not_found: ErrorResult,
    {entity_name}_not_found: ProblemDetails,
    mocker: MockerFixture,
) -> None:
    # Arrange
    mocker.patch.object(
        {EntityName}Service,
        "delete",
        return_value=Err({entity_name}_error_result_not_found),
    )

    # Act
    response = client.delete(f"{{{ENTITY_NAME}_URL}}/{{{entity_name}_id}}")

    # Assert
    assert response.status_code == HTTP_404_NOT_FOUND
    assert is_expected_result_json(response.json(), {entity_name}_not_found)
```

### Optional: Tests for Unique Constraint Conflicts

Add these tests if the entity has unique constraints:

```python
def test_create_{entity_name}__conflict(
    client: TestClient,
    {entity_name}_create: {EntityName}Create,
    {entity_name}_error_result_already_exists: ErrorResult,
    {entity_name}_already_exists: ProblemDetails,
    mocker: MockerFixture,
) -> None:
    # Arrange
    mocker.patch.object({EntityName}Service, "create", return_value=Err({entity_name}_error_result_already_exists))

    # Act
    response = client.post({ENTITY_NAME}_URL, json={entity_name}_create.model_dump())

    # Assert
    assert response.status_code == HTTP_409_CONFLICT
    assert is_expected_result_json(response.json(), {entity_name}_already_exists)


def test_update_{entity_name}__conflict(
    client: TestClient,
    {entity_name}_id: UUID,
    {entity_name}_update: {EntityName}Update,
    {entity_name}_error_result_already_exists: ErrorResult,
    {entity_name}_already_exists: ProblemDetails,
    mocker: MockerFixture,
) -> None:
    # Arrange
    mocker.patch.object({EntityName}Service, "update", return_value=Err({entity_name}_error_result_already_exists))

    # Act
    response = client.patch(f"{{{ENTITY_NAME}_URL}}/{{{entity_name}_id}}", json={entity_name}_update.model_dump())

    # Assert
    assert response.status_code == HTTP_409_CONFLICT
    assert is_expected_result_json(response.json(), {entity_name}_already_exists)
```

**Router Test Notes:**

**Unit Test Style (4A - Recommended):**
- Call router functions directly (e.g., `get_{entity_name}s(...)`)
- Pass service as a parameter to the function
- Mock service instance methods with `mocker.patch.object({entity_name}_service, "method_name", ...)`
- Verify return values with `assert result == expected`
- Verify service method calls with `.assert_called_once_with(...)`
- For error cases, use `with pytest.raises(HTTPException)` and check status_code and detail
- Import uuid module (not from uuid import UUID)
- Import router functions directly from router file
- Use `current_user_id = "test-user-id"` for create/update tests
- Filter parameters: `{filter_args_none}` = `is_active=None, is_completed=None`
- Filter parameters: `{filter_args_with_values}` = `is_active=True, is_completed=False`
- Filter values in assertions: `{filter_values_none}` = `None, None`
- Filter values in assertions: `{filter_values}` = `True, False`
- Always include sort_by and sort_direction parameters
- Use `@pytest.mark.filterwarnings("ignore::UserWarning")` for validation error tests

**Integration Test Style (4B - Alternative):**
- Use `TestClient` to make HTTP requests
- Use `{ENTITY_NAME}_URL` constant for endpoint base path
- Mock the `{EntityName}Service` class methods (not instance), e.g., `mocker.patch.object({EntityName}Service, "method_name", ...)`
- Verify HTTP status codes (HTTP_200_OK, HTTP_201_CREATED, etc.)
- Use `is_expected_result_json()` helper for comparing response JSON
- For validation error tests, set invalid field: `{entity_name}_create.{first_field_name} = 1  # type: ignore[assignment]`
- Use `@pytest.mark.filterwarnings("ignore::UserWarning")` to suppress Pydantic warnings in validation tests
- Query parameters use camelCase (e.g., `?pageNumber=True&pageSize=kek`)

**Both Styles:**
- Mock the service layer (not data service)
- Test both success (Ok) and error (Err) result patterns
- Include conflict tests only if unique constraints exist
- Use descriptive test names: `test_{method}` for success, `test_{method}__{condition}` for errors
- Total of 10 tests minimum: 2 for GET list, 2 for GET by ID, 2 for POST, 3 for PATCH, 2 for DELETE
- Add 2 more tests if unique constraints (conflict cases for create and update)

## 5. Update conftest.py

**File:** `src/tests/conftest.py`

Add to the `pytest_plugins` list:

```python
pytest_plugins = [
    "src.tests.fixtures.user_fixtures",
    "src.tests.fixtures.{entity_name}_fixtures",  # Add this line
]
```

Add service and data service fixtures:

```python
@pytest.fixture
def {entity_name}_data_service(session: Session) -> {EntityName}DataService:
    return {EntityName}DataService(session=session)


@pytest.fixture
def {entity_name}_service({entity_name}_data_service: {EntityName}DataService) -> {EntityName}Service:
    return {EntityName}Service(data_service={entity_name}_data_service)
```

Add imports at the top:

```python
from src.data_services.{entity_name}_data_service import {EntityName}DataService
from src.services.{entity_name}_service import {EntityName}Service
```

## Placeholder Reference Guide

| Placeholder | Example Value | Description |
|------------|---------------|-------------|
| `{EntityName}` | `Task` | PascalCase entity class name |
| `{entity_name}` | `task` | snake_case entity name |
| `{entity_name_plural}` | `tasks` | snake_case plural |
| `{ENTITY_PREFIX}` | `TASKS_PREFIX` | Constant for route prefix |
| `{ENTITY_NAME}` | `TASK` | Uppercase for URL constant |
| `{create_fields}` | `title="Sample Task",\n        description="Task description",\n        is_completed=False,\n        user_id=user_id` | Create model fields with explicit values |
| `{update_fields}` | `title="Updated Task",\n        description="Updated description",\n        is_completed=True,\n        is_active=True` | Update model fields |
| `{explicit_fields}` | `title="Sample Task",\n        description="Task description",\n        is_completed=False,\n        user_id=user_id,` | All entity fields listed explicitly |
| `{foreign_key_fixtures}` | `@pytest.fixture(scope="session")\ndef user_id() -> uuid.UUID:\n    return uuid.uuid4()` | Foreign key ID fixtures |
| `{foreign_key_params}` | `user_id: uuid.UUID` | Parameters for FK fixtures |
| `{first_fk_id}` | `user_id` | First foreign key ID for audit fields |
| `{field_assertions}` | `assert result.title == task_create.title\n    assert result.description == task_create.description` | Assertions for all fields |
| `{foreign_key_assertions}` | `assert result.user_id == task_create.user_id\n    assert isinstance(result.user_id, uuid.UUID)` | FK field assertions |
| `{filter_args}` | `is_active=True, is_completed=False` | Filter arguments with values |
| `{no_filter_args}` | `is_active=None, is_completed=None` | Filter arguments as None |
| `{partial_filter_args}` | `is_active=True, is_completed=None` | Some filters with values |
| `{filter_args_none}` | `is_active=None,\n        is_completed=None,` | Router filter params as None |
| `{filter_args_with_values}` | `is_active=True,\n        is_completed=False,` | Router filter params with values |
| `{filter_values_none}` | `None, None` | Filter values for assertions |
| `{filter_values}` | `True, False` | Filter values for assertions |
| `{filter_count}` | `2` | Number of filters passed |
| `{filter_assertions}` | `assert any(isinstance(f, EqualsFilter) and f.field == "is_active" and f.value is True for f in filters)` | Detailed filter checks |
| `{first_filter}` | `is_active` | First filter name |
| `{first_filter_value}` | `True` | First filter value |
| `{first_field}` | `title` | First sortable field name |
| `{first_field_name}` | `title` | First string field for validation tests |

## Tips for Customization

1. **Sample Data**: Make fixture data realistic but simple
2. **Foreign Keys**: If entity has relationships, add foreign key fixtures
3. **Custom Methods**: If service has custom methods beyond CRUD, add tests
4. **Business Logic**: Add tests for any business rule validations
5. **Edge Cases**: Consider boundary conditions for numeric fields
6. **Relationships**: Test cascade behavior if entity has dependent children
