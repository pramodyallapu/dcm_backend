import os
from celery import Celery
from celery.signals import task_prerun

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.production')

app = Celery('dcm')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()


@task_prerun.connect
def set_tenant_context_for_task(sender=None, kwargs=None, **_):
    """If a task was queued with org_id in kwargs, activate that tenant's
    schema and row-level context so tenant-scoped models work inside tasks."""
    if not kwargs:
        return
    org_id = kwargs.get('org_id')
    if not org_id:
        return
    try:
        from django.db import connection
        from apps.tenants.models import Organization
        org = Organization.objects.get(pk=org_id)
        connection.set_tenant(org)
    except Exception:
        pass


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
