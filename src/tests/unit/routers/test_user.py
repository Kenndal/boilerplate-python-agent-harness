from unittest.mock import AsyncMock
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
        new_callable=AsyncMock,
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
        new_callable=AsyncMock,
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
        new_callable=AsyncMock,
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
    mocker.patch.object(UserService, "create", new_callable=AsyncMock, return_value=Ok(user))

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
    mocker.patch.object(UserService, "update", new_callable=AsyncMock, return_value=Ok(user))

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
    mocker.patch.object(UserService, "update", new_callable=AsyncMock, return_value=Err(user_error_result_not_found))

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
        new_callable=AsyncMock,
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
        new_callable=AsyncMock,
        return_value=Err(user_error_result_not_found),
    )

    # Act
    response = client.delete(f"{USER_URL}/{user_id}")

    # Assert
    assert response.status_code == HTTP_404_NOT_FOUND
    assert is_expected_result_json(response.json(), user_not_found)
