from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('programs', '0013_rename_tpms_fields_external'),
    ]

    operations = [
        migrations.AddField(
            model_name='target',
            name='sub_items',
            field=models.JSONField(blank=True, default=list),
        ),
    ]
