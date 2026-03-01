# Example: Product Entity

This is a complete example of scaffolding a Product entity with the following specifications:

- **Entity Name:** Product
- **Fields:**
  - name: str (unique, indexed)
  - description: str
  - price: float
  - quantity: int
  - is_available: bool
- **Relationships:** None
- **Query Parameters:** is_available (bool)
- **Modifiable Fields:** name, description, price, quantity, is_available

## Generated Files

### 1. Entity (`src/database/entities/product.py`)

```python
from uuid import UUID

from sqlalchemy.orm import Mapped, mapped_column

from src.database.entities.base import Base, BaseAuditEntity


class ProductEntity(Base, BaseAuditEntity):
    __tablename__ = "product"

    id: Mapped[UUID] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(unique=True, index=True)
    description: Mapped[str]
    price: Mapped[float]
    quantity: Mapped[int]
    is_available: Mapped[bool]
```

### 2. Models (`src/models/product.py`)

```python
from uuid import UUID

from pydantic import ConfigDict

from src.models.base import BaseAudit, BaseModelWithConfig


class ProductCreate(BaseModelWithConfig):
    name: str
    description: str
    price: float
    quantity: int
    is_available: bool


class ProductUpdate(BaseModelWithConfig):
    name: str = ""
    description: str = ""
    price: float = 0.0
    quantity: int = 0
    is_available: bool = True


class Product(ProductCreate, BaseAudit):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    is_active: bool
```

### 3. Mapper (`src/mappers/product.py`)

```python
import uuid

from src.database.entities.product import ProductEntity
from src.models.product import ProductCreate


def to_product_entity(model: ProductCreate, user_id: str) -> ProductEntity:
    return ProductEntity(
        id=uuid.uuid4(),
        name=model.name,
        description=model.description,
        price=model.price,
        quantity=model.quantity,
        is_available=model.is_available,
        is_active=True,
        created_by_user_id=user_id,
        last_modified_by_user_id=user_id,
    )
```

### 4. Data Service (`src/data_services/product_data_service.py`)

```python
from sqlalchemy.orm import Session

from src.data_services.crud import Crud
from src.database.entities.product import ProductEntity
from src.models.product import ProductCreate, ProductUpdate


class ProductDataService(Crud[ProductEntity, ProductCreate, ProductUpdate]):
    def __init__(self, session: Session) -> None:
        super().__init__(
            session=session,
            entity_type=ProductEntity,
        )
```

### 5. Service (`src/services/product_service.py`)

```python
from result import Result

from src.data_services.filters import EqualsFilter
from src.data_services.product_data_service import ProductDataService
from src.database.entities.product import ProductEntity
from src.models.base import ModelList
from src.models.enums.sort_direction import SortDirection
from src.models.error_result import ErrorResult
from src.models.product import Product, ProductCreate, ProductUpdate
from src.services.base_service import BaseService


class ProductService(BaseService[ProductEntity, Product, ProductCreate, ProductUpdate]):
    data_service: ProductDataService
    CREATE_UNIQUE_VALIDATION_MSG = "Product with given name already exists"
    UPDATE_UNIQUE_VALIDATION_MSG = "Product with given name already exists"
    model_class = Product

    def get_page(
        self,
        page_number: int,
        page_size: int,
        omit_pagination: bool,
        is_available: bool | None = None,
        sort_by: str | None = None,
        sort_direction: SortDirection = SortDirection.ascending,
    ) -> Result[ModelList[Product], ErrorResult]:
        filters = []
        if is_available is not None:
            filters.append(EqualsFilter(ProductEntity.is_available, is_available))

        return super().get_page(
            page_number=page_number,
            page_size=page_size,
            omit_pagination=omit_pagination,
            filters=filters,
            sort_by=sort_by,
            sort_direction=sort_direction,
        )
```

### 6. Router (`src/api_server/routers/product.py`)

```python
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from result import Err, Ok
from starlette.status import HTTP_201_CREATED, HTTP_204_NO_CONTENT

from src.api_server.deps import get_product_service
from src.api_server.helpers.error_response import http_exception_from_error
from src.api_server.responses import response_404, response_409
from src.constants import (
    DEFAULT_PAGE_NUMBER,
    DEFAULT_PAGE_SIZE,
    OMIT_PAGINATION,
    PAGE_NUMBER,
    PAGE_SIZE,
    PRODUCTS_PREFIX,
    SORT_BY,
    SORT_DIRECTION,
)
from src.mappers.product import to_product_entity
from src.models.base import ModelList
from src.models.enums.sort_direction import SortDirection
from src.models.product import Product, ProductCreate, ProductUpdate
from src.services.product_service import ProductService

router = APIRouter(prefix=f"/{PRODUCTS_PREFIX}")


@router.get("/", response_model=ModelList[Product])
def get_products(
    page_number: int = Query(default=DEFAULT_PAGE_NUMBER, alias=PAGE_NUMBER, gt=0),
    page_size: int = Query(default=DEFAULT_PAGE_SIZE, alias=PAGE_SIZE, gt=0),
    omit_pagination: bool = Query(default=False, alias=OMIT_PAGINATION),
    is_available: bool | None = Query(default=None, alias="isAvailable"),
    sort_by: str | None = Query(default=None, alias=SORT_BY),
    sort_direction: SortDirection = Query(default=SortDirection.ascending, alias=SORT_DIRECTION),
    product_service: ProductService = Depends(get_product_service),
) -> ModelList[Product]:
    match product_service.get_page(page_number, page_size, omit_pagination, is_available, sort_by, sort_direction):
        case Ok(result):
            return result
        case Err(error):
            raise http_exception_from_error(error)
        case _:
            raise http_exception_from_error()


@router.get("/{product_id}", response_model=Product, responses=response_404)
def get_product_by_id(product_id: UUID, product_service: ProductService = Depends(get_product_service)) -> Product:
    match product_service.get_by_id(product_id):
        case Ok(result):
            return result
        case Err(error):
            raise http_exception_from_error(error)
        case _:
            raise http_exception_from_error()


@router.post("/", response_model=Product, status_code=HTTP_201_CREATED, responses=response_409)
def create_product(
    product: ProductCreate,
    product_service: ProductService = Depends(get_product_service),
    # Note: In real implementation, you would get user_id from authentication context
    current_user_id: str = "system",  # Placeholder for actual user authentication
) -> Product:
    match product_service.create(product, to_product_entity, current_user_id):  # ty: ignore[invalid-argument-type]
        case Ok(result):
            return result
        case Err(error):
            raise http_exception_from_error(error)
        case _:
            raise http_exception_from_error()


@router.patch("/{product_id}", response_model=Product, responses=response_404 | response_409)
def update_product(
    product_id: UUID,
    product: ProductUpdate,
    product_service: ProductService = Depends(get_product_service),
    # Note: In real implementation, you would get user_id from authentication context
    current_user_id: str = "system",  # Placeholder for actual user authentication
) -> Product:
    match product_service.update(product_id, product, current_user_id):
        case Ok(result):
            return result
        case Err(error):
            raise http_exception_from_error(error)
        case _:
            raise http_exception_from_error()


@router.delete("/{product_id}", status_code=HTTP_204_NO_CONTENT, responses=response_404)
def delete_product(product_id: UUID, product_service: ProductService = Depends(get_product_service)) -> None:
    match product_service.delete(product_id):
        case Err(error):
            raise http_exception_from_error(error)
```

### 7. Dependencies Update (`src/api_server/deps.py`)

Add these imports at the top:

```python
from src.data_services.product_data_service import ProductDataService
from src.services.product_service import ProductService
```

Add these functions at the end:

```python


def get_product_data_service(db_session: Session = Depends(get_db)) -> ProductDataService:
    return ProductDataService(session=db_session)


def get_product_service(product_data_service: ProductDataService = Depends(get_product_data_service)) -> ProductService:
    return ProductService(data_service=product_data_service)
```

### 8. Constants Update (`src/constants/__init__.py`)

Add:

```python
PRODUCTS_PREFIX = "products"
```

### 9. Router Registration (`src/api_server/main.py`)

Add import:

```python
from src.api_server.routers import product
```

Add router registration in `build_app()`:

```python
    _app.include_router(product.router, tags=["products"], prefix=f"/{VERSION_PREFIX}")
```

## Endpoint Responses Explanation

Since ProductEntity has a **unique constraint** on the `name` field, the endpoints have the following responses:

- **GET /v1/products** - No special responses (empty list is valid)
- **GET /v1/products/{product_id}** - `responses=response_404` (returns 404 if product not found)
- **POST /v1/products** - `responses=response_409` (returns 409 if name already exists)
- **PATCH /v1/products/{product_id}** - `responses=response_404 | response_409` (returns 404 if not found OR 409 if updated name conflicts)
- **DELETE /v1/products/{product_id}** - `responses=response_404` (returns 404 if product not found)

## API Endpoints

After scaffolding, the following endpoints are available:

- `GET /v1/products` - List all products with pagination and filters
  - Query params: pageNumber, pageSize, omitPagination, isAvailable, sortBy, sortDirection
- `GET /v1/products/{product_id}` - Get a product by ID (404 if not found)
- `POST /v1/products` - Create a new product (409 if name already exists)
- `PATCH /v1/products/{product_id}` - Update a product (404 if not found, 409 if name conflicts)
- `DELETE /v1/products/{product_id}` - Delete a product (404 if not found, soft delete)

## Database Migration

```bash
make db_migrate message="add_product"
make db_upgrade
```

## Testing

After running `make start`, test the endpoints at: http://localhost:5000/docs

---

# Example with Relationships: Order Entity

This example demonstrates creating an entity with a **many-to-one** relationship using the `TYPE_CHECKING` pattern to avoid circular imports.

## Specifications

- **Entity Name:** Order
- **Fields:**
  - order_number: str (unique, indexed)
  - total_amount: float
  - status: str
  - user_id: UUID (foreign key to User)
- **Relationships:** many-to-one with User
- **Query Parameters:** status (str), user_id (UUID)
- **Modifiable Fields:** status, total_amount

## Key Files

### 1. Entity with TYPE_CHECKING (`src/database/entities/order.py`)

```python
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database.entities.base import Base, BaseAuditEntity

if TYPE_CHECKING:
    from src.database.entities.user import UserEntity


class OrderEntity(Base, BaseAuditEntity):
    __tablename__ = "order"

    id: Mapped[UUID] = mapped_column(primary_key=True, index=True)
    order_number: Mapped[str] = mapped_column(unique=True, index=True)
    total_amount: Mapped[float]
    status: Mapped[str]
    user_id: Mapped[UUID] = mapped_column(ForeignKey("user.id"), index=True)

    # Relationships
    user: Mapped["UserEntity"] = relationship(back_populates="orders")
```

**Key Points:**
- Import `TYPE_CHECKING` from `typing`
- Import related entity (`UserEntity`) inside `if TYPE_CHECKING:` block
- Use string forward reference in relationship: `Mapped["UserEntity"]`
- Foreign key references table name and column: `ForeignKey("user.id")`
- Add index on foreign key for query performance

### 2. Update Related Entity (`src/database/entities/user.py`)

Add back-reference to UserEntity:

```python
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database.entities.base import Base, BaseAuditEntity

if TYPE_CHECKING:
    from src.database.entities.order import OrderEntity


class UserEntity(Base, BaseAuditEntity):
    __tablename__ = "user"

    id: Mapped[UUID] = mapped_column(primary_key=True, index=True)
    first_name: Mapped[str]
    last_name: Mapped[str]
    username: Mapped[str] = mapped_column(unique=True, index=True)
    email: Mapped[str] = mapped_column(unique=True, index=True)

    # Relationships
    orders: Mapped[list["OrderEntity"]] = relationship(back_populates="user")
```

### 3. Models with Foreign Key (`src/models/order.py`)

```python
from uuid import UUID

from pydantic import ConfigDict

from src.models.base import BaseAudit, BaseModelWithConfig


class OrderCreate(BaseModelWithConfig):
    order_number: str
    total_amount: float
    status: str
    user_id: UUID  # Foreign key included in Create model


class OrderUpdate(BaseModelWithConfig):
    status: str = ""
    total_amount: float | None = None
    is_active: bool = True


class Order(OrderCreate, BaseAudit):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    is_active: bool
```

**Key Points:**
- Include `user_id: UUID` in Create model for foreign key
- Update model only includes fields that should be modifiable
- Foreign key IDs are typically not modifiable after creation

### 4. Service with Relationship Filters (`src/services/order_service.py`)

```python
from uuid import UUID

from result import Result

from src.data_services.filters import EqualsFilter
from src.data_services.order_data_service import OrderDataService
from src.database.entities.order import OrderEntity
from src.models.base import ModelList
from src.models.enums.sort_direction import SortDirection
from src.models.error_result import ErrorResult
from src.models.order import Order, OrderCreate, OrderUpdate
from src.services.base_service import BaseService


class OrderService(BaseService[OrderEntity, Order, OrderCreate, OrderUpdate]):
    data_service: OrderDataService
    CREATE_UNIQUE_VALIDATION_MSG = "{model_class} with given {unique_fields} already exists"
    UPDATE_UNIQUE_VALIDATION_MSG = "{model_class} with given {unique_fields} already exists"
    model_class = Order

    def get_page(
        self,
        page_number: int,
        page_size: int,
        omit_pagination: bool,
        status: str | None = None,
        user_id: UUID | None = None,
        sort_by: str | None = None,
        sort_direction: SortDirection = SortDirection.ascending,
    ) -> Result[ModelList[Order], ErrorResult]:
        filters = []
        if status is not None:
            filters.append(EqualsFilter(field="status", value=status))
        if user_id is not None:
            filters.append(EqualsFilter(field="user_id", value=user_id))

        return super().get_page(
            page_number=page_number,
            page_size=page_size,
            omit_pagination=omit_pagination,
            filters=filters,
            sort_by=sort_by,
            sort_direction=sort_direction,
        )
```

**Key Points:**
- Add foreign key (`user_id`) as optional filter parameter
- Use `EqualsFilter` for filtering by relationship ID
- This allows querying: "Get all orders for user X"

### 4. Router with Unique Constraints (`src/api_server/routers/order.py`)

Since OrderEntity has a **unique constraint** on `order_number`, the router must handle 409 conflicts:

```python
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from result import Err, Ok
from starlette.status import HTTP_201_CREATED, HTTP_204_NO_CONTENT

from src.api_server.deps import get_order_service
from src.api_server.helpers.error_response import http_exception_from_error
from src.api_server.responses import response_404, response_409
from src.constants import (
    DEFAULT_PAGE_NUMBER,
    DEFAULT_PAGE_SIZE,
    OMIT_PAGINATION,
    ORDERS_PREFIX,
    PAGE_NUMBER,
    PAGE_SIZE,
    SORT_BY,
    SORT_DIRECTION,
)
from src.mappers.order import to_order_entity
from src.models.base import ModelList
from src.models.enums.sort_direction import SortDirection
from src.models.order import Order, OrderCreate, OrderUpdate
from src.services.order_service import OrderService

router = APIRouter(prefix=f"/{ORDERS_PREFIX}")


@router.get("/", response_model=ModelList[Order])
def get_orders(
    page_number: int = Query(default=DEFAULT_PAGE_NUMBER, alias=PAGE_NUMBER, gt=0),
    page_size: int = Query(default=DEFAULT_PAGE_SIZE, alias=PAGE_SIZE, gt=0),
    omit_pagination: bool = Query(default=False, alias=OMIT_PAGINATION),
    status: str | None = Query(default=None),
    user_id: UUID | None = Query(default=None, alias="userId"),
    sort_by: str | None = Query(default=None, alias=SORT_BY),
    sort_direction: SortDirection = Query(default=SortDirection.ascending, alias=SORT_DIRECTION),
    order_service: OrderService = Depends(get_order_service),
) -> ModelList[Order]:
    match order_service.get_page(page_number, page_size, omit_pagination, status, user_id, sort_by, sort_direction):
        case Ok(result):
            return result
        case Err(error):
            raise http_exception_from_error(error)
        case _:
            raise http_exception_from_error()


@router.get("/{order_id}", response_model=Order, responses=response_404)
def get_order_by_id(order_id: UUID, order_service: OrderService = Depends(get_order_service)) -> Order:
    match order_service.get_by_id(order_id):
        case Ok(result):
            return result
        case Err(error):
            raise http_exception_from_error(error)
        case _:
            raise http_exception_from_error()


@router.post("/", response_model=Order, status_code=HTTP_201_CREATED, responses=response_409)
def create_order(
    order: OrderCreate,
    order_service: OrderService = Depends(get_order_service),
    current_user_id: str = "system",
) -> Order:
    match order_service.create(order, to_order_entity, current_user_id):  # ty: ignore[invalid-argument-type]
        case Ok(result):
            return result
        case Err(error):
            raise http_exception_from_error(error)
        case _:
            raise http_exception_from_error()


@router.patch("/{order_id}", response_model=Order, responses=response_404 | response_409)
def update_order(
    order_id: UUID,
    order: OrderUpdate,
    order_service: OrderService = Depends(get_order_service),
    current_user_id: str = "system",
) -> Order:
    match order_service.update(order_id, order, current_user_id):
        case Ok(result):
            return result
        case Err(error):
            raise http_exception_from_error(error)
        case _:
            raise http_exception_from_error()


@router.delete("/{order_id}", status_code=HTTP_204_NO_CONTENT, responses=response_404)
def delete_order(order_id: UUID, order_service: OrderService = Depends(get_order_service)) -> None:
    match order_service.delete(order_id):
        case Err(error):
            raise http_exception_from_error(error)
```

**Important:** Order has `unique=True` on `order_number`, so:
- POST returns 409 if order_number already exists
- PATCH returns 404 if not found OR 409 if updated order_number conflicts
- Import both `response_404` and `response_409`

## Why TYPE_CHECKING?

Without `TYPE_CHECKING`, you would get circular import errors:
- `order.py` imports `UserEntity` from `user.py`
- `user.py` imports `OrderEntity` from `order.py`
- Python cannot resolve this circular dependency

**Solution:**
1. Import related entities only under `if TYPE_CHECKING:` (never executed at runtime)
2. Use string forward references in type hints: `Mapped["UserEntity"]`
3. Type checkers (mypy, ty) can still validate types
4. No circular imports at runtime!

This pattern is essential for bidirectional relationships in SQLAlchemy with proper type safety.

---

# Example Without Unique Constraints: Task Entity

This example demonstrates creating an entity **without unique constraints**, showing the difference in endpoint responses.

## Specifications

- **Entity Name:** Task
- **Fields:**
  - title: str
  - description: str
  - due_date: datetime
  - priority: int
  - is_completed: bool
  - user_id: UUID (foreign key to User)
- **Relationships:** many-to-one with User
- **Unique Constraints:** NONE (no fields are unique)
- **Query Parameters:** is_completed (bool), user_id (UUID)
- **Modifiable Fields:** title, description, due_date, priority, is_completed, user_id

## Key Difference: Router Responses

Since TaskEntity has **NO unique constraints**, the router only needs `response_404`:

```python
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from result import Err, Ok
from starlette.status import HTTP_201_CREATED, HTTP_204_NO_CONTENT

from src.api_server.deps import get_task_service
from src.api_server.helpers.error_response import http_exception_from_error
from src.api_server.responses import response_404  # Only need 404, not 409
from src.constants import (
    DEFAULT_PAGE_NUMBER,
    DEFAULT_PAGE_SIZE,
    OMIT_PAGINATION,
    PAGE_NUMBER,
    PAGE_SIZE,
    SORT_BY,
    SORT_DIRECTION,
    TASKS_PREFIX,
)
from src.mappers.task import to_task_entity
from src.models.base import ModelList
from src.models.enums.sort_direction import SortDirection
from src.models.task import Task, TaskCreate, TaskUpdate
from src.services.task_service import TaskService

router = APIRouter(prefix=f"/{TASKS_PREFIX}")


@router.get("/", response_model=ModelList[Task])
def get_tasks(
    page_number: int = Query(default=DEFAULT_PAGE_NUMBER, alias=PAGE_NUMBER, gt=0),
    page_size: int = Query(default=DEFAULT_PAGE_SIZE, alias=PAGE_SIZE, gt=0),
    omit_pagination: bool = Query(default=False, alias=OMIT_PAGINATION),
    is_completed: bool | None = Query(default=None, alias="isCompleted"),
    user_id: UUID | None = Query(default=None, alias="userId"),
    sort_by: str | None = Query(default=None, alias=SORT_BY),
    sort_direction: SortDirection = Query(default=SortDirection.ascending, alias=SORT_DIRECTION),
    task_service: TaskService = Depends(get_task_service),
) -> ModelList[Task]:
    match task_service.get_page(page_number, page_size, omit_pagination, is_completed, user_id, sort_by, sort_direction):
        case Ok(result):
            return result
        case Err(error):
            raise http_exception_from_error(error)
        case _:
            raise http_exception_from_error()


@router.get("/{task_id}", response_model=Task, responses=response_404)
def get_task_by_id(task_id: UUID, task_service: TaskService = Depends(get_task_service)) -> Task:
    match task_service.get_by_id(task_id):
        case Ok(result):
            return result
        case Err(error):
            raise http_exception_from_error(error)
        case _:
            raise http_exception_from_error()


@router.post("/", response_model=Task, status_code=HTTP_201_CREATED)  # NO responses parameter
def create_task(
    task: TaskCreate,
    task_service: TaskService = Depends(get_task_service),
    current_user_id: str = "system",
) -> Task:
    match task_service.create(task, to_task_entity, current_user_id):  # ty: ignore[invalid-argument-type]
        case Ok(result):
            return result
        case Err(error):
            raise http_exception_from_error(error)
        case _:
            raise http_exception_from_error()


@router.patch("/{task_id}", response_model=Task, responses=response_404)  # Only 404
def update_task(
    task_id: UUID,
    task: TaskUpdate,
    task_service: TaskService = Depends(get_task_service),
    current_user_id: str = "system",
) -> Task:
    match task_service.update(task_id, task, current_user_id):
        case Ok(result):
            return result
        case Err(error):
            raise http_exception_from_error(error)
        case _:
            raise http_exception_from_error()


@router.delete("/{task_id}", status_code=HTTP_204_NO_CONTENT, responses=response_404)
def delete_task(task_id: UUID, task_service: TaskService = Depends(get_task_service)) -> None:
    match task_service.delete(task_id):
        case Err(error):
            raise http_exception_from_error(error)
```

## Key Differences from Order/Product

Since Task has **no unique constraints**:

1. **Import:** Only `response_404` needed (no `response_409`)
2. **POST endpoint:** No `responses` parameter (cannot return 409 conflict)
3. **PATCH endpoint:** Only `responses=response_404` (cannot return 409 conflict)
4. **Unique validation messages:** Service class can use default messages since no unique constraints exist

## Comparison Table

| Endpoint | Task (No Unique) | Product/Order (Has Unique) |
|----------|------------------|----------------------------|
| GET list | No responses | No responses |
| GET by ID | `response_404` | `response_404` |
| POST | No responses | `response_409` |
| PATCH | `response_404` | `response_404 \| response_409` |
| DELETE | `response_404` | `response_404` |

**Rule of thumb:** Check entity for `unique=True` fields. If none exist, only import and use `response_404`.
