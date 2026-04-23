from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("telescope", "0002_add_indexes"),
    ]

    operations = [
        migrations.AlterField(
            model_name="telescopeentry",
            name="type",
            field=models.SmallIntegerField(
                choices=[
                    (1, "Request"),
                    (2, "Query"),
                    (3, "Exception"),
                    (4, "Model"),
                    (5, "Log"),
                    (6, "Cache"),
                    (7, "Redis"),
                    (8, "Mail"),
                    (9, "View"),
                    (10, "Event"),
                    (11, "Command"),
                    (12, "Dump"),
                    (13, "Client Request"),
                    (14, "Gate"),
                    (15, "Notification"),
                    (16, "Schedule"),
                    (17, "Batch"),
                    (18, "Transaction"),
                    (19, "Storage"),
                ],
                db_index=True,
            ),
        ),
    ]
