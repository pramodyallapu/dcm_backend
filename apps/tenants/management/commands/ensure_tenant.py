"""
Idempotent bootstrap for single-tenant production deployments.

Reads ORG_NAME / ORG_SCHEMA / ORG_DOMAIN from env (with sensible defaults),
creates the Organization + Domain rows if they don't exist, then runs
migrate_schemas so TENANT_APPS tables land in the right schema.

Safe to run on every deploy — exits cleanly if everything is already set up.
"""
import os

from django.core.management import call_command
from django.core.management.base import BaseCommand

from apps.tenants.models import Domain, Organization


class Command(BaseCommand):
    help = 'Ensure the production tenant exists and its schema is migrated.'

    def handle(self, *args, **options):
        name   = os.environ.get('ORG_NAME',   'Progressly')
        schema = os.environ.get('ORG_SCHEMA', 'public')
        domain = os.environ.get('ORG_DOMAIN', 'api.progressly.io')

        org, org_created = Organization.objects.get_or_create(
            schema_name=schema,
            defaults={'name': name, 'slug': schema, 'plan': 'starter'},
        )
        if org_created:
            self.stdout.write(self.style.SUCCESS(f'Created org "{name}" (schema={schema})'))
        else:
            self.stdout.write(f'Org already exists: "{org.name}" (schema={org.schema_name})')

        _, dom_created = Domain.objects.get_or_create(
            tenant=org,
            defaults={'domain': domain, 'is_primary': True},
        )
        if dom_created:
            self.stdout.write(self.style.SUCCESS(f'Registered domain "{domain}"'))
        else:
            self.stdout.write(f'Domain already registered for this org')

        self.stdout.write('Running tenant migrations…')
        call_command('migrate_schemas', schema=schema, verbosity=1)
        self.stdout.write(self.style.SUCCESS('Done.'))
