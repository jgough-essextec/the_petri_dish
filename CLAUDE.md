# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Petri Dish is a full-stack todo application designed as a testbed for frontend and backend testing experimentation. It features hierarchical todos (parent-child relationships), pagination, and a completed items history with search.

# Project Constitution
## 1. Tech Stack & Standards
## Architecture

```
backend/
  main.py        - FastAPI app with all endpoints and SQLite database logic
  test_main.py   - pytest test suite using TestClient with isolated temp databases

frontend/
  src/App.js     - Main React component handling all UI and state
  src/App.test.js - Jest/React Testing Library tests
```

### Backend

- **Framework**: FastAPI with Pydantic models for validation
- **Database**: SQLite (`todos.db`) with direct sqlite3 connections (no ORM)
- **Testing**: pytest with `TestClient`, each test gets an isolated temporary database via `DatabaseManager` context manager

### Frontend

- **Framework**: React 18 with Bootstrap 5 for styling
- **HTTP Client**: Axios for API calls
- **Testing**: Jest with React Testing Library

## 2. Agent Protocol
- **No Direct Commits:** Agents must rely on the Orchestrator or User to commit changes unless explicitly authorized.
- **TDD First:** No implementation code is written without a failing test in `tests/`.
- **Atomic Changes:** One task = One PR. Do not combine refactoring with feature work.

## 3. Commands
- Build: `npm run build`
- Test: `npm test`
- Lint: `npm run lint`
- DB Migrate: `npx prisma migrate dev`

### Backend (Python/FastAPI)

```bash
# Run tests (from backend/)
cd backend && pytest

# Run a single test
cd backend && pytest test_main.py::TestTodoAPI::test_create_todo_basic -v

# Run tests with coverage
cd backend && pytest --cov=. --cov-report=term-missing

# Lint
cd backend && flake8 . --max-line-length=127

# Run server locally
cd backend && uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend (React)

```bash
# Install dependencies
cd frontend && npm ci

# Run tests
cd frontend && npm test -- --watchAll=false

# Run a single test file
cd frontend && npm test -- App.test.js --watchAll=false

# Build
cd frontend && npm run build

# Start dev server
cd frontend && npm start
```

### Docker

```bash
# Run full stack
docker-compose up

# Rebuild containers
docker-compose up --build
```

### API Endpoints

- `GET/POST /todos/` - List (paginated) / Create todos
- `PUT/DELETE /todos/{id}` - Update / Delete todo
- `GET /todos/completed/` - Completed todos (paginated)
- `GET /todos/search/?query=` - Search completed todos
- `GET /todos/hierarchy/` - Todos with parent-child structure
