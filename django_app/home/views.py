from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.files.base import ContentFile
from .task import analyze_repo_task
from .models import *

@csrf_exempt
def start_task(request):
    """
    View to accept a task request, trigger the task, and return the task ID.
    """
    if request.method == "POST":
        try:
            owner = request.POST.get('owner')
            repo = request.POST.get('repo')
            token = request.POST.get('token')


            # Trigger the Celery task
            print(token)
            print(token)
            print(token)
            print(token)

            task = analyze_repo_task.delay(owner, repo, token)
            _task = TaskStatus.objects.create(task_id=task.id, status="STARTED")
            # Return the task ID to the client (this can be used to check the task status)
            return JsonResponse({"task_id": task.id, "status": "Task started"})
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)

    return JsonResponse({"message": "Only POST method is allowed"}, status=405)
