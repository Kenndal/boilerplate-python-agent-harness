# Example: User Entity Tests

This example shows complete test coverage for the User entity.

## Entity Structure

```python
# src/database/entities/user.py
class UserEntity(Base, BaseAuditEntity):
    __tablename__ = "user"

    id: Mapped[UUID] = mapped_column(primary_key=True, index=True)
    first_name: Mapped[str]
    last_name: Mapped[str]
    username: Mapped[str] = mapped_column(unique=True, index=True)
    email: Mapped[str] = mapped_column(unique=True, index=True)
```

## Custom Filters

- `is_active: bool` - Filter by active status in get_page()

## Unique Constraints

- `username` - Must be unique
- `email` - Must be unique

## Generated Test Files

### 1. Fixtures (src/tests/fixtures/user_fixtures.py)

```python
from uuid import UUID, uuid4

import pytest
from starlette.status import HTTP_404_NOT_FOUND

from src.database.entities.user import UserEntity
from src.models.base import BaseAudit, ModelList
from src.models.enums.error_status import ErrorStatus
from src.models.error_result import ErrorResult
from src.models.problem_details import ProblemDetails
from src.models.user import User, UserCreate, UserUpdate


@pytest.fixture(scope="module")
def user_id() -> UUID:
    return uuid4()


@pytest.fixture
def user_create() -> UserCreate:
    return UserCreate(first_name="John", last_name="Doe", username="johndoe", email="john.doe@example.com")


@pytest.fixture
def user_update() -> UserUpdate:
    return UserUpdate(
        first_name="Jane", last_name="Smith", username="janesmith", email="jane.smith@example.com", is_active=False
    )


@pytest.fixture
def user(user_id: UUID, user_create: UserCreate, audit: BaseAudit) -> User:
    return User(id=user_id, is_active=True, **user_create.model_dump(), **audit.model_dump())


@pytest.fixture
def users(user: User) -> ModelList[User]:
    return ModelList[User](items=[user], total=1)


@pytest.fixture
def user_entity(user: User) -> UserEntity:
    return UserEntity(**user.model_dump())


@pytest.fixture
def user_error_result_not_found(user_id: UUID) -> ErrorResult:
    return ErrorResult(status=ErrorStatus.NOT_FOUND_ERROR, details=f"User with id {user_id} not found")


@pytest.fixture
def user_not_found(user_error_result_not_found: ErrorResult) -> ProblemDetails:
    return ProblemDetails(
        title="Not Found",
        detail=user_error_result_not_found.details,
        status=HTTP_404_NOT_FOUND,
    )


@pytest.fixture
def user_error_result_already_exists() -> ErrorResult:
    return ErrorResult(status=ErrorStatus.CONFLICT, details="User already exists")


@pytest.fixture
def user_already_exists(user_error_result_already_exists: ErrorResult) -> ProblemDetails:
    return ProblemDetails(
        title="Conflict",
        detail=user_error_result_already_exists.details,
        status=409,
    )
```

### 2. Mapper Tests (src/tests/unit/mappers/test_user_mapper.py)

```python
from uuid import UUID

from src.database.entities.user import UserEntity
from src.mappers.user import to_user_entity
from src.models.user import UserCreate


def test_to_user_entity(
    user_create: UserCreate,
    fake_user_id: str,
) -> None:
    # Act
    result = to_user_entity(user_create, fake_user_id)

    # Assert
    assert isinstance(result, UserEntity)
    assert isinstance(result.id, UUID)
    assert result.first_name == user_create.first_name
    assert result.last_name == user_create.last_name
    assert result.username == user_create.username
    assert result.email == user_create.email
    assert result.is_active is True
    assert result.created_by_user_id == fake_user_id
    assert result.last_modified_by_user_id == fake_user_id
```

### 3. Service Tests (src/tests/unit/services/test_user_service.py)

```python
from pytest_mock import MockerFixture
from result import Ok

from src.data_services.user_data_service import UserDataService
from src.database.entities.user import UserEntity
from src.models.base import ModelList
from src.models.user import User
from src.services.user_service import UserService


def test_get_page_with_is_active_filter(
    user_service: UserService,
    user_entity: UserEntity,
    user: User,
    mocker: MockerFixture,
) -> None:
    # Arrange
    mocker.patch.object(UserDataService, "get_by_page", return_value=([user_entity], 1))

    # Act
    result = user_service.get_page(page_number=1, page_size=10, omit_pagination=False, is_active=True)

    # Assert
    assert result == Ok(ModelList[User](items=[user], total=1))


def test_get_page_without_filters(
    user_service: UserService,
    user_entity: UserEntity,
    user: User,
    mocker: MockerFixture,
) -> None:
    # Arrange
    mocker.patch.object(UserDataService, "get_by_page", return_value=([user_entity], 1))

    # Act
    result = user_service.get_page(page_number=1, page_size=10, omit_pagination=False)

    # Assert
    assert result == Ok(ModelList[User](items=[user], total=1))
```

### 4. Router Tests (src/tests/unit/routers/test_user.py)

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
)
from starlette.testclient import TestClient

from src.constants import USER_PREFIX, VERSION_PREFIX
from src.models.base import ModelList
from src.models.error_result import ErrorResult
from src.models.problem_details import ProblemDetails
from src.models.user import User, UserCreate, UserUpdate
from src.services.user_service import UserService
from src.tests.utils import is_expected_result_json

USER_URL = f"/{VERSION_PREFIX}/{USER_PREFIX}"


def test_get_users(
    client: TestClient,
    users: ModelList[User],
    mocker: MockerFixture,
) -> None:
    # Arrange
    mocker.patch.object(
        UserService,
        "get_page",
        return_value=Ok(users),
    )

    # Act
    response = client.get(USER_URL)

    # Assert
    assert response.status_code == HTTP_200_OK
    assert is_expected_result_json(response.json(), users)


def test_get_users__validation_error(client: TestClient) -> None:
    # Act
    response = client.get(f"{USER_URL}?pageNumber=True&pageSize=kek&omitPagination=2&sortBy=name")

    # Assert
    assert response.status_code == HTTP_400_BAD_REQUEST


def test_get_user_by_id(
    client: TestClient,
    user_id: UUID,
    user: User,
    mocker: MockerFixture,
) -> None:
    # Arrange
    mocker.patch.object(
        UserService,
        "get_by_id",
        return_value=Ok(user),
    )

    # Act
    response = client.get(f"{USER_URL}/{user_id}")

    # Assert
    assert response.status_code == HTTP_200_OK
    assert is_expected_result_json(response.json(), user)


def test_get_user_by_id__user_not_found(
    client: TestClient,
    user_error_result_not_found: ErrorResult,
    user_id: UUID,
    user_not_found: ProblemDetails,
    mocker: MockerFixture,
) -> None:
    # Arrange
    mocker.patch.object(
        UserService,
        "get_by_id",
        return_value=Err(user_error_result_not_found),
    )

    # Act
    response = client.get(f"{USER_URL}/{user_id}")

    # Assert
    assert response.status_code == HTTP_404_NOT_FOUND
    assert is_expected_result_json(response.json(), user_not_found)


def test_create_user(
    client: TestClient,
    user_create: UserCreate,
    user: User,
    mocker: MockerFixture,
) -> None:
    # Arrange
    mocker.patch.object(UserService, "create", return_value=Ok(user))

    # Act
    response = client.post(USER_URL, json=user_create.model_dump())

    # Assert
    assert response.status_code == HTTP_201_CREATED
    assert is_expected_result_json(response.json(), user)


@pytest.mark.filterwarnings("ignore::UserWarning")
def test_create_user__validation_error(client: TestClient, user_create: UserCreate) -> None:
    # Arrange
    user_create.first_name = 1  # type: ignore[assignment]

    # Act
    response = client.post(USER_URL, json=user_create.model_dump())

    # Assert
    assert response.status_code == HTTP_400_BAD_REQUEST


def test_update_user(
    client: TestClient, user_id: UUID, user_update: UserUpdate, user: User, mocker: MockerFixture
) -> None:
    # Arrange
    mocker.patch.object(UserService, "update", return_value=Ok(user))

    # Act
    response = client.patch(f"{USER_URL}/{user_id}", json=user_update.model_dump())

    # Assert
    assert response.status_code == HTTP_200_OK
    assert is_expected_result_json(response.json(), user)


def test_update_user__user_not_found(
    client: TestClient,
    user_id: UUID,
    user_update: UserUpdate,
    user_error_result_not_found: ErrorResult,
    user_not_found: ProblemDetails,
    mocker: MockerFixture,
) -> None:
    # Arrange
    mocker.patch.object(UserService, "update", return_value=Err(user_error_result_not_found))

    # Act
    response = client.patch(f"{USER_URL}/{user_id}", json=user_update.model_dump())

    # Assert
    assert response.status_code == HTTP_404_NOT_FOUND
    assert is_expected_result_json(response.json(), user_not_found)


@pytest.mark.filterwarnings("ignore::UserWarning")
def test_update_user__validation_error(client: TestClient, user_id: UUID, user_update: UserUpdate) -> None:
    # Arrange
    user_update.first_name = 1  # type: ignore[assignment]

    # Act
    response = client.patch(f"{USER_URL}/{user_id}", json=user_update.model_dump())

    # Assert
    assert response.status_code == HTTP_400_BAD_REQUEST


def test_delete_user(client: TestClient, user_id: UUID, mocker: MockerFixture) -> None:
    # Arrange
    mocker.patch.object(
        UserService,
        "delete",
        return_value=Ok(None),
    )
    # Act
    response = client.delete(f"{USER_URL}/{user_id}")

    # Assert
    assert response.status_code == HTTP_204_NO_CONTENT


def test_delete_user__user_not_found(
    client: TestClient,
    user_id: UUID,
    user_error_result_not_found: ErrorResult,
    user_not_found: ProblemDetails,
    mocker: MockerFixture,
) -> None:
    # Arrange
    mocker.patch.object(
        UserService,
        "delete",
        return_value=Err(user_error_result_not_found),
    )

    # Act
    response = client.delete(f"{USER_URL}/{user_id}")

    # Assert
    assert response.status_code == HTTP_404_NOT_FOUND
    assert is_expected_result_json(response.json(), user_not_found)
```

### 5. conftest.py Updates

```python
# Add to pytest_plugins list
pytest_plugins = [
    "src.tests.fixtures.user_fixtures",
]

# Add imports
from src.data_services.user_data_service import UserDataService
from src.services.user_service import UserService

# Add fixtures
@pytest.fixture
def user_data_service(session: Session) -> UserDataService:
    return UserDataService(session=session)


@pytest.fixture
def user_service(user_data_service: UserDataService) -> UserService:
    return UserService(data_service=user_data_service)
```

## Test Coverage

### Fixtures (10 fixtures)
- `user_id` - UUID for user
- `user_create` - Create model with sample data
- `user_update` - Update model with different sample data
- `user` - Complete User model (read model)
- `users` - ModelList containing one user
- `user_entity` - Database entity instance
- `user_error_result_not_found` - Error result for 404
- `user_not_found` - ProblemDetails for 404 response
- `user_error_result_already_exists` - Error result for 409
- `user_already_exists` - ProblemDetails for 409 response

### Mapper Tests (1 test)
- `test_to_user_entity` - Tests create model to entity transformation

### Service Tests (2 tests)
- `test_get_page_with_is_active_filter` - Tests filtering by is_active
- `test_get_page_without_filters` - Tests default list behavior

### Router Tests (10 tests)
- `test_get_users` - GET list success
- `test_get_users__validation_error` - GET list with bad query params
- `test_get_user_by_id` - GET by ID success
- `test_get_user_by_id__user_not_found` - GET by ID not found
- `test_create_user` - POST create success
- `test_create_user__validation_error` - POST create with invalid data
- `test_update_user` - PATCH update success
- `test_update_user__user_not_found` - PATCH update not found
- `test_update_user__validation_error` - PATCH update with invalid data
- `test_delete_user` - DELETE success
- `test_delete_user__user_not_found` - DELETE not found

## Running the Tests

```bash
# Run all user tests
PYTHONPATH=`pwd` uv run pytest src/tests/unit/mappers/test_user_mapper.py src/tests/unit/services/test_user_service.py src/tests/unit/routers/test_user.py -vv

# Run only mapper tests
PYTHONPATH=`pwd` uv run pytest src/tests/unit/mappers/test_user_mapper.py -vv

# Run only service tests
PYTHONPATH=`pwd` uv run pytest src/tests/unit/services/test_user_service.py -vv

# Run only router tests
PYTHONPATH=`pwd` uv run pytest src/tests/unit/routers/test_user.py -vv

# Run with coverage
PYTHONPATH=`pwd` uv run pytest src/tests/unit/mappers/test_user_mapper.py src/tests/unit/services/test_user_service.py src/tests/unit/routers/test_user.py --cov=src --cov-report=html
```
