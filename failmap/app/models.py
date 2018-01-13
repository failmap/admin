# coding=UTF-8
# from __future__ import unicode_literals

import datetime
import importlib

import celery
from django.contrib.auth.models import User
from django.db import models
from jsonfield import JSONField

from ..app.common import ResultEncoder
from ..celery import app


class Job(models.Model):
    """Wrap any Celery task to easily 'manage' it from Django."""

    name = models.CharField(max_length=255, help_text="name of the job")
    task = models.TextField(help_text="celery task signature in string form")
    result_id = models.CharField(unique=True, null=True, blank=True, max_length=255,
                                 help_text="celery asyncresult ID for tracing task")
    status = models.CharField(max_length=255, help_text="status of the job")
    result = JSONField(help_text="output of the task as JSON", encoder_class=ResultEncoder)

    created_on = models.DateTimeField(auto_now_add=True, blank=True, null=True, help_text="when task was created")
    finished_on = models.DateTimeField(blank=True, null=True, help_text="when task ended")

    # TypeError: __init__() missing 1 required positional argument: 'on_delete'
    # probably because of blank and/or default.
    created_by = models.ForeignKey(User, blank=True, null=True, on_delete=models.CASCADE,)

    @classmethod
    def create(cls, task: celery.Task, name: str, request, *args, **kwargs) -> 'Job':
        """Create job object and publish task on celery queue."""
        # create database object
        job = cls(task=str(task))
        if request:
            job.created_by = request.user
        job.name = name[:255]
        job.status = 'created'
        job.save()

        # retrieve job object again with lock to prevent the `store_result` task from overwriting it before
        # `create` has a chance to update the `result_id`. (common when Celery is fast or set to 'eager')
        job = Job.objects.select_for_update().get(id=job.id)

        # publish original task which stores the result in this Job object
        result_id = (task | cls.store_result.s(job_id=job.id)).apply_async(*args, **kwargs)

        # store the task async result ID for reference
        job.result_id = result_id.id
        job.save()

        return job

    @staticmethod
    @app.task
    def store_result(result, job_id=None):
        """Celery task to store result of wrapped task after it has completed."""
        job = Job.objects.get(id=job_id)
        if not result:
            result = '-- task generated no result object --'
        job.result = result
        job.status = 'completed'
        job.finished_on = datetime.datetime.now()
        job.save()

    def __str__(self):
        return self.result_id or ''


@app.task
def create_job(task_module: str):
    """Helper to allow Jobs to be created using Celery Beat.

    task_module: module from which to call `create_task` which results in the task to be executed
    """

    module = importlib.import_module(task_module)
    task = module.create_task()

    return Job.create(task, task_module, None)
