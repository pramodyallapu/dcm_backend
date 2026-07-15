from django.db import models
from shared.models import OrganizationScopedMixin


class AuditLog(OrganizationScopedMixin):
    class Action(models.TextChoices):
        CREATE = 'create', 'Create'
        UPDATE = 'update', 'Update'
        DELETE = 'delete', 'Delete'

    # Who
    actor_id = models.IntegerField(db_index=True)
    actor_email = models.CharField(max_length=254)
    actor_role = models.CharField(max_length=20)

    # What
    action = models.CharField(max_length=10, choices=Action.choices, db_index=True)
    model = models.CharField(max_length=100, db_index=True)   # e.g. "SessionRun"
    object_id = models.CharField(max_length=40, db_index=True)
    object_repr = models.CharField(max_length=200)            # str(instance)

    # Delta — only populated on UPDATE
    changes = models.JSONField(default=dict)

    # When
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)

    # Request metadata
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    request_id = models.CharField(max_length=36, blank=True)

    class Meta:
        app_label = 'audit'
        ordering = ['-timestamp']

    def __str__(self) -> str:
        return f'{self.actor_email} {self.action} {self.model}#{self.object_id} @ {self.timestamp:%Y-%m-%d %H:%M}'
