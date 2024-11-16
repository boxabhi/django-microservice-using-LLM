from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.files.base import ContentFile
from .task import analyze_repo_task
from .models import *
from celery.result import AsyncResult

@csrf_exempt
def start_task(request):
    """
    View to accept a task request, trigger the task, and return the task ID.
    """
    if request.method == "POST":
        try:
            repo_url = request.POST.get('repo_url')
            pr_number = request.POST.get('pr_number')
            github_token = request.POST.get('github_token')


            task = analyze_repo_task.delay(repo_url, pr_number, github_token)
           
            # Return the task ID to the client (this can be used to check the task status)
            return JsonResponse({"task_id": task.id, "status": "Task started"})
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)

    return JsonResponse({"message": "Only POST method is allowed"}, status=405)


def task_status_view(request, task_id):
    result = AsyncResult(task_id)

    response_data = {
        'task_id': task_id,
        'status': result.state,
    }

    if result.state == 'SUCCESS':
        response_data['result'] = result.result
    elif result.state == 'FAILURE':
        response_data['error'] = str(result.result)

    return JsonResponse(response_data)