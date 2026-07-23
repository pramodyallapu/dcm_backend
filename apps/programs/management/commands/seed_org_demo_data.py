"""
Seeds a full demo dataset for one Organization: Settings-page entities
(treatment areas, tags, target statuses, data fields, prompting/mastery/
workflow templates), a demo Client, and Programs+Targets for that client.

Written org-scoped from the start (tenant_context, not schema_context) —
this is what every seed command moves to once the M3 rework of the
schema-based ones lands; this one didn't exist before, so it started here
directly.

Usage:
    python manage.py seed_org_demo_data --org dev
    python manage.py seed_org_demo_data --org dev --clear
"""
from django.core.management.base import BaseCommand, CommandError
from django_tenants.utils import schema_context

from apps.tenants.models import Organization
from shared.tenancy import tenant_context

SEED_STATUSES = [
    {'key': 'waiting', 'label': 'Waiting', 'icon': 'hourglass', 'color': '#94a3b8', 'is_staff_visible': False, 'is_default': True, 'display_order': 0},
    {'key': 'probe', 'label': 'Probe', 'icon': 'clipboard-list', 'color': '#d97706', 'is_staff_visible': True, 'is_default': False, 'display_order': 1},
    {'key': 'acquisition', 'label': 'Acquisition', 'icon': 'graduation-cap', 'color': '#2563eb', 'is_staff_visible': True, 'is_default': False, 'display_order': 2},
    {'key': 'mastered', 'label': 'Mastered', 'icon': 'trophy', 'color': '#7c3aed', 'is_staff_visible': True, 'is_default': False, 'display_order': 3},
    {'key': 'closed', 'label': 'Closed', 'icon': 'check-circle', 'color': '#059669', 'is_staff_visible': False, 'is_default': False, 'display_order': 4},
    {'key': 'hold', 'label': 'Hold', 'icon': 'hand', 'color': '#ea580c', 'is_staff_visible': False, 'is_default': False, 'display_order': 5},
    {'key': 'discontinued', 'label': 'Discontinued', 'icon': 'x-square', 'color': '#dc2626', 'is_staff_visible': False, 'is_default': False, 'display_order': 6},
]

TREATMENT_AREAS = ['Communication', 'Language', 'Daily Living Skills', 'Behavior Management', 'Social Skills']

PROGRAM_TAGS = [
    {'name': 'Priority', 'color': '#dc2626'},
    {'name': 'New', 'color': '#2563eb'},
    {'name': 'Review', 'color': '#d97706'},
    {'name': 'Parent Training', 'color': '#7c3aed'},
]

DATA_FIELDS = [
    {'name': 'Insurance Authorization #', 'field_type': 'text', 'field_location': 'treatment_tab'},
    {'name': 'Re-eval Due Date', 'field_type': 'date', 'field_location': 'treatment_tab'},
    {'name': 'Parent Consent on File', 'field_type': 'yes_no', 'field_location': 'instructions_tab'},
]

WORKFLOWS = [
    {
        'name': 'Standard DTT Workflow',
        'description': 'Probe → Acquisition → Mastered progression for discrete trial training.',
        'phases': [
            {'phase': 'probe', 'criteria': {'consecutive_sessions': 1, 'threshold_pct': 100, 'minimum_trials': 3}, 'on_success': 'acquisition', 'on_regression': None},
            {'phase': 'acquisition', 'criteria': {'consecutive_sessions': 3, 'threshold_pct': 80, 'minimum_trials': 5}, 'on_success': 'mastered', 'on_regression': 'probe'},
            {'phase': 'mastered', 'criteria': {'consecutive_sessions': 2, 'threshold_pct': 90, 'minimum_trials': 5}, 'on_success': 'maintenance', 'on_regression': 'acquisition'},
        ],
        'is_org_default': True,
    },
    {
        'name': 'Behavior Reduction Workflow',
        'description': 'Tracks frequency/duration toward reduction goals.',
        'phases': [
            {'phase': 'baseline', 'criteria': {'consecutive_sessions': 3, 'threshold_pct': 0, 'minimum_trials': 1}, 'on_success': 'acquisition', 'on_regression': None},
            {'phase': 'acquisition', 'criteria': {'consecutive_sessions': 5, 'threshold_pct': 20, 'minimum_trials': 1}, 'on_success': 'mastered', 'on_regression': 'baseline'},
        ],
        'is_org_default': False,
    },
]

PROGRAMS = [
    {
        'name': 'Mand Training — Basic',
        'category': 'skill_acquisition',
        'treatment_area': 'Communication',
        'phase': 'teaching',
        'objective': 'Client will independently request preferred items, activities, and breaks using vocal speech or AAC device across 3 consecutive sessions with 80% accuracy.',
        'instructions': 'Use the PECS or vocal mand protocol. Present the preferred item just out of reach. Wait 3-5 seconds for a spontaneous mand before prompting. Reinforce immediately.',
        'tags': ['Communication'],
        'targets': [
            {'name': 'Request preferred snack', 'measurement_type': 'discrete_trial', 'status': 'acquisition', 'sd_text': 'Present snack just out of reach, pause 5s'},
            {'name': 'Request break', 'measurement_type': 'discrete_trial', 'status': 'acquisition', 'sd_text': 'Present task demand, wait for mand'},
            {'name': 'Request preferred toy', 'measurement_type': 'discrete_trial', 'status': 'probe', 'sd_text': 'Hold toy visible but out of reach'},
            {'name': 'Request help', 'measurement_type': 'discrete_trial', 'status': 'waiting', 'sd_text': 'Present difficult task, wait for "help" mand'},
        ],
    },
    {
        'name': 'Receptive Language — Body Parts',
        'category': 'skill_acquisition',
        'treatment_area': 'Language',
        'phase': 'teaching',
        'objective': 'Client will identify 10 body parts by pointing when asked "Show me ___" with 90% accuracy across 3 consecutive sessions.',
        'instructions': 'Use a card or doll for receptive identification. Mix targets across trials. Use errorless learning initially, fading prompts systematically.',
        'tags': ['New'],
        'targets': [
            {'name': 'Identify nose', 'measurement_type': 'discrete_trial', 'status': 'mastered', 'sd_text': 'Show me your nose'},
            {'name': 'Identify ears', 'measurement_type': 'discrete_trial', 'status': 'acquisition', 'sd_text': 'Show me your ears'},
            {'name': 'Identify eyes', 'measurement_type': 'discrete_trial', 'status': 'probe', 'sd_text': 'Show me your eyes'},
        ],
    },
    {
        'name': 'Tantrum Behavior',
        'category': 'behavior_reduction',
        'treatment_area': 'Behavior Management',
        'phase': 'teaching',
        'objective': 'Reduce duration of tantrum episodes to under 2 minutes per session average.',
        'instructions': 'Record start and end time of each tantrum. Use planned ignoring unless safety is a concern.',
        'tags': ['Priority'],
        'targets': [
            {'name': 'Tantrum duration', 'measurement_type': 'duration', 'status': 'acquisition', 'sd_text': 'Record total duration of tantrum episode in seconds'},
        ],
    },
]


ORG_PROGRAM_TEMPLATES = [
    {
        'name': 'Mand Training — Template',
        'category': 'skill_acquisition',
        'treatment_area': 'Communication',
        'phase': 'teaching',
        'objective': 'Standard mand-training template for facility-wide reuse — copy to a client and adjust targets as needed.',
        'instructions': 'Use the PECS or vocal mand protocol. Present the preferred item just out of reach and wait for a spontaneous mand before prompting.',
        'tags': ['Communication'],
        'targets': [
            {'name': 'Request preferred item', 'measurement_type': 'discrete_trial', 'status': 'waiting', 'sd_text': 'Present item just out of reach, pause 5s'},
            {'name': 'Request break', 'measurement_type': 'discrete_trial', 'status': 'waiting', 'sd_text': 'Present task demand, wait for mand'},
        ],
    },
    {
        'name': 'Receptive Identification — Template',
        'category': 'skill_acquisition',
        'treatment_area': 'Language',
        'phase': 'teaching',
        'objective': 'Generic receptive-ID template (colors, shapes, body parts, etc.) — swap in target-specific stimuli per client.',
        'instructions': 'Present 2-3 field array. Ask "Show me ___". Use errorless learning initially, fading prompts systematically.',
        'tags': ['New'],
        'targets': [
            {'name': 'Identify target 1', 'measurement_type': 'discrete_trial', 'status': 'waiting', 'sd_text': 'Show me ___'},
            {'name': 'Identify target 2', 'measurement_type': 'discrete_trial', 'status': 'waiting', 'sd_text': 'Show me ___'},
            {'name': 'Identify target 3', 'measurement_type': 'discrete_trial', 'status': 'waiting', 'sd_text': 'Show me ___'},
        ],
    },
    {
        'name': 'Behavior Reduction — Template',
        'category': 'behavior_reduction',
        'treatment_area': 'Behavior Management',
        'phase': 'baseline',
        'objective': 'Generic behavior-reduction template — define the target behavior operationally per client before assigning.',
        'instructions': 'Record frequency/duration per the assigned measurement type. Confirm function via FBA before implementing a reduction procedure.',
        'tags': ['Priority'],
        'targets': [
            {'name': 'Target behavior', 'measurement_type': 'frequency', 'status': 'waiting', 'sd_text': 'Record each occurrence'},
        ],
    },
]


class Command(BaseCommand):
    help = 'Seed Settings-page data, a demo client, and programs/targets for one Organization'

    def add_arguments(self, parser):
        parser.add_argument('--org', required=True, help='Organization schema_name or slug (e.g. dev)')
        parser.add_argument('--clear', action='store_true', help='Delete this org\'s existing seeded programs/client first')

    def handle(self, *args, **options):
        org = self._resolve_org(options['org'])
        with schema_context(org.schema_name), tenant_context(org.pk):
            self._seed(org, options['clear'])

    def _resolve_org(self, ref: str) -> Organization:
        try:
            return Organization.objects.get(schema_name=ref)
        except Organization.DoesNotExist:
            pass
        try:
            return Organization.objects.get(slug=ref)
        except Organization.DoesNotExist:
            raise CommandError(f'No Organization with schema_name or slug "{ref}"')

    def _seed(self, org: Organization, clear: bool):
        from apps.clients.models import Client
        from apps.programs.models import (
            PromptingTemplate, Program, ProgramDataField,
            ProgramTag, Target, TargetStatus, TreatmentArea, WorkflowTemplate,
        )

        self.stdout.write(f'Seeding demo data for organization: {org.name} ({org.schema_name})')

        if clear:
            deleted, _ = Program.objects.filter(name__in=[p['name'] for p in PROGRAMS]).delete()
            self.stdout.write(f'  Cleared {deleted} previously-seeded program-tree row(s)')

        # ── Settings: statuses ──────────────────────────────────────────────
        for row in SEED_STATUSES:
            _, created = TargetStatus.objects.get_or_create(key=row['key'], defaults=row)
            self.stdout.write(f'  {"Created" if created else "Found"} status: {row["label"]}')

        # ── Settings: treatment areas ────────────────────────────────────────
        for name in TREATMENT_AREAS:
            TreatmentArea.objects.get_or_create(name=name)

        # ── Settings: tags ───────────────────────────────────────────────────
        tag_objects = {}
        for tag_data in PROGRAM_TAGS:
            tag, _ = ProgramTag.objects.get_or_create(name=tag_data['name'], defaults={'color': tag_data['color']})
            tag_objects[tag_data['name']] = tag

        # ── Settings: data fields ───────────────────────────────────────────
        for field_data in DATA_FIELDS:
            ProgramDataField.objects.get_or_create(name=field_data['name'], defaults=field_data)

        # ── Settings: prompting templates ───────────────────────────────────
        prompt_tpl, _ = PromptingTemplate.objects.get_or_create(
            name='Standard Prompt Hierarchy',
            defaults={
                'description': 'Full Physical → Partial Physical → Model → Gestural → Independent',
                'levels': [
                    {'label': 'Full Physical', 'score': 0, 'color': '#e74c3c', 'abbreviation': 'FP'},
                    {'label': 'Partial Physical', 'score': 0, 'color': '#e67e22', 'abbreviation': 'PP'},
                    {'label': 'Model', 'score': 0, 'color': '#f1c40f', 'abbreviation': 'M'},
                    {'label': 'Gestural', 'score': 0, 'color': '#3498db', 'abbreviation': 'G'},
                    {'label': 'Independent', 'score': 1, 'color': '#2ecc71', 'abbreviation': 'I'},
                ],
                'is_org_default': True,
            },
        )
        # ── Settings: workflow templates ────────────────────────────────────
        workflow_objects = {}
        for wf_data in WORKFLOWS:
            wf, created = WorkflowTemplate.objects.get_or_create(
                name=wf_data['name'],
                defaults={
                    'description': wf_data['description'],
                    'phases': wf_data['phases'],
                    'is_org_default': wf_data['is_org_default'],
                },
            )
            workflow_objects[wf_data['name']] = wf
            self.stdout.write(f'  {"Created" if created else "Found"} workflow: {wf.name}')

        default_wf = workflow_objects.get('Standard DTT Workflow')
        behavior_wf = workflow_objects.get('Behavior Reduction Workflow')

        # ── Demo client ──────────────────────────────────────────────────────
        client, created = Client.objects.get_or_create(
            first_name='Jordan',
            last_name='Demo',
            defaults={'preferred_name': 'Jordan', 'status': 'active'},
        )
        self.stdout.write(f'  {"Created" if created else "Found"} client: {client.full_name} (id={client.id})')

        # ── Programs + targets ───────────────────────────────────────────────
        total_programs = 0
        total_targets = 0
        for i, prog_data in enumerate(PROGRAMS):
            if Program.objects.filter(name=prog_data['name'], external_client_id=client.id).exists():
                continue
            wf = behavior_wf if prog_data['category'] == 'behavior_reduction' else default_wf
            program = Program.objects.create(
                external_client_id=client.id,
                name=prog_data['name'],
                category=prog_data['category'],
                treatment_area=prog_data['treatment_area'],
                phase=prog_data['phase'],
                objective=prog_data['objective'],
                instructions=prog_data['instructions'],
                tags=prog_data['tags'],
                workflow_template=wf,
                status='active',
                display_order=i * 10,
            )
            total_programs += 1
            for j, t_data in enumerate(prog_data['targets']):
                use_prompt = t_data['measurement_type'] == 'discrete_trial'
                Target.objects.create(
                    program=program,
                    name=t_data['name'],
                    measurement_type=t_data['measurement_type'],
                    status=t_data['status'],
                    sd_text=t_data.get('sd_text', ''),
                    prompting_template=prompt_tpl if use_prompt else None,
                    is_visible_to_staff=t_data['status'] in ('probe', 'acquisition', 'mastered'),
                    display_order=j * 10,
                )
                total_targets += 1
            self.stdout.write(f'  Created program: "{program.name}" ({len(prog_data["targets"])} targets)')

        # ── Org-level program library (/org-programs) ───────────────────────
        # Scoped by created_by.external_admin_id (apps/backend/apps/programs/api.py's
        # _org_qs), not by `organization` — so the creator must share the same
        # external_admin_id as whoever is logged in and viewing /org-programs.
        from apps.accounts.models import User
        creator = User.objects.filter(role='admin', external_admin_id__isnull=False).order_by('id').first()
        total_templates = 0
        total_template_targets = 0
        if creator is None:
            self.stdout.write(self.style.WARNING(
                '  Skipping org-program library — no admin user with external_admin_id set was found.'
            ))
        else:
            for i, tpl_data in enumerate(ORG_PROGRAM_TEMPLATES):
                if Program.objects.filter(name=tpl_data['name'], is_template=True).exists():
                    continue
                wf = behavior_wf if tpl_data['category'] == 'behavior_reduction' else default_wf
                template = Program.objects.create(
                    is_template=True,
                    external_client_id=None,
                    name=tpl_data['name'],
                    category=tpl_data['category'],
                    treatment_area=tpl_data['treatment_area'],
                    phase=tpl_data['phase'],
                    objective=tpl_data['objective'],
                    instructions=tpl_data['instructions'],
                    tags=tpl_data['tags'],
                    workflow_template=wf,
                    status='active',
                    display_order=i * 10,
                    created_by=creator,
                )
                total_templates += 1
                for j, t_data in enumerate(tpl_data['targets']):
                    Target.objects.create(
                        program=template,
                        name=t_data['name'],
                        measurement_type=t_data['measurement_type'],
                        status=t_data['status'],
                        sd_text=t_data.get('sd_text', ''),
                        is_visible_to_staff=False,
                        display_order=j * 10,
                    )
                    total_template_targets += 1
                self.stdout.write(f'  Created org-program template: "{template.name}" ({len(tpl_data["targets"])} targets)')

        self.stdout.write(self.style.SUCCESS(
            f'\nDone — org "{org.name}": {total_programs} programs, {total_targets} targets, '
            f'client id={client.id}, {total_templates} org-program template(s) with {total_template_targets} target(s), '
            f'plus Settings-page data (statuses/areas/tags/fields/templates).'
        ))
