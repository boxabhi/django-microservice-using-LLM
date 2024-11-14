from celery import Celery
from django.core.files.base import ContentFile
from django.utils import timezone
from .models import TaskStatus
import base64
import time
import requests
from groq import Groq
from celery import shared_task
from .models import RepoData

# Set up Celery in Django
app = Celery('django_app')
app.config_from_object('django.conf:settings', namespace='CELERY')

# Celery task for processing file content and analyzing it
@shared_task
def analyze_repo_task(owner, repo, token=None):
    print(owner, repo, token)
    # Fetch all files from the repo
    def fetch_repo_contents(owner, repo, path="", token=None):
        url = f"https://api.github.com/repos/{owner}/{repo}/contents/{path}"
        headers = {"Authorization": f"token {token}"} if token else {}

        response = requests.get(url, headers=headers)
        response.raise_for_status()
        contents = response.json()

        files = []
        for item in contents:
            if item["type"] == "file":
                files.append(item["path"])
            elif item["type"] == "dir":
                files.extend(fetch_repo_contents(owner, repo, item["path"], token))

        return files

    # Fetch the content of a file in base64
    def get_file_content_base64(owner, repo, file_path, token=None):
        url = f"https://api.github.com/repos/{owner}/{repo}/contents/{file_path}"
        headers = {"Authorization": f"token {token}"} if token else {}

        response = requests.get(url, headers=headers)
        response.raise_for_status()
        content = response.json()
        return content["content"]

    # Perform code quality check
    def code_quality_checker(file_content,repo):
        file_content = base64.b64decode(file_content).decode()
        client = Groq(api_key="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")
        completion = client.chat.completions.create(
            model="llama3-8b-8192",
            messages=[{
                "role": "user",
                "content": f"Analyze the code file provided below for code quality, potential bugs, performance issues, and best practices violations.\n\n{file_content}"
            }],
            temperature=1,
            max_tokens=1024,
            top_p=1,
            stream=True
        )
        for chunk in completion:
            print(chunk.choices[0].delta.content or "", end="")
            RepoData.objects.create(
                repo_name = repo,
                code_analysis =chunk.choices[0].delta.content
                )

    # Fetch files and analyze them
    files = fetch_repo_contents(owner, repo, token=token)
    for file_path in files:
        try:
            file_content_base64 = get_file_content_base64(owner, repo, file_path, token=token)
            code_quality_checker(file_content_base64,repo)
        except Exception as e:
            print(f"Error processing {file_path}: {str(e)}")

    task_id = analyze_repo_task.request.id
    _task = TaskStatus.objects.filter(task_id=task_id, status="STARTED").update(status="COMPLETED")