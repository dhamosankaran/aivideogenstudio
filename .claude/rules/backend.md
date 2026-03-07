---
paths:
  - "backend/**/*.py"
---

# Backend Python Rules

## Naming Conventions
- Files: `snake_case.py`
- Classes: `PascalCase`
- Functions/variables: `snake_case`
- Constants: `UPPER_SNAKE_CASE`

## Type Hints
All function signatures require type hints. Use `str | None` (Python 3.10+) not `Optional[str]`.

## Error Handling
```python
# Correct
try:
    result = await external_api.call()
except httpx.TimeoutException as e:
    logger.error(f"[ServiceName] API timeout: {e}")
    raise ServiceTimeoutError("External API timed out") from e
except httpx.HTTPStatusError as e:
    logger.error(f"[ServiceName] API error {e.response.status_code}: {e}")
    raise

# Never
try:
    result = api.call()
except:
    pass
```

## Logging Pattern
```python
logger = logging.getLogger(__name__)
logger.info(f"[ServiceName] Action completed: {detail}")
logger.error(f"[ServiceName] Failed: {e}", exc_info=True)
```

## FastAPI Patterns
- Routers: `backend/app/routers/` — HTTP logic, request validation, response shaping only
- Services: `backend/app/services/` — business logic, no HTTP imports
- Schemas: `backend/app/schemas/` — Pydantic request/response models
- Router imports services; services never import from routers

## Import Order (isort)
```python
# 1. Standard library
import os
from pathlib import Path

# 2. Third-party
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

# 3. Local
from app.config import settings
from app.services.my_service import MyService
```

## Async Rules
- Use `async def` for all I/O-bound operations (DB, HTTP, file I/O)
- Don't block the event loop with sync calls inside async functions
- Background tasks: use FastAPI `BackgroundTasks`, not `asyncio.create_task`

## Security
- Never hardcode API keys — use `os.getenv()` or `settings`
- Validate all user input at router level before passing to services
- SQLAlchemy ORM handles parameterization — never use f-strings in raw SQL
