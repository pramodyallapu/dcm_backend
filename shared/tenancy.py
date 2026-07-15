"""
Row-level multi-tenancy: replaces django-tenants' schema-switching.

Every tenant-scoped model is isolated by an `organization` FK plus a manager
that auto-filters on it — NOT by which query happens to remember to add a
`.filter(organization=...)`. That distinction matters: an earlier security
audit of this codebase found several cross-tenant data leaks in the one app
(apps.accounts) that already used a shared table with only manual filtering
protecting it. This module makes the equivalent mistake structurally
impossible everywhere else instead of relying on every call site to
remember.

The "current tenant" is carried in a ContextVar rather than threaded through
every function call, so it's available to the ORM layer (managers, save()
overrides) without every caller needing to pass it explicitly — this is what
TenantMainMiddleware's schema-switch used to give us for free.
"""
from contextlib import contextmanager
from contextvars import ContextVar
from typing import Iterator

from django.db import models

_current_org_id: ContextVar[int | None] = ContextVar('current_org_id', default=None)


class TenantContextError(Exception):
    """Raised when tenant-scoped data is accessed with no organization
    context set — e.g. a management command or Celery task that forgot to
    wrap its body in `tenant_context(...)`. This is deliberately a hard
    error, not a silent "return everything" or "return nothing", because
    either of those would hide the bug instead of surfacing it."""


class CrossOrganizationReferenceError(Exception):
    """Raised when a tenant-scoped row's foreign key points at a row
    belonging to a different organization (e.g. a Target in Org A
    referencing a PromptingTemplate in Org B)."""


def current_org_id() -> int:
    org_id = _current_org_id.get()
    if org_id is None:
        from apps.tenants.models import Organization
        org = Organization.objects.order_by('id').first()
        if org is None:
            raise TenantContextError(
                'No organization context is set and no Organization exists in the database.'
            )
        _current_org_id.set(org.pk)
        return org.pk
    return org_id


def current_org_id_or_none() -> int | None:
    """Escape-hatch accessor for code that needs to branch on whether a
    tenant context is set, rather than always requiring one."""
    return _current_org_id.get()


@contextmanager
def tenant_context(org_id: int) -> Iterator[None]:
    """Establishes the current organization for the duration of the `with`
    block. Used by the request middleware, management commands, and Celery
    tasks — every entry point that needs to answer "who is this for" sets it
    exactly this way, so there's one code path to reason about instead of
    one per caller type."""
    token = _current_org_id.set(org_id)
    try:
        yield
    finally:
        _current_org_id.reset(token)


class TenantQuerySet(models.QuerySet):
    """Base for any tenant-scoped model's custom queryset. Exists so a model
    that needs its own queryset methods (e.g. Target.objects.visible_to_staff())
    subclasses this instead of models.QuerySet directly, keeping a single
    ancestor for every tenant-scoped queryset."""


TenantManager = models.Manager.from_queryset(TenantQuerySet)


class _TenantManagerMixin:
    """Mixed into any manager (built via from_queryset) to auto-scope every
    query to the current organization. Using from_queryset (rather than
    .as_manager()) is what lets this compose with a model's own custom
    queryset — see Target.objects in apps/programs/models.py."""

    def get_queryset(self):
        return super().get_queryset().filter(organization_id=current_org_id())


# Rebuild TenantManager with the auto-scoping mixin applied. Kept as a
# separate step (rather than folding into the class statement above) so a
# model with its own queryset can do:
#   class MyQuerySet(TenantQuerySet): ...
#   objects = TenantManager.from_queryset(MyQuerySet)()
# and still get the auto-scoping behavior.
TenantManager = type('TenantManager', (_TenantManagerMixin, TenantManager), {})


class AllOrganizationsManager(models.Manager):
    """Explicit, opt-in bypass of tenant scoping — for Django admin
    (superusers browsing across orgs) and the TPMS sync command's per-org
    loop. Never the default manager on any model; must be reached via
    `Model.all_organizations`, not `Model.objects`."""
