from unittest.mock import AsyncMock

from pytest_mock import MockerFixture
from result import Ok

from src.data_services.user_data_service import UserDataService
from src.database.entities.user import UserEntity
from src.models.base import ModelList
from src.models.user import User
from src.services.user_service import UserService


async def test_get_page_with_is_active_filter(
    user_service: UserService,
    user_entity: UserEntity,
    user: User,
    mocker: MockerFixture,
) -> None:
    # Arrange
    mocker.patch.object(UserDataService, "get_by_page", new_callable=AsyncMock, return_value=([user_entity], 1))

    # Act
    result = await user_service.get_page(page_number=1, page_size=10, omit_pagination=False, is_active=True)

    # Assert
    assert result == Ok(ModelList[User](items=[user], total=1))


async def test_get_page_without_filters(
    user_service: UserService,
    user_entity: UserEntity,
    user: User,
    mocker: MockerFixture,
) -> None:
    # Arrange
    mocker.patch.object(UserDataService, "get_by_page", new_callable=AsyncMock, return_value=([user_entity], 1))

    # Act
    result = await user_service.get_page(page_number=1, page_size=10, omit_pagination=False)

    # Assert
    assert result == Ok(ModelList[User](items=[user], total=1))
