# Example: Task Entity Tests

This is a complete example of generating tests for the Task entity with the following specifications:

- **Entity Name:** Task
- **Fields:** title (str), description (str), priority (int), user_id (UUID FK to User)
- **Filters:** is_active (bool), user_id (UUID), title (str, ContainsFilter)
- **Unique Constraints:** NONE
- **Relationships:** many-to-one with User

## Generated Files

### 1. Fixtures (`src/tests/fixtures/task_fixtures.py`)

```python
import uuid
from datetime import datetime, timezone

import pytest

from src.database.entities.task import TaskEntity
from src.models.base import ModelList
from src.models.enums.error_status import ErrorStatus
from src.models.error_result import ErrorResult
from src.models.problem_details import ProblemDetails
from src.models.task import Task, TaskCreate, TaskUpdate


@pytest.fixture(scope="session")
def task_id() -> uuid.UUID:
    return uuid.uuid4()


@pytest.fixture(scope="session")
def task_user_id() -> uuid.UUID:
    return uuid.uuid4()


@pytest.fixture(scope="session")
def task_create(task_user_id: uuid.UUID) -> TaskCreate:
    return TaskCreate(
        title="Sample Task",
        description="Task description",
        priority=1,
        user_id=task_user_id,
    )


@pytest.fixture(scope="session")
def task_update() -> TaskUpdate:
    return TaskUpdate(
        title="Updated Task",
        description="Updated description",
        priority=2,
        is_active=True,
    )


@pytest.fixture(scope="session")
def task(task_id: uuid.UUID, task_user_id: uuid.UUID) -> Task:
    return Task(
        id=task_id,
        title="Sample Task",
        description="Task description",
        priority=1,
        user_id=task_user_id,
        is_active=True,
        created_date=datetime(2024, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
        last_modified_date=datetime(2024, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
        created_by_user_id=str(task_user_id),
        last_modified_by_user_id=str(task_user_id),
    )


@pytest.fixture(scope="session")
def tasks(task: Task) -> ModelList[Task]:
    return ModelList(
        items=[task],
        total=1,
    )


@pytest.fixture(scope="session")
def task_entity(task_id: uuid.UUID, task_user_id: uuid.UUID) -> TaskEntity:
    return TaskEntity(
        id=task_id,
        title="Sample Task",
        description="Task description",
        priority=1,
        user_id=task_user_id,
        is_active=True,
        created_date=datetime(2024, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
        last_modified_date=datetime(2024, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
        created_by_user_id=str(task_user_id),
        last_modified_by_user_id=str(task_user_id),
    )


@pytest.fixture(scope="session")
def task_error_result_not_found() -> ErrorResult:
    return ErrorResult(
        status=ErrorStatus.NOT_FOUND_ERROR,
        details="Task not found",
    )


@pytest.fixture(scope="session")
def task_not_found(task_error_result_not_found: ErrorResult) -> ProblemDetails:
    return ProblemDetails(
        type="about:blank",
        title="Not Found",
        status=404,
        detail=task_error_result_not_found.details,
        instance="string",
    )
```

**Key rules followed:**
- All fixtures use `scope="session"` (not `scope="module"` or default function scope)
- Fields are assigned explicitly (NOT `**model_dump()`)
- Datetimes use explicit values like `datetime(2024, 1, 1, ...)` (NOT `datetime.now()`)
- FK fixture is named `task_user_id` (prefixed) to avoid conflicts with other fixtures
- Error message is simple: `"Task not found"` (not `"Task with id {id} not found"`)

### 2. Mapper Tests (`src/tests/unit/mappers/test_task_mapper.py`)

```python
import uuid

from src.mappers.task import to_task_entity
from src.models.task import TaskCreate


def test_to_task_entity(task_create: TaskCreate) -> None:
    # Arrange
    user_id = str(uuid.uuid4())

    # Act
    result = to_task_entity(task_create, user_id)

    # Assert
    assert result.id is not None
    assert isinstance(result.id, uuid.UUID)
    assert result.title == task_create.title
    assert result.description == task_create.description
    assert result.priority == task_create.priority
    assert result.is_active is True
    assert result.created_by_user_id == user_id
    assert result.last_modified_by_user_id == user_id


def test_to_task_entity__generates_unique_id(task_create: TaskCreate) -> None:
    # Arrange
    user_id = str(uuid.uuid4())

    # Act
    result1 = to_task_entity(task_create, user_id)
    result2 = to_task_entity(task_create, user_id)

    # Assert
    assert result1.id != result2.id


def test_to_task_entity__maps_foreign_key(task_create: TaskCreate) -> None:
    # Arrange
    user_id = str(uuid.uuid4())

    # Act
    result = to_task_entity(task_create, user_id)

    # Assert
    assert result.user_id == task_create.user_id
    assert isinstance(result.user_id, uuid.UUID)
```

**Key rules followed:**
- Use `import uuid` (not `from uuid import UUID`)
- `user_id` is created locally in each test (not from a fixture)
- Three tests: basic mapping, UUID uniqueness, FK mapping (separate test since entity has FK)

### 3. Service Tests (`src/tests/unit/services/test_task_service.py`)

```python
from uuid import UUID

import pytest
from pytest_mock import MockerFixture
from result import Ok

from src.data_services.filters import ContainsFilter, EqualsFilter
from src.data_services.task_data_service import TaskDataService
from src.database.entities.task import TaskEntity
from src.models.base import ModelList
from src.models.enums.sort_direction import SortDirection
from src.models.task import Task
from src.services.task_service import TaskService


def test_get_page_with_all_filters(
    task_service: TaskService,
    task_entity: TaskEntity,
    task: Task,
    task_user_id: UUID,
    mocker: MockerFixture,
) -> None:
    # Arrange
    mocker.patch.object(
        TaskDataService,
        "get_by_page",
        return_value=([task_entity], 1),
    )

    # Act
    result = task_service.get_page(
        page_number=1,
        page_size=10,
        omit_pagination=False,
        is_active=True,
        user_id=task_user_id,
        title="Sample",
        sort_by=None,
        sort_direction=SortDirection.ascending,
    )

    # Assert
    assert result == Ok(ModelList[Task](items=[task], total=1))

    # Verify filters were passed correctly
    TaskDataService.get_by_page.assert_called_once()  # ty: ignore[has-type]
    call_args = TaskDataService.get_by_page.call_args  # ty: ignore[has-type]
    filters = call_args.kwargs["filters"]  # ty: ignore[index]
    assert len(filters) == 3

    is_active_filter = next(
        (f for f in filters if isinstance(f, EqualsFilter) and f.field == TaskEntity.is_active), None
    )
    assert is_active_filter is not None
    assert is_active_filter.value is True

    user_id_filter = next(
        (f for f in filters if isinstance(f, EqualsFilter) and f.field == TaskEntity.user_id), None
    )
    assert user_id_filter is not None
    assert user_id_filter.value == task_user_id

    title_filter = next(
        (f for f in filters if isinstance(f, ContainsFilter) and f.field == TaskEntity.title), None
    )
    assert title_filter is not None
    assert title_filter.value == "Sample"


def test_get_page_without_filters(
    task_service: TaskService,
    task_entity: TaskEntity,
    task: Task,
    mocker: MockerFixture,
) -> None:
    # Arrange
    mocker.patch.object(
        TaskDataService,
        "get_by_page",
        return_value=([task_entity], 1),
    )

    # Act
    result = task_service.get_page(
        page_number=1,
        page_size=10,
        omit_pagination=False,
        is_active=None,
        user_id=None,
        title=None,
        sort_by=None,
        sort_direction=SortDirection.ascending,
    )

    # Assert
    assert result.is_ok()
    result_value = result.unwrap()
    assert result_value.items[0].id == task.id
    assert result_value.total == 1

    # Verify no filters were passed
    TaskDataService.get_by_page.assert_called_once()  # ty: ignore[has-type]
    call_args = TaskDataService.get_by_page.call_args  # ty: ignore[has-type]
    filters = call_args.kwargs["filters"]  # ty: ignore[index]
    assert len(filters) == 0


def test_get_page_with_partial_filters(
    task_service: TaskService,
    task_entity: TaskEntity,
    task: Task,
    mocker: MockerFixture,
) -> None:
    # Arrange
    mocker.patch.object(
        TaskDataService,
        "get_by_page",
        return_value=([task_entity], 1),
    )

    # Act - only pass is_active filter
    result = task_service.get_page(
        page_number=1,
        page_size=10,
        omit_pagination=False,
        is_active=True,
        user_id=None,
        title=None,
        sort_by=None,
        sort_direction=SortDirection.ascending,
    )

    # Assert
    assert result.is_ok()

    # Verify only is_active filter was passed
    TaskDataService.get_by_page.assert_called_once()  # ty: ignore[has-type]
    call_args = TaskDataService.get_by_page.call_args  # ty: ignore[has-type]
    filters = call_args.kwargs["filters"]  # ty: ignore[index]
    assert len(filters) == 1
    assert isinstance(filters[0], EqualsFilter)
    assert filters[0].field == TaskEntity.is_active
    assert filters[0].value is True
```

**Key rules followed:**
- Mock `get_by_page` on the **class** (not instance) with `mocker.patch.object(TaskDataService, "get_by_page", ...)`
- Return value is a **tuple**: `([task_entity], 1)` (NOT `Ok([task_entity])`)
- Filter assertions use `filter.field == TaskEntity.field_name` (NOT `filter.field_name == "string"`)
- Three tests: all filters, no filters, partial filters

### 4. Router Tests (`src/tests/unit/routers/test_task.py`)

```python
import uuid

import pytest
from fastapi import HTTPException
from pytest_mock import MockerFixture
from result import Err, Ok
from starlette.status import (
    HTTP_400_BAD_REQUEST,
    HTTP_404_NOT_FOUND,
)

from src.api_server.routers.task import (
    create_task,
    delete_task,
    get_task_by_id,
    get_tasks,
    update_task,
)
from src.models.base import ModelList
from src.models.enums.error_status import ErrorStatus
from src.models.enums.sort_direction import SortDirection
from src.models.error_result import ErrorResult
from src.models.task import Task, TaskCreate, TaskUpdate
from src.services.task_service import TaskService


def test_get_tasks(
    mocker: MockerFixture, task_service: TaskService, tasks: ModelList[Task]
) -> None:
    # Arrange
    mocker.patch.object(task_service, "get_page", return_value=Ok(tasks))

    # Act
    result = get_tasks(
        page_number=1,
        page_size=10,
        omit_pagination=False,
        is_active=None,
        user_id=None,
        title=None,
        sort_by=None,
        sort_direction=SortDirection.ascending,
        task_service=task_service,
    )

    # Assert
    assert result == tasks
    assert result.total == 1
    assert len(result.items) == 1
    task_service.get_page.assert_called_once_with(  # ty: ignore[has-type]
        1, 10, False, None, None, None, None, SortDirection.ascending
    )


def test_get_tasks_with_filters(
    mocker: MockerFixture, task_service: TaskService, tasks: ModelList[Task], task_user_id: uuid.UUID
) -> None:
    # Arrange
    mocker.patch.object(task_service, "get_page", return_value=Ok(tasks))

    # Act
    result = get_tasks(
        page_number=1,
        page_size=10,
        omit_pagination=False,
        is_active=True,
        user_id=task_user_id,
        title="Sample",
        sort_by="title",
        sort_direction=SortDirection.descending,
        task_service=task_service,
    )

    # Assert
    assert result == tasks
    task_service.get_page.assert_called_once_with(  # ty: ignore[has-type]
        1, 10, False, True, task_user_id, "Sample", "title", SortDirection.descending
    )


@pytest.mark.filterwarnings("ignore::UserWarning")
def test_get_tasks__validation_error(
    mocker: MockerFixture, task_service: TaskService
) -> None:
    # Arrange
    error = ErrorResult(status=ErrorStatus.BAD_REQUEST, details="Validation failed")
    mocker.patch.object(task_service, "get_page", return_value=Err(error))

    # Act & Assert
    with pytest.raises(HTTPException) as exc_info:
        get_tasks(
            page_number=1,
            page_size=10,
            omit_pagination=False,
            is_active=None,
            user_id=None,
            title=None,
            sort_by=None,
            sort_direction=SortDirection.ascending,
            task_service=task_service,
        )

    assert exc_info.value.status_code == HTTP_400_BAD_REQUEST
    assert exc_info.value.detail == error.details


def test_get_task_by_id(
    mocker: MockerFixture, task_service: TaskService, task_id: uuid.UUID, task: Task
) -> None:
    # Arrange
    mocker.patch.object(task_service, "get_by_id", return_value=Ok(task))

    # Act
    result = get_task_by_id(task_id=task_id, task_service=task_service)

    # Assert
    assert result == task
    task_service.get_by_id.assert_called_once_with(task_id)  # ty: ignore[has-type]


def test_get_task_by_id__task_not_found(
    mocker: MockerFixture,
    task_service: TaskService,
    task_id: uuid.UUID,
    task_error_result_not_found: ErrorResult,
) -> None:
    # Arrange
    mocker.patch.object(
        task_service, "get_by_id", return_value=Err(task_error_result_not_found)
    )

    # Act & Assert
    with pytest.raises(HTTPException) as exc_info:
        get_task_by_id(task_id=task_id, task_service=task_service)

    assert exc_info.value.status_code == HTTP_404_NOT_FOUND
    assert exc_info.value.detail == task_error_result_not_found.details


def test_create_task(
    mocker: MockerFixture,
    task_service: TaskService,
    task_create: TaskCreate,
    task: Task,
) -> None:
    # Arrange
    current_user_id = "test-user-id"
    mocker.patch.object(task_service, "create", return_value=Ok(task))

    # Act
    result = create_task(
        task=task_create, task_service=task_service, current_user_id=current_user_id
    )

    # Assert
    assert result == task
    task_service.create.assert_called_once()  # ty: ignore[has-type]
    call_args = task_service.create.call_args  # ty: ignore[has-type]
    assert call_args[0][0] == task_create  # ty: ignore[index]
    assert call_args[0][2] == current_user_id  # ty: ignore[index]


@pytest.mark.filterwarnings("ignore::UserWarning")
def test_create_task__validation_error(
    mocker: MockerFixture, task_service: TaskService, task_create: TaskCreate
) -> None:
    # Arrange
    current_user_id = "test-user-id"
    error = ErrorResult(status=ErrorStatus.BAD_REQUEST, details="Validation failed")
    mocker.patch.object(task_service, "create", return_value=Err(error))

    # Act & Assert
    with pytest.raises(HTTPException) as exc_info:
        create_task(
            task=task_create, task_service=task_service, current_user_id=current_user_id
        )

    assert exc_info.value.status_code == HTTP_400_BAD_REQUEST
    assert exc_info.value.detail == error.details


def test_update_task(
    mocker: MockerFixture,
    task_service: TaskService,
    task_id: uuid.UUID,
    task_update: TaskUpdate,
    task: Task,
) -> None:
    # Arrange
    current_user_id = "test-user-id"
    mocker.patch.object(task_service, "update", return_value=Ok(task))

    # Act
    result = update_task(
        task_id=task_id,
        task=task_update,
        task_service=task_service,
        current_user_id=current_user_id,
    )

    # Assert
    assert result == task
    task_service.update.assert_called_once_with(
        task_id, task_update, current_user_id
    )  # ty: ignore[has-type]


def test_update_task__task_not_found(
    mocker: MockerFixture,
    task_service: TaskService,
    task_id: uuid.UUID,
    task_update: TaskUpdate,
    task_error_result_not_found: ErrorResult,
) -> None:
    # Arrange
    current_user_id = "test-user-id"
    mocker.patch.object(
        task_service, "update", return_value=Err(task_error_result_not_found)
    )

    # Act & Assert
    with pytest.raises(HTTPException) as exc_info:
        update_task(
            task_id=task_id,
            task=task_update,
            task_service=task_service,
            current_user_id=current_user_id,
        )

    assert exc_info.value.status_code == HTTP_404_NOT_FOUND
    assert exc_info.value.detail == task_error_result_not_found.details


@pytest.mark.filterwarnings("ignore::UserWarning")
def test_update_task__validation_error(
    mocker: MockerFixture,
    task_service: TaskService,
    task_id: uuid.UUID,
    task_update: TaskUpdate,
) -> None:
    # Arrange
    current_user_id = "test-user-id"
    error = ErrorResult(status=ErrorStatus.BAD_REQUEST, details="Validation failed")
    mocker.patch.object(task_service, "update", return_value=Err(error))

    # Act & Assert
    with pytest.raises(HTTPException) as exc_info:
        update_task(
            task_id=task_id,
            task=task_update,
            task_service=task_service,
            current_user_id=current_user_id,
        )

    assert exc_info.value.status_code == HTTP_400_BAD_REQUEST
    assert exc_info.value.detail == error.details


def test_delete_task(
    mocker: MockerFixture, task_service: TaskService, task_id: uuid.UUID
) -> None:
    # Arrange
    mocker.patch.object(task_service, "delete", return_value=Ok(None))

    # Act
    result = delete_task(task_id=task_id, task_service=task_service)

    # Assert
    assert result is None
    task_service.delete.assert_called_once_with(task_id)  # ty: ignore[has-type]


def test_delete_task__task_not_found(
    mocker: MockerFixture,
    task_service: TaskService,
    task_id: uuid.UUID,
    task_error_result_not_found: ErrorResult,
) -> None:
    # Arrange
    mocker.patch.object(
        task_service, "delete", return_value=Err(task_error_result_not_found)
    )

    # Act & Assert
    with pytest.raises(HTTPException) as exc_info:
        delete_task(task_id=task_id, task_service=task_service)

    assert exc_info.value.status_code == HTTP_404_NOT_FOUND
    assert exc_info.value.detail == task_error_result_not_found.details
```

**Key rules followed:**
- Import router functions directly (unit test style — call functions, not HTTP requests)
- Mock the **service instance** with `mocker.patch.object(task_service, "method", ...)`
- Use `pytest.raises(HTTPException)` for error cases
- Import `import uuid` (not `from uuid import UUID`)
- No unique constraints → no conflict tests needed

### 5. conftest.py Updates

Add to `pytest_plugins`:
```python
pytest_plugins = [
    "src.tests.fixtures.user_fixtures",
    "src.tests.fixtures.task_fixtures",  # Add this
]
```

Add imports at the top:
```python
from src.data_services.task_data_service import TaskDataService
from src.services.task_service import TaskService
```

Add fixtures (no `scope` = function scope for mutable service instances):
```python
@pytest.fixture
def task_data_service(session: Session) -> TaskDataService:
    return TaskDataService(session=session)


@pytest.fixture
def task_service(task_data_service: TaskDataService) -> TaskService:
    return TaskService(data_service=task_data_service)
```

**Key rule:** Service fixtures use real `session` (MagicMock), NOT `MagicMock` directly for data service.

## API Endpoints Tested

Since Task has **no unique constraints**:

| Endpoint | Tests |
|----------|-------|
| GET /v1/tasks | success, with_filters, validation_error |
| GET /v1/tasks/{task_id} | success, not_found |
| POST /v1/tasks | success, validation_error |
| PATCH /v1/tasks/{task_id} | success, not_found, validation_error |
| DELETE /v1/tasks/{task_id} | success, not_found |

**Total: 11 tests** (no conflict tests since no unique constraints)

## Example With Unique Constraints

If the entity had unique constraints (like Product with unique `name`), add:

**Extra fixtures in `product_fixtures.py`:**
```python
@pytest.fixture(scope="session")
def product_error_result_already_exists() -> ErrorResult:
    return ErrorResult(
        status=ErrorStatus.CONFLICT,
        details="Product with given name already exists",
    )


@pytest.fixture(scope="session")
def product_already_exists(product_error_result_already_exists: ErrorResult) -> ProblemDetails:
    return ProblemDetails(
        type="about:blank",
        title="Conflict",
        status=409,
        detail=product_error_result_already_exists.details,
        instance="string",
    )
```

**Extra router tests:**
```python
def test_create_product__conflict(
    mocker: MockerFixture,
    product_service: ProductService,
    product_create: ProductCreate,
    product_error_result_already_exists: ErrorResult,
) -> None:
    # Arrange
    current_user_id = "test-user-id"
    mocker.patch.object(product_service, "create", return_value=Err(product_error_result_already_exists))

    # Act & Assert
    with pytest.raises(HTTPException) as exc_info:
        create_product(
            product=product_create, product_service=product_service, current_user_id=current_user_id
        )

    assert exc_info.value.status_code == HTTP_409_CONFLICT
    assert exc_info.value.detail == product_error_result_already_exists.details


def test_update_product__conflict(
    mocker: MockerFixture,
    product_service: ProductService,
    product_id: uuid.UUID,
    product_update: ProductUpdate,
    product_error_result_already_exists: ErrorResult,
) -> None:
    # Arrange
    current_user_id = "test-user-id"
    mocker.patch.object(product_service, "update", return_value=Err(product_error_result_already_exists))

    # Act & Assert
    with pytest.raises(HTTPException) as exc_info:
        update_product(
            product_id=product_id,
            product=product_update,
            product_service=product_service,
            current_user_id=current_user_id,
        )

    assert exc_info.value.status_code == HTTP_409_CONFLICT
    assert exc_info.value.detail == product_error_result_already_exists.details
```

## Running the Tests

```bash
PYTHONPATH=`pwd` uv run pytest src/tests/unit/mappers/test_task_mapper.py -vv
PYTHONPATH=`pwd` uv run pytest src/tests/unit/services/test_task_service.py -vv
PYTHONPATH=`pwd` uv run pytest src/tests/unit/routers/test_task.py -vv
```

Or validate everything at once:
```bash
bash .claude/skills/add-entity-tests/scripts/validate.sh task
```