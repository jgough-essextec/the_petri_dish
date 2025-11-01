import React, { useState, useEffect } from 'react';
import axios from 'axios';
import 'bootstrap/dist/css/bootstrap.min.css';
import './App.css';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

function App() {
  const [todos, setTodos] = useState([]);
  const [newTodo, setNewTodo] = useState('');
  const [searchQuery, setSearchQuery] = useState('');
  const [currentPage, setCurrentPage] = useState(0);
  const [currentView, setCurrentView] = useState('active'); // 'active', 'history'
  const [paginationInfo, setPaginationInfo] = useState({ total: 0, pages: 0 });
  const [expandedItems, setExpandedItems] = useState(new Set());
  const [selectedParentId, setSelectedParentId] = useState(null);

  // Fetch todos
  const fetchTodos = async (page = 0) => {
    try {
      const response = await axios.get(`${API_BASE_URL}/todos/?skip=${page * 10}&limit=10`);
      setTodos(response.data);
      
      // Fetch total count for pagination
      const countResponse = await axios.get(`${API_BASE_URL}/todos/`);
      const totalCount = countResponse.data.length;
      setPaginationInfo({
        total: totalCount,
        pages: Math.ceil(totalCount / 10)
      });
    } catch (error) {
      console.error('Error fetching todos:', error);
    }
  };

  // Fetch completed todos for history view
  const fetchCompletedTodos = async (page = 0) => {
    try {
      const response = await axios.get(`${API_BASE_URL}/todos/completed/?skip=${page * 10}&limit=10`);
      setTodos(response.data);
      
      // Fetch total count for pagination
      const countResponse = await axios.get(`${API_BASE_URL}/todos/completed/`);
      const totalCount = countResponse.data.length;
      setPaginationInfo({
        total: totalCount,
        pages: Math.ceil(totalCount / 10)
      });
    } catch (error) {
      console.error('Error fetching completed todos:', error);
    }
  };

  // Fetch search results
  const searchCompletedTodos = async (query, page = 0) => {
    try {
      const response = await axios.get(`${API_BASE_URL}/todos/search/?query=${encodeURIComponent(query)}&skip=${page * 10}&limit=10`);
      setTodos(response.data);
      
      // Fetch total count for pagination
      const countResponse = await axios.get(`${API_BASE_URL}/todos/search/?query=${encodeURIComponent(query)}`);
      const totalCount = countResponse.data.length;
      setPaginationInfo({
        total: totalCount,
        pages: Math.ceil(totalCount / 10)
      });
    } catch (error) {
      console.error('Error searching completed todos:', error);
    }
  };

  // Add new todo
  const addTodo = async () => {
    if (newTodo.trim() === '') return;
    
    try {
      const response = await axios.post(`${API_BASE_URL}/todos/`, {
        title: newTodo,
        parent_id: selectedParentId
      });
      
      setNewTodo('');
      setSelectedParentId(null);
      fetchTodos(currentPage);
    } catch (error) {
      console.error('Error adding todo:', error);
    }
  };

  // Toggle todo completion
  const toggleTodo = async (id, completed) => {
    try {
      await axios.put(`${API_BASE_URL}/todos/${id}`, {
        completed: !completed
      });
      fetchTodos(currentPage);
    } catch (error) {
      console.error('Error updating todo:', error);
    }
  };

  // Delete todo
  const deleteTodo = async (id) => {
    try {
      await axios.delete(`${API_BASE_URL}/todos/${id}`);
      fetchTodos(currentPage);
    } catch (error) {
      console.error('Error deleting todo:', error);
    }
  };

  // Handle search
  const handleSearch = async () => {
    if (searchQuery.trim()) {
      searchCompletedTodos(searchQuery, 0);
    } else {
      fetchCompletedTodos(0);
    }
  };

  // Handle page change
  const handlePageChange = (page) => {
    if (currentView === 'active') {
      fetchTodos(page);
    } else if (currentView === 'history') {
      fetchCompletedTodos(page);
    } else if (currentView === 'search') {
      searchCompletedTodos(searchQuery, page);
    }
    setCurrentPage(page);
  };

  // Toggle expand/collapse for hierarchy
  const toggleExpand = (id) => {
    const newExpanded = new Set(expandedItems);
    if (newExpanded.has(id)) {
      newExpanded.delete(id);
    } else {
      newExpanded.add(id);
    }
    setExpandedItems(newExpanded);
  };

  // Format date for display
  const formatDate = (dateString) => {
    if (!dateString) return '';
    const date = new Date(dateString);
    return date.toLocaleString();
  };

  // Initialize
  useEffect(() => {
    fetchTodos(0);
  }, []);

  // View change handler
  useEffect(() => {
    if (currentView === 'active') {
      fetchTodos(0);
    } else if (currentView === 'history') {
      fetchCompletedTodos(0);
    }
  }, [currentView]);

  // Render todo item with hierarchy
  const renderTodoItem = (todo, level = 0) => {
    const isExpanded = expandedItems.has(todo.id);
    const hasChildren = todos.some(t => t.parent_id === todo.id);
    
    return (
      <div key={todo.id} className={`todo-item mb-2 ${level > 0 ? 'ms-4' : ''}`}>
        <div className="d-flex align-items-center">
          <input
            type="checkbox"
            checked={todo.completed}
            onChange={() => toggleTodo(todo.id, todo.completed)}
            className="me-2"
          />
          <span className={todo.completed ? 'text-decoration-line-through text-muted' : ''}>
            {todo.title}
          </span>
          {hasChildren && (
            <button
              onClick={() => toggleExpand(todo.id)}
              className="btn btn-sm btn-outline-secondary ms-2"
              style={{ fontSize: '0.7rem' }}
            >
              {isExpanded ? '−' : '+'}
            </button>
          )}
          <button
            onClick={() => deleteTodo(todo.id)}
            className="btn btn-sm btn-outline-danger ms-auto"
            style={{ fontSize: '0.7rem' }}
          >
            Delete
          </button>
        </div>
        
        {/* Children */}
        {hasChildren && isExpanded && (
          <div className="mt-2">
            {todos
              .filter(t => t.parent_id === todo.id)
              .map(child => renderTodoItem(child, level + 1))}
          </div>
        )}
      </div>
    );
  };

  // Render pagination controls
  const renderPagination = () => {
    if (paginationInfo.pages <= 1) return null;

    const pages = [];
    for (let i = 0; i < paginationInfo.pages; i++) {
      pages.push(
        <button
          key={i}
          onClick={() => handlePageChange(i)}
          className={`btn btn-sm mx-1 ${currentPage === i ? 'btn-primary' : 'btn-outline-primary'}`}
        >
          {i + 1}
        </button>
      );
    }

    return (
      <div className="d-flex justify-content-center mt-3">
        <button
          onClick={() => handlePageChange(Math.max(0, currentPage - 1))}
          disabled={currentPage === 0}
          className="btn btn-outline-primary me-2"
        >
          Previous
        </button>
        {pages}
        <button
          onClick={() => handlePageChange(Math.min(paginationInfo.pages - 1, currentPage + 1))}
          disabled={currentPage === paginationInfo.pages - 1}
          className="btn btn-outline-primary ms-2"
        >
          Next
        </button>
      </div>
    );
  };

  return (
    <div className="container-fluid py-4">
      <div className="row">
        <div className="col-12">
          <h1 className="text-center mb-4">Petri Dish - Todo App</h1>
          
          {/* Navigation */}
          <div className="d-flex justify-content-center mb-4">
            <div className="btn-group" role="group">
              <button
                className={`btn ${currentView === 'active' ? 'btn-primary' : 'btn-outline-primary'}`}
                onClick={() => setCurrentView('active')}
              >
                Active Todos
              </button>
              <button
                className={`btn ${currentView === 'history' ? 'btn-primary' : 'btn-outline-primary'}`}
                onClick={() => setCurrentView('history')}
              >
                History
              </button>
            </div>
          </div>

          {/* Add Todo Form */}
          {currentView === 'active' && (
            <div className="card mb-4">
              <div className="card-body">
                <h5 className="card-title">Add New Todo</h5>
                <div className="input-group mb-3">
                  <input
                    type="text"
                    className="form-control"
                    placeholder="Enter a new todo..."
                    value={newTodo}
                    onChange={(e) => setNewTodo(e.target.value)}
                    onKeyDown={(e) => e.key === 'Enter' && addTodo()}
                  />
                  <button
                    className="btn btn-primary"
                    onClick={addTodo}
                  >
                    Add Todo
                  </button>
                </div>
                
                {/* Parent selection for hierarchy */}
                <div className="mb-3">
                  <label className="form-label">Add as sub-task of:</label>
                  <select
                    className="form-select"
                    value={selectedParentId || ''}
                    onChange={(e) => setSelectedParentId(e.target.value ? parseInt(e.target.value) : null)}
                  >
                    <option value="">None (Top-level)</option>
                    {todos.filter(t => !t.parent_id && !t.completed).map(todo => (
                      <option key={todo.id} value={todo.id}>{todo.title}</option>
                    ))}
                  </select>
                </div>
              </div>
            </div>
          )}

          {/* Search for History */}
          {currentView === 'history' && (
            <div className="card mb-4">
              <div className="card-body">
                <h5 className="card-title">Search Completed Todos</h5>
                <div className="input-group mb-3">
                  <input
                    type="text"
                    className="form-control"
                    placeholder="Search completed todos..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
                  />
                  <button
                    className="btn btn-primary"
                    onClick={handleSearch}
                  >
                    Search
                  </button>
                </div>
              </div>
            </div>
          )}

          {/* Todo List */}
          <div className="card">
            <div className="card-body">
              <h5 className="card-title">
                {currentView === 'active' ? 'Active Todos' : 'Completed Todos'}
              </h5>
              
              {todos.length === 0 ? (
                <p className="text-center text-muted">
                  {currentView === 'active' 
                    ? 'No active todos. Add one above!' 
                    : 'No completed todos yet.'}
                </p>
              ) : (
                <>
                  {currentView === 'active' ? (
                    <div>
                      {todos.map(todo => !todo.parent_id && renderTodoItem(todo))}
                    </div>
                  ) : (
                    <div>
                      {todos.map(todo => (
                        <div key={todo.id} className="border-bottom pb-2 mb-2">
                          <div className="d-flex align-items-center">
                            <span className={todo.completed ? 'text-decoration-line-through text-muted' : ''}>
                              {todo.title}
                            </span>
                            <small className="text-muted ms-auto">
                              Completed: {formatDate(todo.completed_at)}
                            </small>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                  
                  {renderPagination()}
                </>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;
