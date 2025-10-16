# """
# Data access layer: provides CRUD via an abstract interface.
# Supports MongoDB (Motor) or JSON-file fallback.
# """
# from __future__ import annotations

# import os
# import json
# import asyncio
# from typing import List, Optional, Protocol, Dict, Any

# from models import Task, TaskCreate
# from utils import utc_now_iso, get_logger

# logger = get_logger("data_handler")

# class IDataHandler(Protocol):
#     async def create_task(self, payload: TaskCreate) -> Task: ...
#     async def list_tasks(self, *, is_completed: Optional[bool] = None, q: Optional[str] = None) -> List[Task]: ...
#     async def mark_completed(self, task_id: str) -> Task: ...
#     async def delete_task(self, task_id: str) -> bool: ...
#     async def get_task(self, task_id: str) -> Optional[Task]: ...

# # JSON implement
# class JSONDataHandler(IDataHandler):
#     def __init__(self, path: str = "data.json"):
#         self.path = path
#         if not os.path.exists(self.path):
#             with open(self.path, "w", encoding="utf-8") as f:
#                 json.dump({"tasks": []}, f)

#     async def _load(self) -> Dict[str, Any]:
#         return await asyncio.to_thread(lambda: json.load(open(self.path, "r", encoding="utf-8")))

#     async def _save(self, data: Dict[str, Any]) -> None:
#         def _write():
#             with open(self.path, "w", encoding="utf-8") as f:
#                 json.dump(data, f, ensure_ascii=False, indent=2)
#         await asyncio.to_thread(_write)

#     async def create_task(self, payload: TaskCreate) -> Task:
#         data = await self._load()
#         task = Task(**payload.model_dump(), created_at=utc_now_iso())
#         data["tasks"].append(task.model_dump())
#         await self._save(data)
#         return task

#     async def list_tasks(self, *, is_completed: Optional[bool] = None, q: Optional[str] = None) -> List[Task]:
#         data = await self._load()
#         tasks = [Task(**t) for t in data.get("tasks", [])]
#         if is_completed is not None:
#             tasks = [t for t in tasks if t.is_completed == is_completed]
#         if q:
#             ql = q.lower()
#             tasks = [t for t in tasks if ql in t.title.lower() or (t.description and ql in t.description.lower())]
#         return tasks

#     async def get_task(self, task_id: str) -> Optional[Task]:
#         data = await self._load()
#         for t in data.get("tasks", []):
#             if t["id"] == task_id:
#                 return Task(**t)
#         return None

#     async def mark_completed(self, task_id: str) -> Task:
#         data = await self._load()
#         for i, t in enumerate(data.get("tasks", [])):
#             if t["id"] == task_id:
#                 t["is_completed"] = True
#                 data["tasks"][i] = t
#                 await self._save(data)
#                 return Task(**t)
#         raise KeyError("Task not found")

#     async def delete_task(self, task_id: str) -> bool:
#         data = await self._load()
#         before = len(data.get("tasks", []))
#         data["tasks"] = [t for t in data.get("tasks", []) if t["id"] != task_id]
#         after = len(data["tasks"])
#         await self._save(data)
#         return after < before


# class MongoDataHandler(IDataHandler):
#     def __init__(self, uri: str, db_name: str = "task_db", collection: str = "tasks"):
#         from motor.motor_asyncio import AsyncIOMotorClient  
#         self.client = AsyncIOMotorClient(uri)
#         self.collection = self.client[db_name][collection]

#     async def create_task(self, payload: TaskCreate) -> Task:
#         task = Task(**payload.model_dump(), created_at=utc_now_iso())
#         await self.collection.insert_one(task.model_dump())
#         return task

#     async def list_tasks(self, *, is_completed: Optional[bool] = None, q: Optional[str] = None) -> List[Task]:
#         query: Dict[str, Any] = {}
#         if is_completed is not None:
#             query["is_completed"] = is_completed
#         if q:
#             query["$or"] = [
#                 {"title": {"$regex": q, "$options": "i"}},
#                 {"description": {"$regex": q, "$options": "i"}},
#             ]
#         cursor = self.collection.find(query).sort("created_at", 1)
#         docs = await cursor.to_list(length=10000)
#         return [Task(**d) for d in docs]

#     async def get_task(self, task_id: str) -> Optional[Task]:
#         doc = await self.collection.find_one({"id": task_id})
#         return Task(**doc) if doc else None

#     async def mark_completed(self, task_id: str) -> Task:
#         res = await self.collection.find_one_and_update(
#             {"id": task_id},
#             {"$set": {"is_completed": True}},
#             return_document=True  
#         )
#         if not res:
#             raise KeyError("Task not found")
#         return Task(**res)

#     async def delete_task(self, task_id: str) -> bool:
#         res = await self.collection.delete_one({"id": task_id})
#         return res.deleted_count == 1


# def get_data_handler() -> IDataHandler:
#     mongo_uri = os.getenv("MONGO_URI")
#     if mongo_uri:
#         logger.info("Using MongoDB backend")
#         return MongoDataHandler(mongo_uri)
#     path = os.getenv("DATA_FILE", "data.json")
#     logger.info("Using JSON file backend at %s", path)
#     return JSONDataHandler(path)

#  =======================================================================================================================



# """
# Data access layer: provides CRUD via an abstract interface.
# Supports MongoDB (Motor) + JSON file dual write.
# """
# from __future__ import annotations
# import os, json, asyncio
# from typing import List, Optional, Protocol, Dict, Any
# from models import Task, TaskCreate
# from utils import utc_now_iso, get_logger

# logger = get_logger("data_handler")

# # ---------------- Protocol Interface ----------------
# class IDataHandler(Protocol):
#     async def create_task(self, payload: TaskCreate) -> Task: ...
#     async def list_tasks(self, *, is_completed: Optional[bool] = None, q: Optional[str] = None) -> List[Task]: ...
#     async def mark_completed(self, task_id: str) -> Task: ...
#     async def delete_task(self, task_id: str) -> bool: ...
#     async def get_task(self, task_id: str) -> Optional[Task]: ...


# # ---------------- JSON FILE BACKEND ----------------
# class JSONDataHandler(IDataHandler):
#     def __init__(self, path: str = "data.json"):
#         self.path = path
#         if not os.path.exists(self.path):
#             with open(self.path, "w", encoding="utf-8") as f:
#                 json.dump({"tasks": []}, f)

#     async def _load(self) -> Dict[str, Any]:
#         return await asyncio.to_thread(lambda: json.load(open(self.path, "r", encoding="utf-8")))

#     async def _save(self, data: Dict[str, Any]) -> None:
#         def _write():
#             with open(self.path, "w", encoding="utf-8") as f:
#                 json.dump(data, f, ensure_ascii=False, indent=2)
#         await asyncio.to_thread(_write)

#     # async def create_task(self, payload: TaskCreate) -> Task:
#     #     data = await self._load()
#     #     task = Task(**payload.model_dump(), created_at=utc_now_iso())
#     #     data["tasks"].append(task.model_dump())
#     #     await self._save(data)
#     #     # print("✅ Mongo Insert:", task.model_dump())
#     #     return task

#     async def create_task(self, payload: TaskCreate) -> Task:
#         # Create a single Task object — generates one UUID
#         task = Task(**payload.model_dump(), created_at=utc_now_iso())
        
#         # Insert into MongoDB
#         await self.collection.insert_one(task.model_dump())
        
#         # Also append the same task into JSON (not re-creating a new Task)
#         data = await self.json_handler._load()
#         data["tasks"].append(task.model_dump())
#         await self.json_handler._save(data)
        
#         print("✅ Dual write with same ID:", task.model_dump()["id"])
#         return task

#     async def list_tasks(self, *, is_completed: Optional[bool] = None, q: Optional[str] = None) -> List[Task]:
#         data = await self._load()
#         tasks = [Task(**t) for t in data.get("tasks", [])]
#         if is_completed is not None:
#             tasks = [t for t in tasks if t.is_completed == is_completed]
#         if q:
#             ql = q.lower()
#             tasks = [t for t in tasks if ql in t.title.lower() or (t.description and ql in t.description.lower())]
#         return tasks

#     async def get_task(self, task_id: str) -> Optional[Task]:
#         data = await self._load()
#         for t in data.get("tasks", []):
#             if t["id"] == task_id:
#                 return Task(**t)
#         return None

#     async def mark_completed(self, task_id: str) -> Task:
#         data = await self._load()
#         for i, t in enumerate(data.get("tasks", [])):
#             if t["id"] == task_id:
#                 t["is_completed"] = True
#                 data["tasks"][i] = t
#                 await self._save(data)
#                 return Task(**t)
#         raise KeyError("Task not found")

#     async def delete_task(self, task_id: str) -> bool:
#         data = await self._load()
#         before = len(data.get("tasks", []))
#         data["tasks"] = [t for t in data.get("tasks", []) if t["id"] != task_id]
#         after = len(data["tasks"])
#         await self._save(data)
#         return after < before


# # ---------------- MONGODB BACKEND ----------------
# class MongoDataHandler(IDataHandler):
#     def __init__(self, uri: str, db_name: str = "task_db", collection: str = "tasks", json_path: str = "data.json"):
#         from motor.motor_asyncio import AsyncIOMotorClient
#         self.client = AsyncIOMotorClient(uri)
#         self.collection = self.client[db_name][collection]
#         self.json_handler = JSONDataHandler(json_path)  # ✅ Dual write setup

#     async def create_task(self, payload: TaskCreate) -> Task:
#         task = Task(**payload.model_dump(), created_at=utc_now_iso())
#         await self.collection.insert_one(task.model_dump())
#         # also write to JSON backup
#         await self.json_handler.create_task(payload)
#         return task

#     async def list_tasks(self, *, is_completed: Optional[bool] = None, q: Optional[str] = None) -> List[Task]:
#         try:
#             query: Dict[str, Any] = {}
#             if is_completed is not None:
#                 query["is_completed"] = is_completed
#             if q:
#                 query["$or"] = [
#                     {"title": {"$regex": q, "$options": "i"}},
#                     {"description": {"$regex": q, "$options": "i"}},
#                 ]
#             cursor = self.collection.find(query).sort("created_at", 1)
#             docs = await cursor.to_list(length=10000)
#             return [Task(**d) for d in docs]
#         except Exception:
#             # fallback to local JSON
#             logger.warning("MongoDB unavailable, falling back to JSON")
#             return await self.json_handler.list_tasks(is_completed=is_completed, q=q)

#     async def get_task(self, task_id: str) -> Optional[Task]:
#         doc = await self.collection.find_one({"id": task_id})
#         if doc:
#             return Task(**doc)
#         return await self.json_handler.get_task(task_id)

#     async def mark_completed(self, task_id: str) -> Task:
#         res = await self.collection.find_one_and_update(
#             {"id": task_id},
#             {"$set": {"is_completed": True}},
#             return_document=True
#         )
#         if res:
#             await self.json_handler.mark_completed(task_id)
#             return Task(**res)
#         raise KeyError("Task not found")

#     async def delete_task(self, task_id: str) -> bool:
#         res = await self.collection.delete_one({"id": task_id})
#         deleted = res.deleted_count == 1
#         if deleted:
#             await self.json_handler.delete_task(task_id)
#         return deleted


# # ---------------- Factory ----------------
# def get_data_handler() -> IDataHandler:
#     mongo_uri = os.getenv("MONGO_URI")
#     if mongo_uri:
#         logger.info("Using MongoDB + JSON dual backend")
#         return MongoDataHandler(mongo_uri)
#     path = os.getenv("DATA_FILE", "data.json")
#     logger.info("Using JSON-only backend at %s", path)
#     return JSONDataHandler(path)


# ==============================================================================================================================


"""
Data access layer: provides CRUD via an abstract interface.
Supports MongoDB (Motor) + JSON file dual write.
"""
from __future__ import annotations
import os, json, asyncio
from typing import List, Optional, Protocol, Dict, Any
from models import Task, TaskCreate
from utils import utc_now_iso, get_logger

logger = get_logger("data_handler")

# ---------------- Protocol Interface ----------------
class IDataHandler(Protocol):
    async def create_task(self, payload: TaskCreate) -> Task: ...
    async def list_tasks(self, *, is_completed: Optional[bool] = None, q: Optional[str] = None) -> List[Task]: ...
    async def mark_completed(self, task_id: str) -> Task: ...
    async def delete_task(self, task_id: str) -> bool: ...
    async def get_task(self, task_id: str) -> Optional[Task]: ...


# ---------------- JSON FILE BACKEND ----------------
class JSONDataHandler(IDataHandler):
    def __init__(self, path: str = "data.json"):
        self.path = path
        if not os.path.exists(self.path):
            with open(self.path, "w", encoding="utf-8") as f:
                json.dump({"tasks": []}, f)

    async def _load(self) -> Dict[str, Any]:
        return await asyncio.to_thread(lambda: json.load(open(self.path, "r", encoding="utf-8")))

    async def _save(self, data: Dict[str, Any]) -> None:
        def _write():
            with open(self.path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        await asyncio.to_thread(_write)

    async def create_task(self, payload: TaskCreate) -> Task:
        data = await self._load()
        task = Task(**payload.model_dump(), created_at=utc_now_iso())
        data["tasks"].append(task.model_dump())
        await self._save(data)
        return task

    async def list_tasks(self, *, is_completed: Optional[bool] = None, q: Optional[str] = None) -> List[Task]:
        data = await self._load()
        tasks = [Task(**t) for t in data.get("tasks", [])]
        if is_completed is not None:
            tasks = [t for t in tasks if t.is_completed == is_completed]
        if q:
            ql = q.lower()
            tasks = [t for t in tasks if ql in t.title.lower() or (t.description and ql in t.description.lower())]
        return tasks

    async def get_task(self, task_id: str) -> Optional[Task]:
        data = await self._load()
        for t in data.get("tasks", []):
            if t["id"] == task_id:
                return Task(**t)
        return None

    async def mark_completed(self, task_id: str) -> Task:
        data = await self._load()
        for i, t in enumerate(data.get("tasks", [])):
            if t["id"] == task_id:
                t["is_completed"] = True
                data["tasks"][i] = t
                await self._save(data)
                return Task(**t)
        raise KeyError("Task not found")

    async def delete_task(self, task_id: str) -> bool:
        data = await self._load()
        before = len(data.get("tasks", []))
        data["tasks"] = [t for t in data.get("tasks", []) if t["id"] != task_id]
        after = len(data["tasks"])
        await self._save(data)
        return after < before


# ---------------- MONGODB BACKEND ----------------
class MongoDataHandler(IDataHandler):
    def __init__(self, uri: str, db_name: str = "task_db", collection: str = "tasks", json_path: str = "data.json"):
        from motor.motor_asyncio import AsyncIOMotorClient
        self.client = AsyncIOMotorClient(uri)
        self.collection = self.client[db_name][collection]
        self.json_handler = JSONDataHandler(json_path)  # ✅ dual write backup

    async def create_task(self, payload: TaskCreate) -> Task:
        # Create one Task object with a single UUID
        task = Task(**payload.model_dump(), created_at=utc_now_iso())
        # Write to MongoDB
        await self.collection.insert_one(task.model_dump())
        # Write the same task to JSON file (keeping same ID)
        data = await self.json_handler._load()
        data["tasks"].append(task.model_dump())
        await self.json_handler._save(data)
        print("✅ Dual write success with same ID:", task.id)
        return task

    async def list_tasks(self, *, is_completed: Optional[bool] = None, q: Optional[str] = None) -> List[Task]:
        try:
            query: Dict[str, Any] = {}
            if is_completed is not None:
                query["is_completed"] = is_completed
            if q:
                query["$or"] = [
                    {"title": {"$regex": q, "$options": "i"}},
                    {"description": {"$regex": q, "$options": "i"}},
                ]
            cursor = self.collection.find(query).sort("created_at", 1)
            docs = await cursor.to_list(length=10000)
            return [Task(**d) for d in docs]
        except Exception:
            logger.warning("MongoDB unavailable, using JSON fallback")
            return await self.json_handler.list_tasks(is_completed=is_completed, q=q)

    async def get_task(self, task_id: str) -> Optional[Task]:
        doc = await self.collection.find_one({"id": task_id})
        if doc:
            return Task(**doc)
        return await self.json_handler.get_task(task_id)

    async def mark_completed(self, task_id: str) -> Task:
        res = await self.collection.find_one_and_update(
            {"id": task_id},
            {"$set": {"is_completed": True}},
            return_document=True
        )
        if res:
            await self.json_handler.mark_completed(task_id)
            return Task(**res)
        raise KeyError("Task not found")

    async def delete_task(self, task_id: str) -> bool:
        res = await self.collection.delete_one({"id": task_id})
        deleted = res.deleted_count == 1
        if deleted:
            await self.json_handler.delete_task(task_id)
        return deleted


# ---------------- Factory ----------------
def get_data_handler() -> IDataHandler:
    mongo_uri = os.getenv("MONGO_URI")
    if mongo_uri:
        logger.info("Using MongoDB + JSON dual backend")
        return MongoDataHandler(mongo_uri)
    path = os.getenv("DATA_FILE", "data.json")
    logger.info("Using JSON-only backend at %s", path)
    return JSONDataHandler(path)
