from uuid import UUID

from fastapi import APIRouter, Depends, Query
from result import Err, Ok
from starlette.status import HTTP_201_CREATED, HTTP_204_NO_CONTENT

from src.api_server.deps import get_user_service
from src.api_server.helpers.error_response import http_exception_from_error
from src.api_server.responses import response_409
from src.constants import (
    DEFAULT_PAGE_NUMBER,
    DEFAULT_PAGE_SIZE,
    OMIT_PAGINATION,
    PAGE_NUMBER,
    PAGE_SIZE,
    SORT_BY,
    SORT_DIRECTION,
    USER_PREFIX,
)
from src.mappers.user import to_user_entity
from src.models.base import ModelList
from src.models.enums.sort_direction import SortDirection
from src.models.user import User, UserCreate, UserUpdate
from src.services.user_service import UserService

router = APIRouter(prefix=f"/{USER_PREFIX}")


@router.get("/", response_model=ModelList[User])
async def get_users(
    page_number: int = Query(default=DEFAULT_PAGE_NUMBER, alias=PAGE_NUMBER, gt=0),
    page_size: int = Query(default=DEFAULT_PAGE_SIZE, alias=PAGE_SIZE, gt=0),
    omit_pagination: bool = Query(default=False, alias=OMIT_PAGINATION),
    is_active: bool | None = Query(default=None),
    sort_by: str | None = Query(default=None, alias=SORT_BY),
    sort_direction: SortDirection = Query(default=SortDirection.ascending, alias=SORT_DIRECTION),
    user_service: UserService = Depends(get_user_service),
) -> ModelList[User]:
    match await user_service.get_page(page_number, page_size, omit_pagination, is_active, sort_by, sort_direction):
        case Ok(result):
            return result
        case Err(error):
            raise http_exception_from_error(error)
        case _:
            raise http_exception_from_error()


@router.get("/{user_id}", response_model=User)
async def get_user_by_id(user_id: UUID, user_service: UserService = Depends(get_user_service)) -> User:
    match await user_service.get_by_id(user_id):
        case Ok(result):
            return result
        case Err(error):
            raise http_exception_from_error(error)
        case _:
            raise http_exception_from_error()


@router.post("/", response_model=User, status_code=HTTP_201_CREATED, responses=response_409)
async def create_user(
    user: UserCreate,
    user_service: UserService = Depends(get_user_service),
    # Note: In real implementation, you would get user_id from authentication context
    current_user_id: str = "system",  # Placeholder for actual user authentication
) -> User:
    match await user_service.create(user, to_user_entity, current_user_id):  # ty: ignore[invalid-argument-type]
        case Ok(result):
            return result
        case Err(error):
            raise http_exception_from_error(error)
        case _:
            raise http_exception_from_error()


@router.patch("/{user_id}", response_model=User, responses=response_409)
async def update_user(
    user_id: UUID,
    user: UserUpdate,
    user_service: UserService = Depends(get_user_service),
    # Note: In real implementation, you would get user_id from authentication context
    current_user_id: str = "system",  # Placeholder for actual user authentication
) -> User:
    match await user_service.update(user_id, user, current_user_id):
        case Ok(result):
            return result
        case Err(error):
            raise http_exception_from_error(error)
        case _:
            raise http_exception_from_error()


@router.delete("/{user_id}", status_code=HTTP_204_NO_CONTENT)
async def delete_user(user_id: UUID, user_service: UserService = Depends(get_user_service)) -> None:
    match await user_service.delete(user_id):
        case Err(error):
            raise http_exception_from_error(error)
