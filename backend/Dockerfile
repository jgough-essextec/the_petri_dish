FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

ENV DATABASE_PATH=/app/todos.db

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
