# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Testing
- **Run all tests**: `python -m unittest discover` (requires PYTHONPATH to be set to src/)
- **Quick test script**: `bash scripts/run_tests.sh` (sets PYTHONPATH automatically)
- **Development environment**: `bash scripts/term.sh` (enters virtual environment with dependencies)

### Database Setup
- **Start SurrealDB**: `docker-compose up -d` or `docker compose up -d`
- **Stop SurrealDB**: `docker-compose down` or `docker compose down`

### Code Quality
- **Linting**: `ruff check` (configured in pyproject.toml, excludes src/surrealdb/__init__.py)
- **Type checking**: `mypy` (configured in pyproject.toml with custom overrides)
- **Formatting**: `black` (available in dev dependencies)

### Environment Management
- **Virtual environment**: Created automatically by `scripts/term.sh`
- **Dependencies**: Install with `pip install -r requirements.txt`
- **PYTHONPATH**: Must be set to `src/` directory for tests and development

## Architecture Overview

### Core Structure
- **Main SDK entry points**: `Surreal()` and `AsyncSurreal()` factory functions in `src/surrealdb/__init__.py`
- **Connection layer**: Four main connection types based on protocol and async/sync:
  - `AsyncHttpSurrealConnection` - HTTP/HTTPS async
  - `AsyncWsSurrealConnection` - WebSocket async
  - `BlockingHttpSurrealConnection` - HTTP/HTTPS blocking
  - `BlockingWsSurrealConnection` - WebSocket blocking
- **Data types**: Custom SurrealDB types in `src/surrealdb/data/types/` (RecordID, Duration, Geometry, etc.)
- **Request handling**: Message construction and SQL adaptation in `src/surrealdb/request_message/`

### Key Patterns
- **URL-based connection routing**: Factory functions automatically select connection type based on URL scheme (ws/wss vs http/https)
- **Protocol abstraction**: All connection types implement similar method interfaces for CRUD operations
- **CBOR serialization**: Custom CBOR implementation in `src/surrealdb/cbor2/`
- **Type validation**: Uses Cerberus for data validation

### Testing Structure
- **Unit tests**: Organized by connection type and method in `tests/unit_tests/connections/`
- **Method coverage**: Each CRUD operation tested across all four connection types
- **Data type tests**: Separate tests for custom SurrealDB data types in `tests/unit_tests/data_types/`

### Sample Applications
- **FastAPI examples**: Complete auth examples in `samples/fastapi-auth-example/` and `samples/chat-gpt/`
- **Documentation**: Comprehensive guides in `docs/` with Docusaurus setup

## Important Notes
- The main `__init__.py` is excluded from ruff linting due to complex metaclass usage
- Tests expect SurrealDB running on localhost:8000 via Docker Compose
- Both sync and async patterns are fully supported throughout the codebase
- Custom data types handle SurrealDB-specific features like RecordIDs and geometric data