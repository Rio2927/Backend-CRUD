import os
from typing import List, Optional

from fastapi import FastAPI, HTTPException, Query, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from models import Task, TaskCreate, TaskUpdate
from data_handler import get_data_handler
from utils import get_logger
from dotenv import load_dotenv

load_dotenv()

logger = get_logger("app")
app = FastAPI(
    title="Task Management System API",
    version="1.0.0",
    description="Simple task manager with MongoDB or JSON storage."
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

handler = get_data_handler()

@app.get("/health")
async def health():
    return {"status": "ok", "backend": handler.__class__.__name__}

@app.post("/tasks", response_model=Task, status_code=status.HTTP_201_CREATED)
async def create_task(payload: TaskCreate):
    try:
        task = await handler.create_task(payload)
        return task
    except Exception as e:
        logger.exception("Failed to create task")
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/tasks", response_model=List[Task])
async def list_tasks(is_completed: Optional[bool] = Query(None), q: Optional[str] = Query(None)):
    tasks = await handler.list_tasks(is_completed=is_completed, q=q)
    return tasks

@app.put("/tasks/{task_id}", response_model=Task)
async def mark_task_completed(task_id: str, _body: TaskUpdate | None = None):
    
    try:
        if _body is not None:
            if _body.is_completed not in (True, False):
                raise HTTPException(status_code=400, detail="Invalid is_completed")

            if _body.is_completed is False:
                pass
            
        task = await handler.mark_completed(task_id)
        return task
    except KeyError:
        raise HTTPException(status_code=404, detail="Task not found")
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Failed to update task")
        raise HTTPException(status_code=400, detail=str(e))

@app.delete("/tasks/{task_id}")
async def delete_task(task_id: str):
    try:
        ok = await handler.delete_task(task_id)
        if not ok:
            raise HTTPException(status_code=404, detail="Task not found")
        return JSONResponse(status_code=200, content={"deleted": True})
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Failed to delete task")
        raise HTTPException(status_code=400, detail=str(e))