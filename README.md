# Boilerplate FastAPI Application

A production-ready FastAPI boilerplate with PostgreSQL, SQLAlchemy ORM, Alembic migrations, and a clean layered architecture. This project demonstrates best practices for building scalable REST APIs with proper separation of concerns, dependency injection, and comprehensive error handling.

## Features

- **FastAPI Framework**: Modern, fast (high-performance) web framework for building APIs
- **PostgreSQL Database**: Robust relational database with schema support
- **SQLAlchemy ORM**: Synchronous database operations with declarative models
- **Alembic Migrations**: Database schema version control
- **Layered Architecture**: Clean separation between routers, services, and data access layers
- **Result Pattern**: Type-safe error handling using the `result` library
- **Docker Support**: Fully containerized development environment with Docker Compose
- **CRUD Operations**: Generic CRUD implementation with filtering, pagination, and sorting
- **Testing Suite**: pytest-based testing with fixtures and mocks
- **Code Quality Tools**: Ruff, mypy, ty, and pre-commit hooks
- **OpenAPI Documentation**: Auto-generated interactive API docs

## Prerequisites

- **Python**: ^3.12
- **uv**: Fast Python package installer and resolver
- **Docker & Docker Compose**: For containerized development
- **PostgreSQL**: 15 (provided via Docker)

## Installation & Local Development Setup

### Using Docker (Recommended)

1. **Clone the repository**

```bash
git clone <repository-url>
cd boilerplate-fast-api
```

2. **Build and start services**

```bash
make build
make start
```

This will start:
- PostgreSQL database on port 5432
- FastAPI application on port 5000

3. **Run database migrations**

```bash
make db_upgrade
```

4. **Access the API**

- API: http://localhost:5000
- Interactive docs: http://localhost:5000/ (Swagger UI)
- OpenAPI schema: http://localhost:5000/v1/swagger.json

## Project Structure

```
boilerplate-fast-api/
├── alembic.ini                      # Alembic configuration
├── docker-compose.yml               # Docker services definition
├── Dockerfile                       # Application container
├── Makefile                         # Common development commands
├── pyproject.toml                   # Project dependencies and tool configs
├── uv.lock                          # uv lockfile with pinned dependencies
├── migrations/                      # Database migrations
│   ├── env.py                       # Alembic environment config
│   └── versions/                    # Migration scripts
│       └── 2025_11_17_1151-*.py     # Sample user entity migration
└── src/
    ├── api_server/                  # API layer
    │   ├── main.py                  # FastAPI app initialization and config
    │   ├── deps.py                  # Dependency injection providers
    │   ├── responses.py             # Standard response schemas
    │   ├── helpers/
    │   │   ├── error_response.py    # Error response builders
    │   │   └── utils.py             # API utility functions
    │   └── routers/
    │       └── user.py              # User endpoints (CRUD operations)
    ├── config/
    │   └── config.py                # Application configuration from env
    ├── constants/
    │   └── __init__.py              # API constants and defaults
    ├── data_services/               # Data access layer
    │   ├── crud.py                  # Generic CRUD operations
    │   ├── filters.py               # Query filter abstractions
    │   └── user_data_service.py     # User-specific data access
    ├── database/
    │   ├── db_engine.py             # SQLAlchemy engine setup
    │   ├── entities/                # SQLAlchemy models
    │   │   ├── base.py              # Base entity with audit fields
    │   │   └── user.py              # User entity
    │   └── scripts/
    │       └── create_db.sql        # Database initialization script
    ├── mappers/
    │   └── user.py                  # Model-to-entity transformations
    ├── models/                      # Pydantic models (DTOs)
    │   ├── base.py                  # Base model classes
    │   ├── error_result.py          # Error result model
    │   ├── problem_details.py       # RFC 7807 problem details
    │   ├── user.py                  # User DTOs (Create, Update, Read)
    │   └── enums/
    │       ├── error_status.py      # Error status enumeration
    │       └── sort_direction.py    # Sort direction enum
    ├── services/                    # Business logic layer
    │   ├── base_service.py          # Generic service with CRUD operations
    │   └── user_service.py          # User-specific business logic
    ├── tests/                       # Test suite
    │   ├── conftest.py              # Pytest configuration and fixtures
    │   ├── utils.py                 # Test utilities
    │   ├── fixtures/
    │   │   └── user_fixtures.py     # User test fixtures
    │   └── unit/
    │       ├── data_services/       # Data service tests
    │       ├── routers/             # Router/endpoint tests
    │       └── services/            # Service layer tests
    └── utils/
        └── exceptions.py            # Custom exception classes
```

## Key Components

### Database Layer

- **Engine**: Synchronous SQLAlchemy engine with connection pooling (`src/database/db_engine.py`)
- **Entities**: Declarative SQLAlchemy models with schema support and audit fields (`src/database/entities/`)
- **Base Entity**: All entities inherit audit fields (created/modified dates, user IDs, is_active flag)
- **Schema Support**: All tables use configurable schema (default: `sample_schema`)

### Data Services Layer

- **Generic CRUD**: Type-safe generic CRUD operations with filtering, pagination, and sorting (`src/data_services/crud.py`)
- **Filters**: Abstraction for building reusable query filters (`src/data_services/filters.py`)
- **User Data Service**: Specialized data access for user entities (`src/data_services/user_data_service.py`)
- **Exception Handling**: Custom exceptions for unique violations and integrity errors

### Service Layer

- **Base Service**: Generic service with CRUD operations and result pattern error handling (`src/services/base_service.py`)
- **User Service**: Business logic for user operations with validation (`src/services/user_service.py`)
- **Result Pattern**: All service methods return `Result[T, ErrorResult]` for type-safe error handling
- **Error Mapping**: Automatic conversion of CRUD exceptions to appropriate HTTP error results

### API Layer

- **FastAPI Application**: Configured with OpenAPI docs, CORS, and global exception handlers (`src/api_server/main.py`)
- **Routers**: RESTful endpoints with OpenAPI documentation (`src/api_server/routers/user.py`)
- **Dependency Injection**: Database session and service providers (`src/api_server/deps.py`)
- **Problem Details**: RFC 7807-compliant error responses
- **Validation Errors**: Automatic Pydantic validation error formatting

### Models (DTOs)

- **Pydantic Models**: Type-safe request/response models with validation (`src/models/`)
- **Camel Case Serialization**: Automatic conversion between snake_case (Python) and camelCase (JSON)
- **Base Audit Model**: Standardized audit fields across all models
- **User Models**: `UserCreate`, `UserUpdate`, and `User` (read) models

### Configuration

- **Database URL**: Auto-generated from individual connection parameters
- **Environment Detection**: Production vs development mode flag

### Migrations

- **Alembic Integration**: Database schema version control with auto-generation support
- **Schema-aware**: Migrations respect the configured database schema
- **Custom File Template**: Timestamped migration files with descriptive names

## Architecture Patterns

### Layered Architecture

The application follows a strict layered architecture with clear separation of concerns:

1. **API Layer** (`api_server/`): HTTP request/response handling, validation, OpenAPI documentation
2. **Service Layer** (`services/`): Business logic, orchestration, error handling with Result pattern
3. **Data Service Layer** (`data_services/`): Database operations, query building, transaction management
4. **Database Layer** (`database/`): SQLAlchemy entities and engine configuration

Each layer depends only on the layer below it, ensuring loose coupling and testability.

### Dependency Injection

FastAPI's dependency injection system is used throughout:

- `get_db()`: Provides database sessions with automatic transaction management
- `get_user_data_service()`: Creates data service instances with injected sessions
- `get_user_service()`: Creates service instances with injected data services

This pattern enables easy testing with mocked dependencies.

### Result Pattern

The service layer uses the `result` library for type-safe error handling instead of exceptions:

```python
Result[User, ErrorResult]  # Success returns User, failure returns ErrorResult
```

This approach:
- Makes error cases explicit in type signatures
- Enables exhaustive pattern matching
- Avoids exception-based control flow
- Provides better IDE support

### Generic Types & Protocol-based Design

The CRUD and service layers use Python generics and protocols for maximum reusability:

- `Crud[Entity, CreateModel, UpdateModel]`: Generic CRUD for any entity type
- `BaseService[Entity, Model, CreateModel, UpdateModel]`: Generic service layer
- `ModelToEntityMapper`: Protocol defining the mapper contract

## Development Tips

### Working with the Database

**Create a new migration:**

```bash
make db_migrate message="description_of_changes"
```

**Apply migrations:**

```bash
make db_upgrade
```

**Rollback one migration:**

```bash
make db_downgrade
```

**Create empty migration (for data migrations):**

```bash
make db_empty_revision message="description"
```

### Running Tests

```bash
make test
```

Tests use pytest with async support and mocked database sessions.

### Code Quality

**Run pre-commit hooks:**

```bash
make pre_commit
```

This runs:
- Ruff format (code formatting)
- Ruff check (linting and import sorting)
- mypy (type checking)
- ty (strict type checking)

**Configure your IDE** to use these tools on save for the best experience.

### Dependency Upgrade Cadence

The project uses a bounded policy for `pydantic-ai-slim[openai]` (`>=1.85.0,<2`) to avoid unplanned major-version changes from lock refreshes.

- Review and refresh dependency locks on a regular monthly cadence.
- Apply patch/minor `pydantic-ai` upgrades after CI and targeted agent-flow tests pass.
- Handle major version upgrades as explicit maintenance work with migration notes and regression verification.

### Adding New Entities

1. **Create entity** in `src/database/entities/`
2. **Create Pydantic models** in `src/models/`
3. **Create mapper** in `src/mappers/`
4. **Create data service** extending `Crud` in `src/data_services/`
5. **Create service** extending `BaseService` in `src/services/`
6. **Create router** in `src/api_server/routers/`
7. **Add dependency providers** in `src/api_server/deps.py`
8. **Generate migration**: `make db_migrate message="add_entity_name"`
9. **Apply migration**: `make db_upgrade`

### Transaction Management

Database sessions are managed via context managers in `get_db()`:

- Transactions begin automatically when the session is created
- Successful requests commit automatically
- Exceptions trigger automatic rollback
- Sessions are closed after each request

### Error Handling Best Practices

1. **Service layer**: Return `Result[T, ErrorResult]` with appropriate error status
2. **Router layer**: Use pattern matching on Result and convert to HTTP exceptions
3. **CRUD layer**: Raise custom exceptions (caught and converted by service layer)
4. **API layer**: Global exception handlers ensure consistent error responses

### Type Safety

The project uses strict type checking with mypy and ty:

- Enable type checking in your IDE
- All functions should have type annotations
- Use generics for reusable components
- Leverage protocol-based design for flexibility
- ty provides additional runtime type validation and stricter checks

### Pagination & Filtering

All list endpoints support:

- **Pagination**: `pageNumber` and `pageSize` query parameters
- **Omit Pagination**: `omitPagination=true` to return all results
- **Filtering**: Pass filters to `get_page()` in services
- **Sorting**: `sortBy` field name and `sortDirection` (ascending/descending)

Example:
```
GET /v1/users?pageNumber=1&pageSize=20&isActive=true&sortBy=lastName&sortDirection=ascending
```

### Avoiding Common Pitfalls

1. **Don't bypass service layer**: Always call services from routers, not data services directly
2. **Use transactions properly**: Don't commit/rollback manually; let `get_db()` handle it
3. **Handle Result types**: Always pattern match on Result instead of assuming success
4. **Respect layering**: Don't import from higher layers (e.g., don't import routers in services)
5. **Follow naming conventions**: Entity suffix for database models, no suffix for Pydantic models
6. **Use mappers**: Always transform Pydantic models to entities via mapper functions
7. **Test isolation**: Use mocked sessions in unit tests, not real database connections

---

Built with ❤️ using FastAPI, SQLAlchemy, and modern Python best practices.
