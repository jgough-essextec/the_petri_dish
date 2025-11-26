from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, ConfigDict, field_validator
from typing import List, Optional
import sqlite3
import os
from datetime import datetime
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Todo App API", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database setup
DATABASE = os.getenv('DATABASE_PATH', '/app/data/todos.db')

def init_db():
    # Ensure the directory exists
    os.makedirs(os.path.dirname(DATABASE), exist_ok=True)
    
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    
    # Create todos table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS todos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            completed BOOLEAN DEFAULT FALSE,
            completed_at TIMESTAMP,
            parent_id INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (parent_id) REFERENCES todos (id) ON DELETE CASCADE
        )
    ''')
    
    conn.commit()
    conn.close()

# Pydantic models
class TodoBase(BaseModel):
    title: str
    parent_id: Optional[int] = None

    @field_validator('title')
    @classmethod
    def title_must_not_be_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('Title cannot be empty')
        return v

class TodoCreate(TodoBase):
    pass

class TodoUpdate(BaseModel):
    title: Optional[str] = None
    completed: Optional[bool] = None

    @field_validator('title')
    @classmethod
    def title_must_not_be_empty(cls, v):
        if v is not None and (not v or not v.strip()):
            raise ValueError('Title cannot be empty')
        return v

class Todo(TodoBase):
    id: int
    completed: bool
    completed_at: Optional[datetime]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

# Thread-safe database connection function
def get_db_connection():
    """Create a fresh database connection for each operation"""
    conn = sqlite3.connect(DATABASE, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

# Initialize database on startup
init_db()

# API Routes
@app.get("/")
async def root():
    return {"message": "Todo App API"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}


@app.post("/todos/", response_model=Todo)
async def create_todo(todo: TodoCreate):
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO todos (title, parent_id) VALUES (?, ?)",
            (todo.title, todo.parent_id)
        )
        conn.commit()
        todo_id = cursor.lastrowid

        # Fetch and return the created todo
        cursor.execute("SELECT * FROM todos WHERE id = ?", (todo_id,))
        row = cursor.fetchone()
        return dict(row)
    finally:
        conn.close()

@app.get("/todos/", response_model=List[Todo])
async def read_todos(skip: int = 0, limit: int = 10):
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM todos ORDER BY created_at DESC LIMIT ? OFFSET ?", (limit, skip))
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()

@app.put("/todos/{todo_id}", response_model=Todo)
async def update_todo(todo_id: int, todo_update: TodoUpdate):
    conn = get_db_connection()
    try:
        cursor = conn.cursor()

        # Get current todo
        cursor.execute("SELECT * FROM todos WHERE id = ?", (todo_id,))
        current_todo = cursor.fetchone()
        if not current_todo:
            raise HTTPException(status_code=404, detail="Todo not found")

        # Update fields if provided
        update_fields = []
        values = []

        if todo_update.title is not None:
            update_fields.append("title = ?")
            values.append(todo_update.title)

        if todo_update.completed is not None:
            update_fields.append("completed = ?")
            values.append(todo_update.completed)
            if todo_update.completed:
                # Store timestamps as ISO formatted strings instead of raw
                # datetime objects. The sqlite3 default datetime adapter is
                # deprecated on newer Pythons; using an ISO string avoids the
                # deprecation and keeps the API consistent for clients/tests.
                update_fields.append("completed_at = ?")
                values.append(datetime.now().isoformat())
            else:
                update_fields.append("completed_at = NULL")

        if update_fields:
            values.append(todo_id)
            query = f"UPDATE todos SET {', '.join(update_fields)} WHERE id = ?"
            cursor.execute(query, values)
            conn.commit()

        # Fetch and return updated todo
        cursor.execute("SELECT * FROM todos WHERE id = ?", (todo_id,))
        row = cursor.fetchone()
        return dict(row)
    finally:
        conn.close()

@app.delete("/todos/{todo_id}")
async def delete_todo(todo_id: int):
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM todos WHERE id = ?", (todo_id,))
        conn.commit()
        return {"message": "Todo deleted"}
    finally:
        conn.close()

@app.get("/todos/completed/", response_model=List[Todo])
async def read_completed_todos(skip: int = 0, limit: int = 10):
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM todos
            WHERE completed = TRUE
            ORDER BY completed_at DESC
            LIMIT ? OFFSET ?
        """, (limit, skip))
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()

@app.get("/todos/search/", response_model=List[Todo])
async def search_completed_todos(query: str, skip: int = 0, limit: int = 10):
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM todos
            WHERE completed = TRUE
            AND (title LIKE ? OR CAST(completed_at AS TEXT) LIKE ?)
            ORDER BY completed_at DESC
            LIMIT ? OFFSET ?
        """, (f"%{query}%", f"%{query}%", limit, skip))
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()

@app.get("/todos/hierarchy/", response_model=List[Todo])
async def read_todos_with_hierarchy():
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM todos ORDER BY created_at DESC")
        rows = cursor.fetchall()

        # Convert to dictionary and add children
        todos = [dict(row) for row in rows]

        # Build hierarchy
        todo_dict = {todo['id']: todo for todo in todos}
        root_todos = []

        for todo in todos:
            if todo['parent_id'] is None:
                root_todos.append(todo)
            else:
                if todo['parent_id'] in todo_dict:
                    if 'children' not in todo_dict[todo['parent_id']]:
                        todo_dict[todo['parent_id']]['children'] = []
                    todo_dict[todo['parent_id']]['children'].append(todo)

        return root_todos
    finally:
        conn.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
