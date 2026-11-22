from django.db import models
from django.urls import reverse
from django.utils.text import slugify
from django.core.exceptions import ValidationError
# Create your models here.


class SEOFields(models.Model):
    """Reusable SEO fields (abstract: no table of its own).

    Used by Category, Service and StaticPageSEO so every public page type is
    managed the same way. Twitter/X cards reuse the social (Open Graph) fields.
    """

    meta_title = models.CharField(
        max_length=70,
        blank=True,
        help_text='Search result title. Aim for about 50-60 characters. Leave blank to use an automatic title.',
    )

    meta_description = models.CharField(
        max_length=320,
        blank=True,
        help_text='Search result snippet. Aim for about 120-155 characters. Leave blank to use an automatic description.',
    )

    focus_keyword = models.CharField(
        max_length=100,
        blank=True,
        help_text="The main search phrase this page targets, e.g. 'deep cleaning services in Islamabad'. Used for the SEO check only; it is not output on the page.",
    )

    secondary_keywords = models.TextField(
        blank=True,
        help_text='Supporting phrases, one per line or comma-separated. Used for the SEO check only; it is not output on the page.',
    )

    canonical_url = models.URLField(
        max_length=300,
        blank=True,
        help_text="Leave blank in almost all cases (the page's own URL is used). Only set to point to another public page on this website; other hosts are rejected.",
    )

    og_title = models.CharField(
        max_length=95,
        blank=True,
        verbose_name='Social title',
        help_text='Title for Facebook, WhatsApp, X/Twitter shares. Blank = use the SEO title.',
    )

    og_description = models.CharField(
        max_length=300,
        blank=True,
        verbose_name='Social description',
        help_text='Description for social shares. Blank = use the meta description.',
    )

    og_image = models.ImageField(
        upload_to='seo/',
        blank=True,
        null=True,
        verbose_name='Social image',
        help_text='Recommended 1200x630 px. Blank = the service image, or the site default image.',
    )

    robots_index = models.BooleanField(
        default=True,
        verbose_name='Allow search engines to index',
        help_text="Untick to add 'noindex' and remove the page from the sitemap.",
    )

    robots_follow = models.BooleanField(
        default=True,
        verbose_name='Allow search engines to follow links',
        help_text="Untick to add 'nofollow'.",
    )

    schema_enabled = models.BooleanField(
        default=True,
        verbose_name='Output structured data (JSON-LD)',
        help_text='Untick to remove JSON-LD from this page.',
    )

    class Meta:
        abstract = True

    def secondary_keyword_list(self):
        raw = (self.secondary_keywords or "").replace("\n", ",")
        return [k.strip() for k in raw.split(",") if k.strip()]

    def clean(self):
        super().clean()
        if self.canonical_url:
            from .seo import validate_canonical
            problem = validate_canonical(self.canonical_url)
            if problem:
                raise ValidationError({"canonical_url": problem})




class Booking(models.Model):
    full_name = models.CharField(max_length=150)
    phone_number = models.CharField(max_length=20)
    service_address = models.CharField(max_length=255)
    cleaning_service = models.CharField(max_length=100)
    preferred_date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.full_name
    




class Category(SEOFields):
    category_name = models.CharField(
        max_length=100,
        unique=True
    )

    slug = models.SlugField(
        max_length=120,
        unique=True,
        blank=True
    )

    class Meta:
        verbose_name = "Category"
        verbose_name_plural = "Categories"
        ordering = ["category_name"]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.category_name)

        super().save(*args, **kwargs)

    def __str__(self):
        return self.category_name

    def get_absolute_url(self):
        return reverse("explor", kwargs={"slug": self.slug})


class Service(SEOFields):

    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name="services"
    )

    image1 = models.ImageField(
        upload_to="services/",
        blank=True,
        null=True
    )

    image2 = models.ImageField(
        upload_to="services/",
        blank=True,
        null=True
    )

    title_h1 = models.CharField(max_length=100)

    slug = models.SlugField(
        max_length=150,
        unique=True,
        blank=True
    )

    paragraph_1 = models.TextField()

    # Service Content Sections

    h1_1 = models.CharField(max_length=150)
    p1_1 = models.TextField()

    h2_2 = models.CharField(max_length=150)
    p2_2 = models.TextField()

    h3_3 = models.CharField(max_length=150)
    p3_3 = models.TextField()

    h4_4 = models.CharField(max_length=150)
    p4_4 = models.TextField()

    # Frequently Asked Questions

    q1_1 = models.CharField(max_length=200)
    a1_1 = models.TextField()

    q2_2 = models.CharField(max_length=200)
    a2_2 = models.TextField()

    q3_3 = models.CharField(max_length=200)
    a3_3 = models.TextField()

    q4_4 = models.CharField(max_length=200)
    a4_4 = models.TextField()

    # Timestamps

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        verbose_name = "Service"
        verbose_name_plural = "Services"
        ordering = ["-created_at"]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title_h1)

        super().save(*args, **kwargs)

    def __str__(self):
        return self.title_h1

    def get_absolute_url(self):
        # Services are displayed on their category page (there is no separate service URL).
        return reverse("explor", kwargs={"slug": self.category.slug})


class StaticPageSEO(SEOFields):
    """SEO settings for fixed pages (home, about, ...). One row per page_key."""

    PAGE_CHOICES = [
        ("home", "Homepage"),
        ("about", "About"),
        ("review", "Reviews"),
        ("complaint", "Customer Support (complaint form)"),
        ("employe", "Join Our Team (employee registration)"),
    ]

    page_key = models.CharField(
        max_length=30,
        unique=True,
        choices=PAGE_CHOICES,
        help_text="Which page these settings apply to.",
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Static page SEO"
        verbose_name_plural = "Static page SEO"
        ordering = ["page_key"]

    def __str__(self):
        return self.get_page_key_display()
