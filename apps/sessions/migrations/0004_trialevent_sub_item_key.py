from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dcm_sessions', '0003_rename_tpms_fields_external'),
    ]

    operations = [
        migrations.AddField(
            model_name='trialevent',
            name='sub_item_key',
            field=models.CharField(blank=True, default='', max_length=100),
        ),
        migrations.AlterUniqueTogether(
            name='trialevent',
            unique_together={('session_run', 'target_id', 'trial_number', 'sub_item_key')},
        ),
    ]
