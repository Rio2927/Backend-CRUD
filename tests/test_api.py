import os
import json
import pytest
from httpx import AsyncClient
from fastapi import status

# Ensure JSON backend for tests
os.environ["DATA_FILE"] = "test_data.json"

from app import app  # noqa

@pytest.mark.asyncio
async def test_create_and_list_tasks(tmp_path, monkeypatch):
    # point data file to tmp path
    data_file = tmp_path / "data.json"
    monkeypatch.setenv("DATA_FILE", str(data_file))

    async with AsyncClient(app=app, base_url="http://test") as ac:
        # create
        res = await ac.post("/tasks", json={"title": "Write tests", "description": "pytest + httpx"})
        assert res.status_code == status.HTTP_201_CREATED
        task = res.json()
        assert task["title"] == "Write tests"
        assert task["is_completed"] is False
        task_id = task["id"]

        # list
        res = await ac.get("/tasks")
        assert res.status_code == 200
        tasks = res.json()
        assert any(t["id"] == task_id for t in tasks)

        # mark completed
        res = await ac.put(f"/tasks/{task_id}")
        assert res.status_code == 200
        assert res.json()["is_completed"] is True

        # filter completed=true
        res = await ac.get("/tasks", params={"is_completed": "true"})
        assert res.status_code == 200
        tasks = res.json()
        assert len(tasks) == 1
        assert tasks[0]["id"] == task_id

        # delete
        res = await ac.delete(f"/tasks/{task_id}")
        assert res.status_code == 200
        assert res.json()["deleted"] is True

        # delete again -> 404
        res = await ac.delete(f"/tasks/{task_id}")
        assert res.status_code == 404