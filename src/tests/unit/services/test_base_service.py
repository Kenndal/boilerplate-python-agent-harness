from functools import partial
from unittest.mock import AsyncMock
from uuid import UUID, uuid4

from pydantic import BaseModel
import pytest
from result import Err, Ok
from sqlalchemy.orm import Mapped, mapped_column

from src.database.entities.base import Base
from src.models.base import ModelList
from src.models.enums.error_status import ErrorStatus
from src.models.error_result import ErrorResult
from src.services.base_service import BaseService
from src.utils.exceptions import CrudError, CrudUniqueValidationError


class Entity(Base):
    __tablename__ = "entity"

    id: Mapped[UUID] = mapped_column(primary_key=True)


class Model(BaseModel):
    id: UUID


class CreateModel(BaseModel):
    pass


class UpdateModel(BaseModel):
    pass


def mapper(model: CreateModel, user_id: str, entity_id: UUID) -> Entity:
    return Entity(id=entity_id)


TestBaseService = BaseService[Entity, Model, CreateModel, UpdateModel]


@pytest.fixture
def base_service() -> TestBaseService:
    srv = TestBaseService(data_service=AsyncMock())
    srv.model_class = Model
    return srv


async def test_get_page(base_service: TestBaseService) -> None:
    # Arrange
    page_number = 2
    page_size = 7
    omit_pagination = False
    other_arg = "test"
    model_id = uuid4()
    base_service.data_service = AsyncMock()
    base_service.data_service.get_by_page.return_value = ([{"id": model_id}], 1)

    # Act
    result = await base_service.get_page(
        page_number=page_number,
        page_size=page_size,
        omit_pagination=omit_pagination,
        other_arg=other_arg,
    )

    # Assert
    assert result == Ok(ModelList[Model](items=[Model(id=model_id)], total=1))
    base_service.data_service.get_by_page.assert_called_once_with(
        page_number=page_number,
        page_size=page_size,
        omit_pagination=omit_pagination,
        other_arg=other_arg,
    )


async def test_get_page__empty_results(base_service: TestBaseService) -> None:
    # Arrange
    page_number = 2
    page_size = 7
    omit_pagination = False
    base_service.data_service = AsyncMock()
    base_service.data_service.get_by_page.return_value = ([], 0)

    # Act
    result = await base_service.get_page(
        page_number=page_number,
        page_size=page_size,
        omit_pagination=omit_pagination,
    )

    # Assert
    assert result == Ok(ModelList[Model](items=[], total=0))


async def test_get_page__crud_error(base_service: TestBaseService) -> None:
    # Arrange
    page_number = 2
    page_size = 7
    omit_pagination = False
    error_details = "fake error"
    base_service.data_service = AsyncMock()
    base_service.data_service.get_by_page.side_effect = CrudError(error_details)

    # Act
    result = await base_service.get_page(
        page_number=page_number,
        page_size=page_size,
        omit_pagination=omit_pagination,
    )

    # Assert
    assert result == Err(ErrorResult(status=ErrorStatus.INTERNAL_ERROR, details=error_details))


async def test_get_by_id(base_service: TestBaseService) -> None:
    # Arrange
    entity_id = uuid4()
    base_service.data_service = AsyncMock()
    base_service.data_service.get_by_id.return_value = {"id": entity_id}

    # Act
    result = await base_service.get_by_id(entity_id)

    # Assert
    assert result == Ok(Model(id=entity_id))


async def test_get_by_id__crud_error(base_service: TestBaseService) -> None:
    # Arrange
    entity_id = uuid4()
    error_details = "fake error"
    base_service.data_service = AsyncMock()
    base_service.data_service.get_by_id.side_effect = CrudError(error_details)

    # Act
    result = await base_service.get_by_id(entity_id)

    # Assert
    assert result == Err(ErrorResult(status=ErrorStatus.INTERNAL_ERROR, details=error_details))


async def test_get_by_id__not_found(base_service: TestBaseService) -> None:
    # Arrange
    entity_id = uuid4()
    base_service.data_service = AsyncMock()
    base_service.data_service.get_by_id.return_value = None

    # Act
    result = await base_service.get_by_id(entity_id)

    # Assert
    assert result == Err(
        ErrorResult(
            status=ErrorStatus.NOT_FOUND_ERROR,
            details=base_service.GET_BY_ID_NOT_FOUND_MSG.format(
                model_class=base_service.model_class.__name__, id=entity_id
            ),
        )
    )


async def test_create(base_service: TestBaseService) -> None:
    # Arrange
    create_model = CreateModel()
    entity_id = uuid4()
    user_id = "fake_user_id"
    base_service.data_service = AsyncMock()
    base_service.data_service.create.return_value = {"id": entity_id}

    # Act
    result = await base_service.create(create_model, partial(mapper, entity_id=entity_id), user_id)

    # Assert
    assert result == Ok(Model(id=entity_id))


async def test_create__crud_error(base_service: TestBaseService) -> None:
    # Arrange
    create_model = CreateModel()
    entity_id = uuid4()
    user_id = "fake_user_id"
    error_details = "fake error"
    base_service.data_service = AsyncMock()
    base_service.data_service.create.side_effect = CrudError(error_details)

    # Act
    result = await base_service.create(create_model, partial(mapper, entity_id=entity_id), user_id)

    # Assert
    assert result == Err(ErrorResult(status=ErrorStatus.INTERNAL_ERROR, details=error_details))


async def test_create__crud_unique_validation_error(base_service: TestBaseService) -> None:
    # Arrange
    create_model = CreateModel()
    entity_id = uuid4()
    user_id = "fake_user_id"
    error_details = "fake error"
    base_service.data_service = AsyncMock()
    base_service.data_service.create.side_effect = CrudUniqueValidationError(error_details)

    # Act
    result = await base_service.create(create_model, partial(mapper, entity_id=entity_id), user_id)

    # Assert
    assert result == Err(
        ErrorResult(
            status=ErrorStatus.CONFLICT, details="Failed to create new Model - Unknown CrudUniqueValidationError"
        )
    )


async def test_update(base_service: TestBaseService) -> None:
    # Arrange
    update_model = UpdateModel()
    entity_id = uuid4()
    user_id = "fake_user_id"
    base_service.data_service = AsyncMock()
    base_service.data_service.entity_exists.return_value = True
    base_service.data_service.update.return_value = {"id": entity_id}

    # Act
    result = await base_service.update(entity_id, update_model, user_id)

    # Assert
    assert result == Ok(Model(id=entity_id))


async def test_update__not_found(base_service: TestBaseService) -> None:
    # Arrange
    update_model = UpdateModel()
    entity_id = uuid4()
    user_id = "fake_user_id"
    base_service.data_service = AsyncMock()
    base_service.data_service.entity_exists.return_value = False

    # Act
    result = await base_service.update(entity_id, update_model, user_id)

    # Assert
    assert result == Err(
        ErrorResult(
            status=ErrorStatus.NOT_FOUND_ERROR,
            details=base_service.GET_BY_ID_NOT_FOUND_MSG.format(
                model_class=base_service.model_class.__name__, id=entity_id
            ),
        )
    )


async def test_update__crud_error(base_service: TestBaseService) -> None:
    # Arrange
    update_model = UpdateModel()
    entity_id = uuid4()
    user_id = "fake_user_id"
    base_service.data_service = AsyncMock()
    base_service.data_service.entity_exists.return_value = True
    error_details = "fake error"
    base_service.data_service.update.side_effect = CrudError(error_details)

    # Act
    result = await base_service.update(entity_id, update_model, user_id)

    # Assert
    assert result == Err(ErrorResult(status=ErrorStatus.INTERNAL_ERROR, details=error_details))


async def test_update__crud_unique_validation_error(base_service: TestBaseService) -> None:
    # Arrange
    update_model = UpdateModel()
    entity_id = uuid4()
    user_id = "fake_user_id"
    error_details = "fake error"
    base_service.data_service = AsyncMock()
    base_service.data_service.entity_exists.return_value = True
    base_service.data_service.update.side_effect = CrudUniqueValidationError(error_details)

    # Act
    result = await base_service.update(entity_id, update_model, user_id)

    # Assert
    assert result == Err(
        ErrorResult(
            status=ErrorStatus.CONFLICT,
            details=f"Failed to update Model with id {entity_id} - Unknown CrudUniqueValidationError",
        )
    )


async def test_delete(base_service: TestBaseService) -> None:
    # Arrange
    entity_id = uuid4()
    base_service.data_service = AsyncMock()
    base_service.data_service.entity_exists.return_value = True

    # Act
    result = await base_service.delete(entity_id)

    # Assert
    assert result == Ok(None)


async def test_delete__not_found(base_service: TestBaseService) -> None:
    # Arrange
    entity_id = uuid4()
    base_service.data_service = AsyncMock()
    base_service.data_service.entity_exists.return_value = False

    # Act
    result = await base_service.delete(entity_id)

    # Assert
    assert result == Err(
        ErrorResult(
            status=ErrorStatus.NOT_FOUND_ERROR,
            details=base_service.GET_BY_ID_NOT_FOUND_MSG.format(
                model_class=base_service.model_class.__name__, id=entity_id
            ),
        )
    )


async def test_delete__crud_error(base_service: TestBaseService) -> None:
    # Arrange
    entity_id = uuid4()
    base_service.data_service = AsyncMock()
    base_service.data_service.entity_exists.return_value = True
    error_details = "fake error"
    base_service.data_service.delete.side_effect = CrudError(error_details)

    # Act
    result = await base_service.delete(entity_id)

    # Assert
    assert result == Err(ErrorResult(status=ErrorStatus.INTERNAL_ERROR, details=error_details))
