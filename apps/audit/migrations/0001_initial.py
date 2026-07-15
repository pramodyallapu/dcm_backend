from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('tenants', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='AuditLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('actor_id', models.IntegerField(db_index=True)),
                ('actor_email', models.CharField(max_length=254)),
                ('actor_role', models.CharField(max_length=20)),
                ('action', models.CharField(choices=[('create', 'Create'), ('update', 'Update'), ('delete', 'Delete')], db_index=True, max_length=10)),
                ('model', models.CharField(db_index=True, max_length=100)),
                ('object_id', models.CharField(db_index=True, max_length=40)),
                ('object_repr', models.CharField(max_length=200)),
                ('changes', models.JSONField(default=dict)),
                ('timestamp', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('ip_address', models.GenericIPAddressField(blank=True, null=True)),
                ('request_id', models.CharField(blank=True, max_length=36)),
                ('organization', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='tenants.organization')),
            ],
            options={
                'ordering': ['-timestamp'],
                'app_label': 'audit',
            },
        ),
    ]
