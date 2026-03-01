# Quick Reference: Critical Patterns

Use this as a checklist when generating entity tests. For detailed explanations, see CORRECTIONS.md.

## ✓ Correct Patterns

### Fixtures

```python
from datetime import datetime, timezone
from uuid import UUID
import pytest

# UUID fixtures
@pytest.fixture(scope="session")
def task_id() -> UUID:
    return UUID("12345678-1234-5678-1234-567812345678")

# Create model fixture
@pytest.fixture(scope="session")
def task_create(user_id: UUID) -> TaskCreate:
    return TaskCreate(
        title="Sample Task",
        description="Description",
        due_date=datetime(2024, 12, 31, 23, 59, 59, tzinfo=timezone.utc),
        priority=1,
        is_completed=False,
        user_id=user_id,
    )

# Read model fixture (explicit fields)
@pytest.fixture(scope="session")
def task(task_id: UUID, task_create: TaskCreate) -> Task:
    return Task(
        id=task_id,
        title=task_create.title,  # Explicit fields
        description=task_create.description,
        due_date=task_create.due_date,
        priority=task_create.priority,
        is_completed=task_create.is_completed,
        user_id=task_create.user_id,
        is_active=True,
        created_date=datetime(2024, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
        last_modified_date=datetime(2024, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
        created_by_user_id="system",
        last_modified_by_user_id="system",
    )

# ModelList fixture (items and total ONLY)
@pytest.fixture(scope="session")
def tasks(task: Task) -> ModelList[Task]:
    return ModelList[Task](
        items=[task],
        total=1,
    )

# Error result fixture
@pytest.fixture(scope="session")
def task_error_result_not_found() -> ErrorResult:
    return ErrorResult(
        status=ErrorStatus.NOT_FOUND_ERROR,  # NOT_FOUND_ERROR not NOT_FOUND
        details="Task not found",  # details not message
    )
```

### Service Tests

```python
from pytest_mock import MockerFixture
from result import Ok

def test_get_page__with_filters(
    task_service: TaskService,  # From conftest.py
    task_entity: TaskEntity,
    task: Task,
    user_id: UUID,
    mocker: MockerFixture,
) -> None:
    # Arrange
    mocker.patch.object(
        TaskDataService,  # Patch the CLASS not instance
        "get_by_page",  # get_by_page not get_page
        return_value=([task_entity], 1),  # Tuple: ([entities], count)
    )

    # Act
    result = task_service.get_page(
        page_number=1,
        page_size=10,
        omit_pagination=False,
        is_completed=True,
        user_id=user_id,
        sort_by="title",
        sort_direction=SortDirection.ascending,
    )

    # Assert
    assert result == Ok(ModelList[Task](items=[task], total=1))

    # Verify filters
    call_args = TaskDataService.get_by_page.call_args  # type: ignore
    filters = call_args.kwargs["filters"]

    # Check filter using entity field object
    is_completed_filter = next(
        (f for f in filters if isinstance(f, EqualsFilter) and f.field == TaskEntity.is_completed),
        None
    )
    assert is_completed_filter is not None
    assert is_completed_filter.value == True
```

### Service Implementation (if you need to fix it)

```python
from src.database.entities.task import TaskEntity

def get_page(
    self,
    page_number: int,
    page_size: int,
    omit_pagination: bool,
    is_completed: bool | None = None,
    user_id: UUID | None = None,
    sort_by: str | None = None,
    sort_direction: SortDirection = SortDirection.ascending,
) -> Result[ModelList[Task], ErrorResult]:
    filters = []
    if is_completed is not None:
        # Use field=EntityType.field_name NOT field_name="string"
        filters.append(EqualsFilter(field=TaskEntity.is_completed, value=is_completed))
    if user_id is not None:
        filters.append(EqualsFilter(field=TaskEntity.user_id, value=user_id))

    return super().get_page(
        page_number=page_number,
        page_size=page_size,
        omit_pagination=omit_pagination,
        filters=filters,
        sort_by=sort_by,
        sort_direction=sort_direction,
    )
```

### Router Tests (Unit Style)

```python
import pytest
from fastapi import HTTPException
from pytest_mock import MockerFixture
from result import Err, Ok

def test_get_tasks(
    mock_task_service: MagicMock,  # Mock service passed as parameter
    tasks: ModelList[Task],
) -> None:
    # Arrange
    mock_task_service.get_page.return_value = Ok(tasks)

    # Act
    result = get_tasks(
        page_number=1,
        page_size=10,
        omit_pagination=False,
        is_completed=None,
        user_id=None,
        sort_by=None,
        sort_direction=SortDirection.ascending,
        task_service=mock_task_service,  # Pass as parameter
    )

    # Assert
    assert result == tasks
    mock_task_service.get_page.assert_called_once_with(
        1, 10, False, None, None, None, SortDirection.ascending
    )

def test_get_task_by_id__task_not_found(
    mock_task_service: MagicMock,
    task_id: UUID,
    task_error_result_not_found: ErrorResult,
) -> None:
    # Arrange
    mock_task_service.get_by_id.return_value = Err(task_error_result_not_found)

    # Act & Assert
    with pytest.raises(HTTPException) as exc_info:
        get_task_by_id(task_id=task_id, task_service=mock_task_service)

    assert exc_info.value.status_code == 404
    assert "Task not found" in exc_info.value.detail
```

### conftest.py Fixtures

```python
from sqlalchemy.orm import Session
from src.data_services.task_data_service import TaskDataService
from src.services.task_service import TaskService

# Add to pytest_plugins
pytest_plugins = [
    "src.tests.fixtures.user_fixtures",
    "src.tests.fixtures.task_fixtures",  # Add this
]

# Add service fixtures
@pytest.fixture
def task_data_service(session: Session) -> TaskDataService:
    return TaskDataService(session=session)

@pytest.fixture
def task_service(task_data_service: TaskDataService) -> TaskService:
    return TaskService(data_service=task_data_service)
```

## ✗ Common Mistakes

### DON'T Use These Patterns

```python
# ✗ WRONG: ModelList with wrong fields
ModelList[Task](data=[task], total_count=1, page_number=1, page_size=10)

# ✗ WRONG: ErrorStatus enums
ErrorStatus.NOT_FOUND
ErrorStatus.VALIDATION_ERROR

# ✗ WRONG: ErrorResult with message
ErrorResult(status=ErrorStatus.NOT_FOUND, message="Not found")

# ✗ WRONG: Filter with field_name string
EqualsFilter(field_name="is_completed", value=True)

# ✗ WRONG: Checking filter with string
assert filters[0].field_name == "is_completed"

# ✗ WRONG: Mock get_page method
mock_service.get_page.return_value = Ok([entity])

# ✗ WRONG: Service fixture without session
@pytest.fixture
def task_service(mock_task_data_service: MagicMock) -> TaskService:
    service = TaskService()
    service.data_service = mock_task_data_service
    return service

# ✗ WRONG: Using datetime.now() in fixtures
created_date=datetime.now(timezone.utc)

# ✗ WRONG: Using **model_dump() in fixtures
return Task(id=task_id, **task_create.model_dump(), is_active=True)
```

## Checklist Before Running Tests

- [ ] ModelList uses `items` and `total` only
- [ ] ErrorStatus uses `NOT_FOUND_ERROR` and `BAD_REQUEST`
- [ ] ErrorResult uses `details` parameter
- [ ] Service fixtures in conftest.py with session parameter
- [ ] Mocking `get_by_page` returning tuple `([entities], count)`
- [ ] Filters use `field=EntityType.field_name`
- [ ] Filter assertions check `filter.field == EntityType.field_name`
- [ ] Explicit datetime values (not `datetime.now()`)
- [ ] All fixtures use `scope="session"`
- [ ] Explicit field assignments (no `**model_dump()`)

## Reference Implementation

**Task entity tests are the canonical reference:**
- `src/tests/fixtures/task_fixtures.py`
- `src/tests/unit/mappers/test_task_mapper.py`
- `src/tests/unit/services/test_task_service.py`
- `src/tests/unit/routers/test_task.py`

**When in doubt, copy these patterns exactly.**
