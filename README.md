# Task Management System API (FastAPI + Mongo/JSON)

Minimal, modular Task API demonstrating clean Python structure, Pydantic models, and a pluggable data layer.
- **Primary storage:** MongoDB (via Motor)
- **Fallback:** Local JSON file
- **Async API:** FastAPI endpoints with OpenAPI/Swagger
- **Extras:** Basic logging, filtering (`?is_completed=`, `?q=`), unit test

---

## Project Structure

```text
.
├── app.py                # API entry point (FastAPI)
├── data_handler.py       # Data layer (Mongo + JSON implementations)
├── models.py             # Pydantic models
├── utils.py              # Helpers (timestamps, logging, parsing)
├── tests/
│   └── test_api.py       # Pytest for API happy-path
├── requirements.txt
└── README.md
```

---

## Setup

### 1) Create & activate a virtualenv (recommended)

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
```

### 2) Install dependencies
```bash
pip install -r requirements.txt
```

### 3a) Run with **MongoDB** (preferred)
Set `MONGO_URI` to your Mongo connection string (local or Atlas), e.g.:
```bash
export MONGO_URI="mongodb://localhost:27017"
uvicorn app:app --reload --port 8000
```

### 3b) Run with **JSON file** (fallback)
```bash
export DATA_FILE="data.json"   # optional; defaults to data.json in cwd
uvicorn app:app --reload --port 8000
```

### OpenAPI / Swagger
- Swagger UI: http://127.0.0.1:8000/docs
- ReDoc: http://127.0.0.1:8000/redoc
- Health check: `GET /health`

---

## Endpoints

### Create task
`POST /tasks`
```json
{
  "title": "Write unit tests",
  "description": "Cover CRUD paths"
}
```
**201 Created**
```json
{
  "id": "a2b4...uuid",
  "title": "Write unit tests",
  "description": "Cover CRUD paths",
  "is_completed": false,
  "created_at": "2025-10-15T12:00:00.000Z"
}
```

### List tasks (with optional filters)
`GET /tasks?is_completed=true&q=unit`
**200 OK**
```json
[
  {
    "id": "a2b4...",
    "title": "Write unit tests",
    "description": "Cover CRUD paths",
    "is_completed": true,
    "created_at": "2025-10-15T12:00:00.000Z"
  }
]
```

### Mark as completed
`PUT /tasks/{id}`
**200 OK** → returns updated task

### Delete task
`DELETE /tasks/{id}`
**200 OK** `{ "deleted": true }`
- **404 Not Found** if id doesn't exist

---

## Testing

This suite runs on the JSON backend by setting `DATA_FILE` to a temporary path.

```bash
pip install pytest httpx
pytest -q
```

---

## Design Notes & Assumptions

- **IDs** are UUIDv4 strings to avoid ObjectId coupling and keep parity across JSON and Mongo.
- **Timestamps** are stored as ISO8601 UTC strings with `Z` suffix.
- **Mongo queries** use case-insensitive regex for simple search and are indexed only by default `_id`—in a real app, add indexes on `id`, `is_completed`, and `created_at`.
- **Error handling:** 400 for bad inputs, 404 for missing IDs; exceptions are logged.
- **Extensibility:** The `IDataHandler` protocol allows future backends (e.g., PostgreSQL) without touching the API layer.

---

## Curl Examples

```bash
# Create
curl -X POST http://127.0.0.1:8000/tasks -H "Content-Type: application/json" -d '{"title":"Demo","description":"try it"}'

# List all
curl http://127.0.0.1:8000/tasks

# List only completed
curl http://127.0.0.1:8000/tasks?is_completed=true

# Search by text
curl http://127.0.0.1:8000/tasks?q=demo

# Mark completed
curl -X PUT http://127.0.0.1:8000/tasks/{id}

# Delete
curl -X DELETE http://127.0.0.1:8000/tasks/{id}
```

---

## Logging

Console logging is enabled by default. Customize in `utils.get_logger`.