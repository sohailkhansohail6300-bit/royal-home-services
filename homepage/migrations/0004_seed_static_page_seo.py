# Data migration: creates one editable SEO row per static page so every page is
# visible in Django Admin. Text fields are left blank on purpose (blank = use the
# built-in defaults in homepage/seo.py). Only the indexing choice is seeded:
# the complaint form and the employee registration form are not search landing
# pages, so they start as noindex. Re-tick "Allow search engines to index" in the
# admin to change that. Idempotent and reversible (reverse is a no-op).
from django.db import migrations

NOINDEX_BY_DEFAULT = {"complaint", "employe"}
PAGE_KEYS = ["home", "about", "review", "complaint", "employe"]


def seed(apps, schema_editor):
    StaticPageSEO = apps.get_model("homepage", "StaticPageSEO")
    for key in PAGE_KEYS:
        StaticPageSEO.objects.get_or_create(
            page_key=key,
            defaults={"robots_index": key not in NOINDEX_BY_DEFAULT},
        )


class Migration(migrations.Migration):

    dependencies = [
        ("homepage", "0003_seo_fields"),
    ]

    operations = [
        migrations.RunPython(seed, migrations.RunPython.noop),
    ]
