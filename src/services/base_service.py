import logging
from typing import Any
from uuid import UUID

from pydantic import BaseModel
from result import Err, Ok, Result

from src.data_services.crud import Crud, ModelToEntityMapper
from src.database.entities.base import Base
from src.models.base import ModelList
from src.models.enums.error_status import ErrorStatus
from src.models.error_result import ErrorResult
from src.utils.exceptions import CrudError, CrudUniqueValidationError

logger = logging.getLogger(__name__)


class BaseService[Entity: Base, Model: BaseModel, CreateModel: BaseModel, UpdateModel: BaseModel]:
    GET_BY_ID_NOT_FOUND_MSG = "{model_class} with id {id} not found"
    GET_BY_IDS_NOT_FOUND_MSG = "One or more {model_class}s with id in {id} not found"
    CREATE_UNIQUE_VALIDATION_MSG = "Unknown CrudUniqueValidationError"
    UPDATE_UNIQUE_VALIDATION_MSG = "Unknown CrudUniqueValidationError"
    model_class: type[Model]

    def __init__(self, data_service: Crud[Entity, CreateModel, UpdateModel]) -> None:
        self.data_service = data_service

    @staticmethod
    def _error_response(details: str, status: ErrorStatus) -> ErrorResult:
        return ErrorResult(status=status, details=details)

    def _not_found_error_response(self, details: str) -> ErrorResult:
        return self._error_response(details, ErrorStatus.NOT_FOUND_ERROR)

    def build_create_crud_unique_validation_error_msg(self) -> str:
        return ("Failed to create new {model_class} - " + self.CREATE_UNIQUE_VALIDATION_MSG).format(
            model_class=self.model_class.__name__
        )

    def build_update_crud_unique_validation_error_msg(self, entity_id: UUID) -> str:
        return ("Failed to update {model_class} with id {id} - " + self.UPDATE_UNIQUE_VALIDATION_MSG).format(
            model_class=self.model_class.__name__, id=str(entity_id)
        )

    async def get_page(
        self,
        page_number: int,
        page_size: int,
        omit_pagination: bool,
        *args: Any,  # noqa: ANN401
        **kwargs: Any,  # noqa: ANN401
    ) -> Result[ModelList[Model], ErrorResult]:
        try:
            entities, total = await self.data_service.get_by_page(
                page_number=page_number,
                page_size=page_size,
                omit_pagination=omit_pagination,
                **kwargs,
            )
        except CrudError as e:
            return Err(self._error_response(status=ErrorStatus.INTERNAL_ERROR, details=str(e)))

        models = [self.model_class.model_validate(e) for e in entities]
        return Ok(ModelList[Model](items=models, total=total))

    async def get_by_id(self, entity_id: UUID, with_for_update: bool = False) -> Result[Model, ErrorResult]:
        try:
            entity = await self.data_service.get_by_id(entity_id=entity_id, with_for_update=with_for_update)
        except CrudError as e:
            return Err(self._error_response(status=ErrorStatus.INTERNAL_ERROR, details=str(e)))

        if entity is None:
            return Err(
                self._not_found_error_response(
                    self.GET_BY_ID_NOT_FOUND_MSG.format(model_class=self.model_class.__name__, id=str(entity_id))
                )
            )
        return Ok(self.model_class.model_validate(entity))

    async def create(
        self,
        model: CreateModel,
        mapper: ModelToEntityMapper[Entity, CreateModel],
        user_id: str,
        *args: Any,  # noqa: ANN401
        **kwargs: Any,  # noqa: ANN401
    ) -> Result[Model, ErrorResult]:
        try:
            entity = await self.data_service.create(create_model=model, mapper=mapper, user_id=user_id)
        except CrudUniqueValidationError as e:
            logger.error(str(e))
            return Err(
                self._error_response(
                    status=ErrorStatus.CONFLICT, details=self.build_create_crud_unique_validation_error_msg()
                )
            )
        except CrudError as e:
            return Err(self._error_response(status=ErrorStatus.INTERNAL_ERROR, details=str(e)))
        return Ok(self.model_class.model_validate(entity))

    async def update(
        self,
        entity_id: UUID,
        model: UpdateModel,
        user_id: str,
        *args: Any,  # noqa: ANN401
        **kwargs: Any,  # noqa: ANN401
    ) -> Result[Model, ErrorResult]:
        try:
            entity_exists = await self.data_service.entity_exists(entity_id=entity_id)
        except CrudError as e:
            return Err(self._error_response(status=ErrorStatus.INTERNAL_ERROR, details=str(e)))

        if not entity_exists:
            return Err(
                self._not_found_error_response(
                    self.GET_BY_ID_NOT_FOUND_MSG.format(model_class=self.model_class.__name__, id=str(entity_id))
                )
            )

        try:
            entity = await self.data_service.update(entity_id=entity_id, update_model=model, user_id=user_id)
        except CrudUniqueValidationError as e:
            logger.error(str(e))
            return Err(
                self._error_response(
                    status=ErrorStatus.CONFLICT,
                    details=self.build_update_crud_unique_validation_error_msg(entity_id=entity_id),
                )
            )
        except CrudError as e:
            return Err(self._error_response(status=ErrorStatus.INTERNAL_ERROR, details=str(e)))

        return Ok(self.model_class.model_validate(entity))

    async def delete(self, entity_id: UUID) -> Result[None, ErrorResult]:
        try:
            entity_exists = await self.data_service.entity_exists(entity_id=entity_id)
        except CrudError as e:
            return Err(self._error_response(status=ErrorStatus.INTERNAL_ERROR, details=str(e)))

        if not entity_exists:
            return Err(
                self._not_found_error_response(
                    self.GET_BY_ID_NOT_FOUND_MSG.format(model_class=self.model_class.__name__, id=str(entity_id))
                )
            )

        try:
            await self.data_service.delete(entity_id=entity_id)
        except CrudError as e:
            return Err(self._error_response(status=ErrorStatus.INTERNAL_ERROR, details=str(e)))

        return Ok(None)

    async def entity_exists(self, entity_id: UUID) -> Result[None, ErrorResult]:
        try:
            entity_exists = await self.data_service.entity_exists(entity_id=entity_id)
        except CrudError as e:
            return Err(self._error_response(status=ErrorStatus.INTERNAL_ERROR, details=str(e)))

        if not entity_exists:
            return Err(
                self._not_found_error_response(
                    self.GET_BY_ID_NOT_FOUND_MSG.format(model_class=self.model_class.__name__, id=str(entity_id))
                )
            )
        return Ok(None)
