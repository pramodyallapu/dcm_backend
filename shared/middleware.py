"""
Tenant resolution middleware. Resolves Organization from hostname via Domain
lookup, falls back to reading org_id from the JWT token, and as a last resort
queries for the first Organization. Sets connection.set_tenant() for schema
routing and the tenancy contextvar for row-level scoping.
"""
import base64
import json
import logging

from django.db import connection
from apps.tenants.models import Domain, Organization

from .tenancy import tenant_context

logger = logging.getLogger(__name__)


def _org_id_from_jwt(request) -> int | None:
    """Extract org_id from the Bearer token without full verification."""
    auth = request.META.get('HTTP_AUTHORIZATION', '')
    if not auth.startswith('Bearer '):
        return None
    try:
        token = auth.split(' ', 1)[1]
        payload_b64 = token.split('.')[1]
        # Add padding
        payload_b64 += '=' * (4 - len(payload_b64) % 4)
        payload = json.loads(base64.b64decode(payload_b64))
        org_id = payload.get('org_id')
        return int(org_id) if org_id else None
    except Exception:
        return None


class TenantResolverMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self._org_cache: dict[int, Organization] = {}
        self._fallback_org: Organization | None = None

    def _get_org_by_pk(self, pk: int) -> Organization | None:
        if pk not in self._org_cache:
            try:
                self._org_cache[pk] = Organization.objects.get(pk=pk)
            except Organization.DoesNotExist:
                return None
        return self._org_cache[pk]

    def _get_fallback_org(self) -> Organization | None:
        if self._fallback_org is None:
            self._fallback_org = Organization.objects.order_by('id').first()
        return self._fallback_org

    def __call__(self, request):
        hostname = request.get_host().split(':')[0]
        request.tenant = None

        try:
            domain = Domain.objects.select_related('tenant').get(domain=hostname)
            request.tenant = domain.tenant
        except Domain.DoesNotExist:
            pass

        if request.tenant is None:
            org_id = _org_id_from_jwt(request)
            if org_id and org_id != 0:
                request.tenant = self._get_org_by_pk(org_id)

        if request.tenant is None:
            request.tenant = self._get_fallback_org()

        tenant = request.tenant
        if tenant is not None:
            connection.set_tenant(tenant)

        org_id = tenant.pk if tenant else None
        with tenant_context(org_id):
            return self.get_response(request)
