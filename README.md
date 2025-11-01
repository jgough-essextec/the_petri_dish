# Petri Dish - Todo App

A project where I can grow and observe my tests: A Petri Dish

This is a full-stack todo application with:
- **Frontend**: React with Bootstrap styling
- **Backend**: FastAPI with SQLite database
- **Features**:
  - Add and manage to-do items
  - Complete items
  - Hierarchical to-do items (subtasks with indentation)
  - Pagination (10 items per page)
  - History view for completed items with date/time completed
  - Search functionality for completed tasks

## Architecture

```
petri_dish/
├── backend/          # FastAPI backend
│   ├── main.py       # API endpoints and business logic
│   ├── requirements.txt  # Python dependencies
│   └── Dockerfile    # Backend Docker configuration
├── frontend/         # React frontend
│   ├── public/       # Static files
│   ├── src/          # Source code
│   │   ├── App.js    # Main application component
│   │   └── index.js  # Entry point
│   └── package.json  # Frontend dependencies
└── docker-compose.yml # Docker orchestration
```

## Getting Started

### Prerequisites
- Docker and Docker Compose installed

### Running the Application

1. Clone the repository
2. Navigate to the project directory
3. Run: `docker-compose up`

The application will be available at:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000

## API Endpoints

### Todos
- `GET /todos/` - Get all todos (paginated)
- `POST /todos/` - Create a new todo
- `PUT /todos/{id}` - Update a todo
- `DELETE /todos/{id}` - Delete a todo

### Completed Todos
- `GET /todos/completed/` - Get completed todos (paginated)
- `GET /todos/search/?query={query}` - Search completed todos

### Hierarchy
- `GET /todos/hierarchy/` - Get todos with hierarchical structure

## Features Implemented

### Frontend
- Clean, responsive UI with Bootstrap
- Add new todos with parent-child relationship
- Mark todos as complete/incomplete
- Delete todos
- Hierarchical display with expand/collapse
- Pagination for todo lists
- History view showing completed items with timestamps
- Search functionality for completed items

### Backend
- SQLite database for persistent storage
- RESTful API with FastAPI
- Support for hierarchical todos (parent-child relationships)
- Pagination for all lists
- Search functionality for completed todos
- Proper error handling and validation

## Testing

This project is designed as a testbed for experimenting with frontend and backend testing in GitHub.
