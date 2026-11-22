# Backward-compatible SEO schema: only ADDS nullable/blank/defaulted columns and one new table.
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('homepage', '0002_category_service'),
    ]

    operations = [
        migrations.AddField(
            model_name='category',
            name='meta_title',
            field=models.CharField(max_length=70, blank=True, help_text='Search result title. Aim for about 50-60 characters. Leave blank to use an automatic title.'),
        ),
        migrations.AddField(
            model_name='category',
            name='meta_description',
            field=models.CharField(max_length=320, blank=True, help_text='Search result snippet. Aim for about 120-155 characters. Leave blank to use an automatic description.'),
        ),
        migrations.AddField(
            model_name='category',
            name='focus_keyword',
            field=models.CharField(max_length=100, blank=True, help_text="The main search phrase this page targets, e.g. 'deep cleaning services in Islamabad'. Used for the SEO check only; it is not output on the page."),
        ),
        migrations.AddField(
            model_name='category',
            name='secondary_keywords',
            field=models.TextField(blank=True, help_text='Supporting phrases, one per line or comma-separated. Used for the SEO check only; it is not output on the page.'),
        ),
        migrations.AddField(
            model_name='category',
            name='canonical_url',
            field=models.URLField(max_length=300, blank=True, help_text="Leave blank in almost all cases (the page's own URL is used). Only set to point to another public page on this website; other hosts are rejected."),
        ),
        migrations.AddField(
            model_name='category',
            name='og_title',
            field=models.CharField(max_length=95, blank=True, verbose_name='Social title', help_text='Title for Facebook, WhatsApp, X/Twitter shares. Blank = use the SEO title.'),
        ),
        migrations.AddField(
            model_name='category',
            name='og_description',
            field=models.CharField(max_length=300, blank=True, verbose_name='Social description', help_text='Description for social shares. Blank = use the meta description.'),
        ),
        migrations.AddField(
            model_name='category',
            name='og_image',
            field=models.ImageField(upload_to='seo/', blank=True, null=True, verbose_name='Social image', help_text='Recommended 1200x630 px. Blank = the service image, or the site default image.'),
        ),
        migrations.AddField(
            model_name='category',
            name='robots_index',
            field=models.BooleanField(default=True, verbose_name='Allow search engines to index', help_text="Untick to add 'noindex' and remove the page from the sitemap."),
        ),
        migrations.AddField(
            model_name='category',
            name='robots_follow',
            field=models.BooleanField(default=True, verbose_name='Allow search engines to follow links', help_text="Untick to add 'nofollow'."),
        ),
        migrations.AddField(
            model_name='category',
            name='schema_enabled',
            field=models.BooleanField(default=True, verbose_name='Output structured data (JSON-LD)', help_text='Untick to remove JSON-LD from this page.'),
        ),
        migrations.AddField(
            model_name='service',
            name='meta_title',
            field=models.CharField(max_length=70, blank=True, help_text='Search result title. Aim for about 50-60 characters. Leave blank to use an automatic title.'),
        ),
        migrations.AddField(
            model_name='service',
            name='meta_description',
            field=models.CharField(max_length=320, blank=True, help_text='Search result snippet. Aim for about 120-155 characters. Leave blank to use an automatic description.'),
        ),
        migrations.AddField(
            model_name='service',
            name='focus_keyword',
            field=models.CharField(max_length=100, blank=True, help_text="The main search phrase this page targets, e.g. 'deep cleaning services in Islamabad'. Used for the SEO check only; it is not output on the page."),
        ),
        migrations.AddField(
            model_name='service',
            name='secondary_keywords',
            field=models.TextField(blank=True, help_text='Supporting phrases, one per line or comma-separated. Used for the SEO check only; it is not output on the page.'),
        ),
        migrations.AddField(
            model_name='service',
            name='canonical_url',
            field=models.URLField(max_length=300, blank=True, help_text="Leave blank in almost all cases (the page's own URL is used). Only set to point to another public page on this website; other hosts are rejected."),
        ),
        migrations.AddField(
            model_name='service',
            name='og_title',
            field=models.CharField(max_length=95, blank=True, verbose_name='Social title', help_text='Title for Facebook, WhatsApp, X/Twitter shares. Blank = use the SEO title.'),
        ),
        migrations.AddField(
            model_name='service',
            name='og_description',
            field=models.CharField(max_length=300, blank=True, verbose_name='Social description', help_text='Description for social shares. Blank = use the meta description.'),
        ),
        migrations.AddField(
            model_name='service',
            name='og_image',
            field=models.ImageField(upload_to='seo/', blank=True, null=True, verbose_name='Social image', help_text='Recommended 1200x630 px. Blank = the service image, or the site default image.'),
        ),
        migrations.AddField(
            model_name='service',
            name='robots_index',
            field=models.BooleanField(default=True, verbose_name='Allow search engines to index', help_text="Untick to add 'noindex' and remove the page from the sitemap."),
        ),
        migrations.AddField(
            model_name='service',
            name='robots_follow',
            field=models.BooleanField(default=True, verbose_name='Allow search engines to follow links', help_text="Untick to add 'nofollow'."),
        ),
        migrations.AddField(
            model_name='service',
            name='schema_enabled',
            field=models.BooleanField(default=True, verbose_name='Output structured data (JSON-LD)', help_text='Untick to remove JSON-LD from this page.'),
        ),
        migrations.CreateModel(
            name='StaticPageSEO',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('meta_title', models.CharField(max_length=70, blank=True, help_text='Search result title. Aim for about 50-60 characters. Leave blank to use an automatic title.')),
                ('meta_description', models.CharField(max_length=320, blank=True, help_text='Search result snippet. Aim for about 120-155 characters. Leave blank to use an automatic description.')),
                ('focus_keyword', models.CharField(max_length=100, blank=True, help_text="The main search phrase this page targets, e.g. 'deep cleaning services in Islamabad'. Used for the SEO check only; it is not output on the page.")),
                ('secondary_keywords', models.TextField(blank=True, help_text='Supporting phrases, one per line or comma-separated. Used for the SEO check only; it is not output on the page.')),
                ('canonical_url', models.URLField(max_length=300, blank=True, help_text="Leave blank in almost all cases (the page's own URL is used). Only set to point to another public page on this website; other hosts are rejected.")),
                ('og_title', models.CharField(max_length=95, blank=True, verbose_name='Social title', help_text='Title for Facebook, WhatsApp, X/Twitter shares. Blank = use the SEO title.')),
                ('og_description', models.CharField(max_length=300, blank=True, verbose_name='Social description', help_text='Description for social shares. Blank = use the meta description.')),
                ('og_image', models.ImageField(upload_to='seo/', blank=True, null=True, verbose_name='Social image', help_text='Recommended 1200x630 px. Blank = the service image, or the site default image.')),
                ('robots_index', models.BooleanField(default=True, verbose_name='Allow search engines to index', help_text="Untick to add 'noindex' and remove the page from the sitemap.")),
                ('robots_follow', models.BooleanField(default=True, verbose_name='Allow search engines to follow links', help_text="Untick to add 'nofollow'.")),
                ('schema_enabled', models.BooleanField(default=True, verbose_name='Output structured data (JSON-LD)', help_text='Untick to remove JSON-LD from this page.')),
                ('page_key', models.CharField(choices=[('home', 'Homepage'), ('about', 'About'), ('review', 'Reviews'), ('complaint', 'Customer Support (complaint form)'), ('employe', 'Join Our Team (employee registration)')], help_text='Which page these settings apply to.', max_length=30, unique=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'Static page SEO',
                'verbose_name_plural': 'Static page SEO',
                'ordering': ['page_key'],
            },
        ),
    ]
