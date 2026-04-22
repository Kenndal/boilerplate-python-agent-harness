from result import Result

from src.data_services.filters import EqualsFilter
from src.data_services.user_data_service import UserDataService
from src.database.entities.user import UserEntity
from src.models.base import ModelList
from src.models.enums.sort_direction import SortDirection
from src.models.error_result import ErrorResult
from src.models.user import User, UserCreate, UserUpdate
from src.services.base_service import BaseService


class UserService(BaseService[UserEntity, User, UserCreate, UserUpdate]):
    data_service: UserDataService
    CREATE_UNIQUE_VALIDATION_MSG = "{model_class} with given username or email already exists"
    UPDATE_UNIQUE_VALIDATION_MSG = "{model_class} with given username or email already exists"
    model_class = User

    async def get_page(
        self,
        page_number: int,
        page_size: int,
        omit_pagination: bool,
        is_active: bool | None = None,
        sort_by: str | None = None,
        sort_direction: SortDirection = SortDirection.ascending,
    ) -> Result[ModelList[User], ErrorResult]:
        filters = []
        if is_active is not None:
            filters.append(EqualsFilter(field=UserEntity.is_active, value=is_active))

        return await super().get_page(
            page_number=page_number,
            page_size=page_size,
            omit_pagination=omit_pagination,
            filters=filters,
            sort_by=sort_by,
            sort_direction=sort_direction,
        )
