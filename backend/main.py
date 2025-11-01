from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional
import sqlite3
import os
from datetime import datetime

app = FastAPI(title="Todo App API", version="1.0.0")

# Database setup
DATABASE = "todos.db"

def init_db():
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

class TodoCreate(TodoBase):
    pass

class TodoUpdate(BaseModel):
    title: Optional[str] = None
    completed: Optional[bool] = None

class Todo(TodoBase):
    id: int
    completed: bool
    completed_at: Optional[datetime]
    created_at: datetime
    
    class Config:
        from_attributes = True

# Dependency
def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    yield conn
    conn.close()

# Initialize database on startup
init_db()

# API Routes
@app.get("/")
async def root():
    return {"message": "Todo App API"}

@app.post("/todos/", response_model=Todo)
async def create_todo(todo: TodoCreate, db=Depends(get_db)):
    cursor = db.cursor()
    cursor.execute(
        "INSERT INTO todos (title, parent_id) VALUES (?, ?)",
        (todo.title, todo.parent_id)
    )
    db.commit()
    todo_id = cursor.lastrowid
    
    # Fetch and return the created todo
    cursor.execute("SELECT * FROM todos WHERE id = ?", (todo_id,))
    row = cursor.fetchone()
    return dict(row)

@app.get("/todos/", response_model=List[Todo])
async def read_todos(skip: int = 0, limit: int = 10, db=Depends(get_db)):
    cursor = db.cursor()
    cursor.execute("SELECT * FROM todos ORDER BY created_at DESC LIMIT ? OFFSET ?", (limit, skip))
    rows = cursor.fetchall()
    return [dict(row) for row in rows]

@app.put("/todos/{todo_id}", response_model=Todo)
async def update_todo(todo_id: int, todo_update: TodoUpdate, db=Depends(get_db)):
    cursor = db.cursor()
    
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
            update_fields.append("completed_at = ?")
            values.append(datetime.now())
        else:
            update_fields.append("completed_at = NULL")
    
    if update_fields:
        values.append(todo_id)
        query = f"UPDATE todos SET {', '.join(update_fields)} WHERE id = ?"
        cursor.execute(query, values)
        db.commit()
    
    # Fetch and return updated todo
    cursor.execute("SELECT * FROM todos WHERE id = ?", (todo_id,))
    row = cursor.fetchone()
    return dict(row)

@app.delete("/todos/{todo_id}")
async def delete_todo(todo_id: int, db=Depends(get_db)):
    cursor = db.cursor()
    cursor.execute("DELETE FROM todos WHERE id = ?", (todo_id,))
    db.commit()
    return {"message": "Todo deleted"}

@app.get("/todos/completed/", response_model=List[Todo])
async def read_completed_todos(skip: int = 0, limit: int = 10, db=Depends(get_db)):
    cursor = db.cursor()
    cursor.execute("""
        SELECT * FROM todos 
        WHERE completed = TRUE 
        ORDER BY completed_at DESC 
        LIMIT ? OFFSET ?
    """, (limit, skip))
    rows = cursor.fetchall()
    return [dict(row) for row in rows]

@app.get("/todos/search/", response_model=List[Todo])
async def search_completed_todos(query: str, skip: int = 0, limit: int = 10, db=Depends(get_db)):
    cursor = db.cursor()
    cursor.execute("""
        SELECT * FROM todos 
        WHERE completed = TRUE 
        AND (title LIKE ? OR CAST(completed_at AS TEXT) LIKE ?)
        ORDER BY completed_at DESC 
        LIMIT ? OFFSET ?
    """, (f"%{query}%", f"%{query}%", limit, skip))
    rows = cursor.fetchall()
    return [dict(row) for row in rows]

@app.get("/todos/hierarchy/", response_model=List[Todo])
async def read_todos_with_hierarchy(db=Depends(get_db)):
    cursor = db.cursor()
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
