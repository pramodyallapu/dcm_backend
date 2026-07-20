from ninja import NinjaAPI
from apps.accounts.api import router as accounts_router
from apps.accounts.auth import jwt_auth, api_key_auth
from apps.clients.api import router as clients_router
from apps.programs.api import router as programs_router
from apps.sessions.api import router as sessions_router
from apps.notes.api import router as notes_router
from apps.analytics.api import router as analytics_router
from apps.exports.api import router as exports_router
from apps.notifications.api import router as notifications_router
from apps.integrations.api import router as integrations_router
from apps.audit.api import router as audit_router

api = NinjaAPI(
    title='DCM Platform API',
    version='1.0.0',
    description=(
        'Data Collection Platform API. '
        'Authenticate with Bearer JWT (users) or X-API-Key header (facility integrations).'
    ),
    docs_url='/docs',
    auth=[jwt_auth, api_key_auth],
)

api.add_router('/auth', accounts_router, tags=['Authentication'])
api.add_router('/clients', clients_router, tags=['Clients'])
api.add_router('/', programs_router, tags=['Programs'])
api.add_router('/', sessions_router, tags=['Sessions'])
api.add_router('/', notes_router, tags=['Notes'])
api.add_router('/', analytics_router, tags=['Analytics'])
api.add_router('/', exports_router, tags=['Exports'])
api.add_router('/', notifications_router, tags=['Notifications'])
api.add_router('/integrations', integrations_router, tags=['Integrations'])
api.add_router('/', audit_router, tags=['Audit'])


@api.get('/dashboard', auth=jwt_auth, tags=['System'])
def dashboard(request):
    """
    Single endpoint that returns everything the dashboard needs in one round-trip:
    - pending review counts (sessions + notes)
    - today's appointments
    - active client count
    - unread notification count
    - recent audit activity (admin only)
    """
    from django.utils import timezone
    from django.db.models import Count, Q
    from apps.sessions.models import SessionRun
    from apps.notes.models import LessonNote
    from apps.notifications.models import Notification
    from apps.clients.models import Client

    user = request.user
    today = timezone.now().date()

    # Sessions pending review
    sessions_pending = SessionRun.objects.filter(status='submitted').count()

    # My open sessions (staff)
    my_open_sessions = (
        SessionRun.objects.filter(staff_id=user.id, status='open').count()
        if user.role == 'staff' else None
    )

    # Notes pending review
    notes_pending = LessonNote.objects.filter(status='submitted').count()

    # My draft notes (staff)
    my_draft_notes = (
        LessonNote.objects.filter(staff_id=user.id, status='draft').count()
        if user.role == 'staff' else None
    )

    # Active clients
    active_clients = Client.objects.filter(status='active').count()

    # Total clients (all statuses) — the admin dashboard's "Total clients" card
    total_clients = Client.objects.count()

    # Unread notifications for this user
    unread_notifications = Notification.objects.filter(
        recipient_id=user.id, read_at__isnull=True
    ).count()

    # Today's sessions
    sessions_today = SessionRun.objects.filter(started_at__date=today).count()

    result = {
        'sessions_pending_review': sessions_pending,
        'notes_pending_review': notes_pending,
        'active_clients': active_clients,
        'total_clients': total_clients,
        'unread_notifications': unread_notifications,
        'sessions_today': sessions_today,
        'my_open_sessions': my_open_sessions,
        'my_draft_notes': my_draft_notes,
    }

    # Recent audit activity — admin/supervisor only
    if user.has_role('admin', 'supervisor'):
        from apps.audit.models import AuditLog
        recent = AuditLog.objects.select_related()[:10]
        result['recent_activity'] = [
            {
                'actor_email': log.actor_email,
                'action': log.action,
                'model': log.model,
                'object_repr': log.object_repr,
                'timestamp': log.timestamp,
            }
            for log in recent
        ]

    return result
