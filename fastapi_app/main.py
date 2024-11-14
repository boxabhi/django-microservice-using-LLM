from fastapi import FastAPI, BackgroundTasks, HTTPException, status
from celery.result import AsyncResult
import httpx
from pydantic import BaseModel

app = FastAPI()

DJANGO_API_URL = "http://127.0.0.1:8000//" 

class TaskRequest(BaseModel):
    owner: str
    repo: str
    token: str

@app.post("/start_task/")
async def start_task_endpoint(task_request: TaskRequest):
    """
    Trigger the task in Django and return the task ID.
    """
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{DJANGO_API_URL}/start_task/",
            data={
                "owner": task_request.owner,
                "repo": task_request.repo,
                "token": task_request.token,
                
            }
        )
        if response.status_code == 200:
            task_id = response.json().get("task_id")
            return {"task_id": task_id, "status": "Task started"}
        else:
            return {"error": "Failed to start task", "details": response.text}

@app.get("/task_status/{task_id}/")
async def task_status_endpoint(task_id: str):
    """
    Check the status of the task by making a request to Django.
    """
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{DJANGO_API_URL}/task_status/{task_id}/")
        return response.json()