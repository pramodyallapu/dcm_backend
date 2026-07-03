from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


SEED_STATUSES = [
    {'key': 'waiting',      'label': 'Waiting',      'icon': 'hourglass',      'color': '#94a3b8', 'is_staff_visible': False, 'is_default': True,  'display_order': 0},
    {'key': 'probe',        'label': 'Probe',        'icon': 'clipboard-list', 'color': '#d97706', 'is_staff_visible': True,  'is_default': False, 'display_order': 1},
    {'key': 'acquisition',  'label': 'Acquisition',  'icon': 'graduation-cap', 'color': '#2563eb', 'is_staff_visible': True,  'is_default': False, 'display_order': 2},
    {'key': 'mastered',     'label': 'Mastered',     'icon': 'trophy',        'color': '#7c3aed', 'is_staff_visible': True,  'is_default': False, 'display_order': 3},
    {'key': 'closed',       'label': 'Closed',       'icon': 'check-circle', 'color': '#059669', 'is_staff_visible': False, 'is_default': False, 'display_order': 4},
    {'key': 'hold',         'label': 'Hold',         'icon': 'hand',          'color': '#ea580c', 'is_staff_visible': False, 'is_default': False, 'display_order': 5},
    {'key': 'discontinued', 'label': 'Discontinued', 'icon': 'x-square',     'color': '#dc2626', 'is_staff_visible': False, 'is_default': False, 'display_order': 6},
]


def seed_statuses(apps, schema_editor):
    TargetStatus = apps.get_model('programs', 'TargetStatus')
    for row in SEED_STATUSES:
        TargetStatus.objects.get_or_create(key=row['key'], defaults=row)


def unseed_statuses(apps, schema_editor):
    TargetStatus = apps.get_model('programs', 'TargetStatus')
    TargetStatus.objects.filter(key__in=[r['key'] for r in SEED_STATUSES]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('programs', '0014_target_sub_items'),
    ]

    operations = [
        migrations.CreateModel(
            name='TargetStatus',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('key', models.SlugField(max_length=20)),
                ('label', models.CharField(max_length=50)),
                ('color', models.CharField(default='#6366f1', max_length=7)),
                ('icon', models.CharField(default='circle', max_length=30)),
                ('is_staff_visible', models.BooleanField(default=False, help_text='Shown to staff in the session recording view')),
                ('is_default', models.BooleanField(default=False, help_text='Starting status for newly created targets')),
                ('display_order', models.PositiveIntegerField(default=0)),
                ('created_by', models.ForeignKey(blank=True, db_constraint=False, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['display_order', 'label'],
                'unique_together': {('key',)},
            },
        ),
        migrations.AlterField(
            model_name='target',
            name='status',
            field=models.CharField(db_index=True, default='waiting', max_length=20),
        ),
        migrations.RunPython(seed_statuses, unseed_statuses),
    ]
