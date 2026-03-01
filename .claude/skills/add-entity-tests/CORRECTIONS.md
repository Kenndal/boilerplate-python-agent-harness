# Common Errors and Corrections

This file documents errors encountered during test generation and their corrections.

## 1. ModelList Field Names

**Error**: Used `data`, `total_count`, `page_number`, `page_size`
```python
# WRONG
ModelList[Task](
    data=[task],
    total_count=1,
    page_number=1,
    page_size=10,
)
```

**Correct**: Only `items` and `total`
```python
# CORRECT
ModelList[Task](
    items=[task],
    total=1,
)
```

## 2. ErrorStatus Enum Values

**Error**: Used `NOT_FOUND` and `VALIDATION_ERROR`
```python
# WRONG
ErrorStatus.NOT_FOUND
ErrorStatus.VALIDATION_ERROR
```

**Correct**: Use `NOT_FOUND_ERROR` and `BAD_REQUEST`
```python
# CORRECT
ErrorStatus.NOT_FOUND_ERROR
ErrorStatus.BAD_REQUEST
```

## 3. ErrorResult Fields

**Error**: Used `message` parameter
```python
# WRONG
ErrorResult(status=ErrorStatus.NOT_FOUND_ERROR, message="Task not found")
```

**Correct**: Use `details` parameter
```python
# CORRECT
ErrorResult(status=ErrorStatus.NOT_FOUND_ERROR, details="Task not found")
```

## 4. Service Fixture Initialization

**Error**: Created service without data_service or tried to set it afterward
```python
# WRONG
@pytest.fixture
def task_service(mock_task_data_service: MagicMock) -> TaskService:
    service = TaskService()
    service.data_service = mock_task_data_service
    return service
```

**Correct**: Use session fixture approach from conftest
```python
# CORRECT - In conftest.py
@pytest.fixture
def task_data_service(session: Session) -> TaskDataService:
    return TaskDataService(session=session)

@pytest.fixture
def task_service(task_data_service: TaskDataService) -> TaskService:
    return TaskService(data_service=task_data_service)
```

## 5. Data Service Method Name

**Error**: Mocked `get_page` method
```python
# WRONG
mock_task_data_service.get_page.return_value = Ok([task_entity])
```

**Correct**: Use `get_by_page` and return tuple
```python
# CORRECT
mocker.patch.object(TaskDataService, "get_by_page", return_value=([task_entity], 1))
```

## 6. Filter Initialization in Service

**Error**: Used `field_name` string parameter
```python
# WRONG
filters.append(EqualsFilter(field_name="is_completed", value=is_completed))
```

**Correct**: Use `field` with actual entity field object
```python
# CORRECT
filters.append(EqualsFilter(field=TaskEntity.is_completed, value=is_completed))
```

## 7. Filter Assertions in Tests

**Error**: Checked `filter.field_name` string
```python
# WRONG
assert filters[0].field_name == "is_completed"
```

**Correct**: Check `filter.field` object equality
```python
# CORRECT
assert filters[0].field == TaskEntity.is_completed
```

## 8. Service Test Result Assertions

**Error**: Used `.is_ok()`, `.unwrap()` with separate assertions
```python
# VERBOSE BUT WORKS
assert result.is_ok()
actual_model_list = result.unwrap()
assert actual_model_list.items == expected_model_list.items
assert actual_model_list.total == expected_model_list.total
```

**Better**: Use direct equality comparison
```python
# BETTER - More concise
assert result == Ok(ModelList[Task](items=[task], total=1))
```

## 9. Import Patterns

**Error**: Mixed import styles
```python
# INCONSISTENT
from uuid import UUID
import uuid
```

**Correct**: Use consistent imports
```python
# CORRECT - For fixtures (type hints need UUID)
from uuid import UUID
```

```python
# CORRECT - For tests (no type hints needed)
import uuid  # Then use uuid.UUID
```

## 10. Datetime in Fixtures

**Error**: Used `datetime.now(timezone.utc)`
```python
# INCONSISTENT - creates different times
created_date=datetime.now(timezone.utc)
```

**Correct**: Use explicit datetime for consistency
```python
# CORRECT - Same time every test run
created_date=datetime(2024, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
```

## 11. Router Test Filter Verification

**Error**: Didn't verify all filter properties
```python
# INCOMPLETE
filters = call_args.kwargs["filters"]
assert len(filters) == 2
```

**Correct**: Verify filter type, field, and value
```python
# COMPLETE
filters = call_args.kwargs["filters"]
assert len(filters) == 2

is_completed_filter = next((f for f in filters if isinstance(f, EqualsFilter) and f.field == TaskEntity.is_completed), None)
assert is_completed_filter is not None
assert is_completed_filter.value == is_completed

user_id_filter = next((f for f in filters if isinstance(f, EqualsFilter) and f.field == TaskEntity.user_id), None)
assert user_id_filter is not None
assert user_id_filter.value == user_id
```

## Summary Checklist

Before running tests, verify:

- [ ] ModelList uses `items` and `total` only
- [ ] ErrorStatus uses `NOT_FOUND_ERROR` and `BAD_REQUEST`
- [ ] ErrorResult uses `details` not `message`
- [ ] Service fixtures defined in conftest.py with session
- [ ] Mock `get_by_page` not `get_page`, return tuple `([entities], count)`
- [ ] Filters use `field=EntityType.field_name` not `field_name="string"`
- [ ] Filter assertions check `filter.field == EntityType.field_name`
- [ ] Datetime fixtures use explicit datetime, not `datetime.now()`
- [ ] All fixtures use `scope="session"` for performance
- [ ] Import styles are consistent per file type
