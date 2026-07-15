from ninja import Router
from ninja.errors import HttpError
from datetime import date

from apps.accounts.auth import jwt_auth
from .models import AuditLog

router = Router(auth=jwt_auth)


@router.get('/audit-logs')
def list_audit_logs(
    request,
    model: str | None = None,
    object_id: str | None = None,
    actor_id: int | None = None,
    action: str | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    limit: int = 100,
):
    if not request.user.has_role('admin', 'supervisor'):
        raise HttpError(403, 'Admin or supervisor access required')

    qs = AuditLog.objects.all()

    if model:
        qs = qs.filter(model=model)
    if object_id:
        qs = qs.filter(object_id=object_id)
    if actor_id:
        qs = qs.filter(actor_id=actor_id)
    if action:
        qs = qs.filter(action=action)
    if date_from:
        qs = qs.filter(timestamp__date__gte=date_from)
    if date_to:
        qs = qs.filter(timestamp__date__lte=date_to)

    limit = min(limit, 500)

    return [
        {
            'id': log.id,
            'actor_id': log.actor_id,
            'actor_email': log.actor_email,
            'actor_role': log.actor_role,
            'action': log.action,
            'model': log.model,
            'object_id': log.object_id,
            'object_repr': log.object_repr,
            'changes': log.changes,
            'timestamp': log.timestamp,
            'ip_address': log.ip_address,
            'request_id': log.request_id,
        }
        for log in qs[:limit]
    ]
