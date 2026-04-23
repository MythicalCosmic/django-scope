from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("telescope", "0001_initial"),
    ]

    operations = [
        # Composite index on entry+tag for faster tag-based filtering
        migrations.AddIndex(
            model_name="telescopeentrytag",
            index=models.Index(fields=["entry", "tag"], name="telescope_t_entry_i_idx"),
        ),
        # Index on family_hash for N+1 pattern grouping queries
        migrations.AlterField(
            model_name="telescopeentry",
            name="family_hash",
            field=models.CharField(blank=True, db_index=True, max_length=64, null=True),
        ),
    ]
