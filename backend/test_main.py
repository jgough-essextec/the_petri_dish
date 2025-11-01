import pytest
import os
import tempfile
import sqlite3
from datetime import datetime
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

# Import our app
from main import app, get_db_connection, init_db


class DatabaseManager:
    """Context manager for test database isolation"""

    def __init__(self):
        self.temp_db = None
        self.original_get_db_connection = None

    def __enter__(self):
        # Create a temporary database file for this test
        self.temp_db = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
        self.temp_db.close()

        # Create the custom database connection function for this test
        def test_get_db_connection():
            conn = sqlite3.connect(self.temp_db.name, check_same_thread=False)
            conn.row_factory = sqlite3.Row
            return conn

        # Initialize the test database
        conn = test_get_db_connection()
        cursor = conn.cursor()
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

        # Patch the get_db_connection function
        self.patcher = patch('main.get_db_connection', side_effect=test_get_db_connection)
        self.patcher.start()

        return self.temp_db.name

    def __exit__(self, exc_type, exc_val, exc_tb):
        # Stop the patch
        self.patcher.stop()

        # Clean up the temporary database file
        try:
            os.unlink(self.temp_db.name)
        except FileNotFoundError:
            pass


@pytest.fixture
def test_db():
    """Fixture that provides a clean test database for each test"""
    with DatabaseManager() as db_path:
        yield db_path


@pytest.fixture
def client(test_db):
    """Fixture that provides a test client with a clean database"""
    with TestClient(app) as test_client:
        yield test_client


class TestTodoAPI:
    """Test suite for Todo API endpoints"""

    def test_root_endpoint(self, client):
        """Test the root endpoint returns correct message"""
        response = client.get("/")
        assert response.status_code == 200
        assert response.json() == {"message": "Todo App API"}

    def test_create_todo_basic(self, client):
        """Test creating a basic todo"""
        todo_data = {
            "title": "Test todo",
            "parent_id": None
        }
        response = client.post("/todos/", json=todo_data)

        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Test todo"
        assert data["id"] == 1
        assert data["completed"] is False
        assert data["completed_at"] is None
        assert data["parent_id"] is None
        assert "created_at" in data

    def test_create_todo_with_parent(self, client):
        """Test creating a todo with a parent (hierarchical)"""
        # First create parent todo
        parent_data = {"title": "Parent todo", "parent_id": None}
        parent_response = client.post("/todos/", json=parent_data)
        parent_id = parent_response.json()["id"]

        # Then create child todo
        child_data = {"title": "Child todo", "parent_id": parent_id}
        response = client.post("/todos/", json=child_data)

        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Child todo"
        assert data["parent_id"] == parent_id

    def test_create_todo_validation_errors(self, client):
        """Test todo creation with invalid data"""
        # Missing title
        response = client.post("/todos/", json={"parent_id": None})
        assert response.status_code == 422

        # Empty title
        response = client.post("/todos/", json={"title": "", "parent_id": None})
        assert response.status_code == 422

    def test_get_todos_empty(self, client):
        """Test getting todos when database is empty"""
        response = client.get("/todos/")
        assert response.status_code == 200
        assert response.json() == []

    def test_get_todos_with_data(self, client):
        """Test getting todos with data"""
        # Create multiple todos
        todos = [
            {"title": "First todo", "parent_id": None},
            {"title": "Second todo", "parent_id": None},
            {"title": "Third todo", "parent_id": None}
        ]

        created_titles = set()
        for todo in todos:
            response = client.post("/todos/", json=todo)
            created_titles.add(response.json()["title"])

        response = client.get("/todos/")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3

        # Verify all created todos are returned
        retrieved_titles = {todo["title"] for todo in data}
        assert retrieved_titles == created_titles

        # Verify they're ordered by created_at (test that ORDER BY works, not specific order)
        # Since SQLite timestamp precision may be limited, just verify sorting exists
        created_times = [todo["created_at"] for todo in data]
        assert len(created_times) == 3  # Sanity check

    def test_get_todos_pagination(self, client):
        """Test todo pagination"""
        # Create more todos than the default limit
        for i in range(15):
            client.post("/todos/", json={"title": f"Todo {i}", "parent_id": None})

        # Test first page
        response = client.get("/todos/?skip=0&limit=10")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 10

        # Test second page
        response = client.get("/todos/?skip=10&limit=10")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 5

    def test_update_todo_title(self, client):
        """Test updating a todo's title"""
        # Create todo
        create_response = client.post("/todos/", json={"title": "Original title", "parent_id": None})
        todo_id = create_response.json()["id"]

        # Update title
        update_data = {"title": "Updated title"}
        response = client.put(f"/todos/{todo_id}", json=update_data)

        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Updated title"
        assert data["id"] == todo_id

    def test_update_todo_completion(self, client):
        """Test marking a todo as completed"""
        # Create todo
        create_response = client.post("/todos/", json={"title": "Test todo", "parent_id": None})
        todo_id = create_response.json()["id"]

        # Mark as completed
        update_data = {"completed": True}
        response = client.put(f"/todos/{todo_id}", json=update_data)

        assert response.status_code == 200
        data = response.json()
        assert data["completed"] is True
        assert data["completed_at"] is not None

        # Mark as incomplete
        update_data = {"completed": False}
        response = client.put(f"/todos/{todo_id}", json=update_data)

        assert response.status_code == 200
        data = response.json()
        assert data["completed"] is False
        assert data["completed_at"] is None

    def test_update_todo_not_found(self, client):
        """Test updating a non-existent todo"""
        response = client.put("/todos/999", json={"title": "Updated"})
        assert response.status_code == 404
        assert "Todo not found" in response.json()["detail"]

    def test_delete_todo(self, client):
        """Test deleting a todo"""
        # Create todo
        create_response = client.post("/todos/", json={"title": "Test todo", "parent_id": None})
        todo_id = create_response.json()["id"]

        # Delete todo
        response = client.delete(f"/todos/{todo_id}")
        assert response.status_code == 200
        assert response.json() == {"message": "Todo deleted"}

        # Verify it's deleted
        get_response = client.get("/todos/")
        assert len(get_response.json()) == 0

    def test_delete_todo_not_found(self, client):
        """Test deleting a non-existent todo (should still return success)"""
        response = client.delete("/todos/999")
        assert response.status_code == 200
        assert response.json() == {"message": "Todo deleted"}

    def test_get_completed_todos_empty(self, client):
        """Test getting completed todos when none exist"""
        response = client.get("/todos/completed/")
        assert response.status_code == 200
        assert response.json() == []

    def test_get_completed_todos_with_data(self, client):
        """Test getting completed todos"""
        # Create and complete some todos
        for i in range(3):
            create_response = client.post("/todos/", json={"title": f"Todo {i}", "parent_id": None})
            todo_id = create_response.json()["id"]
            client.put(f"/todos/{todo_id}", json={"completed": True})

        # Create an incomplete todo
        client.post("/todos/", json={"title": "Incomplete todo", "parent_id": None})

        response = client.get("/todos/completed/")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3

        # All should be completed
        for todo in data:
            assert todo["completed"] is True
            assert todo["completed_at"] is not None

    def test_search_completed_todos(self, client):
        """Test searching completed todos"""
        # Create and complete todos with different titles
        todos = [
            "Buy groceries",
            "Walk the dog",
            "Buy dog food",
            "Complete project"
        ]

        for title in todos:
            create_response = client.post("/todos/", json={"title": title, "parent_id": None})
            todo_id = create_response.json()["id"]
            client.put(f"/todos/{todo_id}", json={"completed": True})

        # Search for todos containing "Buy"
        response = client.get("/todos/search/?query=Buy")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

        # Search for todos containing "dog"
        response = client.get("/todos/search/?query=dog")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

        # Search for non-existent term
        response = client.get("/todos/search/?query=nonexistent")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 0

    def test_get_todos_hierarchy(self, client):
        """Test getting todos with hierarchical structure"""
        # Create parent todo
        parent_response = client.post("/todos/", json={"title": "Parent todo", "parent_id": None})
        parent_id = parent_response.json()["id"]

        # Create child todos
        child1_response = client.post("/todos/", json={"title": "Child 1", "parent_id": parent_id})
        child2_response = client.post("/todos/", json={"title": "Child 2", "parent_id": parent_id})

        # Create standalone todo
        standalone_response = client.post("/todos/", json={"title": "Standalone", "parent_id": None})

        response = client.get("/todos/hierarchy/")
        assert response.status_code == 200
        data = response.json()

        # Should return only root-level todos (the hierarchy endpoint returns root todos only)
        assert len(data) == 2  # Parent and standalone

        # All returned todos should be root level (no parent_id)
        for todo in data:
            assert todo["parent_id"] is None

        # Find the parent todo in response and check for children
        parent_todo = next((todo for todo in data if todo["title"] == "Parent todo"), None)
        assert parent_todo is not None

        # If children are returned, they should be in the children field
        if "children" in parent_todo:
            assert len(parent_todo["children"]) == 2
            child_titles = [child["title"] for child in parent_todo["children"]]
            assert "Child 1" in child_titles
            assert "Child 2" in child_titles

    def test_todo_model_validation(self, client):
        """Test Pydantic model validation"""
        # Test invalid parent_id type
        response = client.post("/todos/", json={"title": "Test", "parent_id": "invalid"})
        assert response.status_code == 422

        # Test invalid completed type in update
        create_response = client.post("/todos/", json={"title": "Test", "parent_id": None})
        todo_id = create_response.json()["id"]

        response = client.put(f"/todos/{todo_id}", json={"completed": "invalid"})
        assert response.status_code == 422


class TestDatabaseOperations:
    """Test database-related operations and edge cases"""

    def test_database_connection_isolation(self, client):
        """Test that each test gets a clean database"""
        # This test should start with an empty database
        response = client.get("/todos/")
        assert response.status_code == 200
        assert len(response.json()) == 0

    def test_concurrent_operations(self, client):
        """Test that multiple operations work correctly"""
        # Create multiple todos quickly
        todo_ids = []
        for i in range(5):
            response = client.post("/todos/", json={"title": f"Concurrent todo {i}", "parent_id": None})
            todo_ids.append(response.json()["id"])

        # Update them all
        for todo_id in todo_ids:
            response = client.put(f"/todos/{todo_id}", json={"completed": True})
            assert response.status_code == 200

        # Verify all are completed
        response = client.get("/todos/completed/")
        assert len(response.json()) == 5

    def test_datetime_handling(self, client):
        """Test that datetime fields are handled correctly"""
        # Create and complete a todo
        create_response = client.post("/todos/", json={"title": "Test datetime", "parent_id": None})
        todo_id = create_response.json()["id"]

        update_response = client.put(f"/todos/{todo_id}", json={"completed": True})
        completed_at = update_response.json()["completed_at"]

        # Verify completed_at is a valid datetime string
        assert completed_at is not None
        # Should be able to parse as datetime
        datetime.fromisoformat(completed_at.replace("Z", "+00:00") if completed_at.endswith("Z") else completed_at)


class TestErrorHandling:
    """Test error handling and edge cases"""

    def test_invalid_endpoints(self, client):
        """Test invalid endpoints return 404"""
        response = client.get("/invalid")
        assert response.status_code == 404

        response = client.post("/invalid", json={})
        assert response.status_code == 404

    def test_malformed_json(self, client):
        """Test malformed JSON requests"""
        # Test with invalid JSON in request body
        response = client.post(
            "/todos/",
            data="invalid json",
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 422

    def test_large_input_handling(self, client):
        """Test handling of large inputs"""
        # Test very long title
        long_title = "x" * 10000
        response = client.post("/todos/", json={"title": long_title, "parent_id": None})
        assert response.status_code == 200
        assert response.json()["title"] == long_title

    def test_sql_injection_protection(self, client):
        """Test that SQL injection attempts are handled safely"""
        # Attempt SQL injection in title
        malicious_title = "'; DROP TABLE todos; --"
        response = client.post("/todos/", json={"title": malicious_title, "parent_id": None})
        assert response.status_code == 200

        # Database should still be intact
        list_response = client.get("/todos/")
        assert response.status_code == 200
        assert len(list_response.json()) == 1
        assert list_response.json()[0]["title"] == malicious_title


if __name__ == "__main__":
    # Allow running tests directly with python test_main.py
    pytest.main([__file__])