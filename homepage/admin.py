from django.contrib import admin
from django.utils.html import format_html, format_html_join
from django.utils.safestring import mark_safe

from .models import Booking, Service, Category, StaticPageSEO
from .seo import DEFAULT_PAGES, clean_text, site_name
# Register your models here.

SEO_FIELDSETS = (
    ("SEO - Search results", {
        "fields": ("meta_title", "meta_description", "focus_keyword", "secondary_keywords", "seo_check"),
        "description": "Blank title/description = automatic values are used. Twitter/X cards reuse the social fields below.",
    }),
    ("SEO - Social sharing (Facebook, WhatsApp, X/Twitter)", {
        "classes": ("collapse",),
        "fields": ("og_title", "og_description", "og_image"),
    }),
    ("SEO - Indexing & structured data", {
        "classes": ("collapse",),
        "fields": ("robots_index", "robots_follow", "schema_enabled", "canonical_url"),
    }),
)

TITLE_MAX, DESC_MIN, DESC_MAX = 65, 70, 160


def _length_row(label, text, low, high):
    n = len(text)
    ok = low <= n <= high
    colour = "#15803d" if ok else "#b45309"
    return format_html('<div><b>{}</b>: <span style="color:{}">{} characters</span> (target {}-{})</div>',
                       label, colour, n, low, high)


class SEOAdminMixin:
    """Adds a read-only 'SEO check' panel. Advisory only - it never blocks saving."""

    def _effective(self, obj):
        raise NotImplementedError

    @admin.display(description="SEO check")
    def seo_check(self, obj):
        if obj is None or obj.pk is None:
            return "Save the record first to see the SEO check."
        title, description = self._effective(obj)
        rows = [_length_row("Title", title, 20, TITLE_MAX), _length_row("Description", description, DESC_MIN, DESC_MAX)]
        keyword = (obj.focus_keyword or "").strip().lower()
        if keyword:
            rows.append(format_html("<div><b>Focus keyword</b> in title: {} / in description: {}</div>",
                                    "yes" if keyword in title.lower() else "NO",
                                    "yes" if keyword in description.lower() else "NO"))
        else:
            rows.append(mark_safe("<div><b>Focus keyword</b>: not set</div>"))
        rows.append(format_html("<div><b>Indexing</b>: {}</div>",
                                "indexable" if obj.robots_index else "NOINDEX - hidden from search and sitemap"))
        preview = format_html('<div style="margin-top:6px;max-width:600px;padding:8px;border:1px solid #ddd;border-radius:6px">'
                              '<div style="color:#1a0dab;font-size:16px">{}</div>'
                              '<div style="color:#4d5156;font-size:13px">{}</div></div>', title, description)
        return format_html_join("", "{}", ((r,) for r in rows + [preview]))

class BookingAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'phone_number', 'service_address', 'cleaning_service', 'preferred_date', 'created_at')
    search_fields = ('full_name', 'phone_number', 'service_address', 'cleaning_service')
    list_filter = ('cleaning_service', 'preferred_date')
admin.site.register(Booking, BookingAdmin)





@admin.register(Category)
class CategoryAdmin(SEOAdminMixin, admin.ModelAdmin):

    list_display = (
        "category_name",
        "slug",
        "robots_index",
        "focus_keyword",
    )

    readonly_fields = ("seo_check",)

    fieldsets = (
        ("Category", {"fields": ("category_name", "slug")}),
    ) + SEO_FIELDSETS

    def _effective(self, obj):
        service = obj.services.order_by("-created_at").first()
        title = clean_text(obj.meta_title or (service and service.meta_title) or "%s | %s" % (obj.category_name, site_name()), 120)
        description = clean_text(obj.meta_description or (service and service.meta_description)
                                 or (service and service.paragraph_1) or "", 320)
        return title, description

    search_fields = (
        "category_name",
    )

    prepopulated_fields = {
        "slug": ("category_name",)
    }

    ordering = ("category_name",)


@admin.register(Service)
class ServiceAdmin(SEOAdminMixin, admin.ModelAdmin):

    list_display = (
        "title_h1",
        "category",
        "robots_index",
        "created_at",
        "updated_at",
    )

    def _effective(self, obj):
        title = clean_text(obj.meta_title or "%s | %s" % (obj.category.category_name, site_name()), 120)
        description = clean_text(obj.meta_description or obj.paragraph_1, 320)
        return title, description

    list_filter = (
        "category",
        "created_at",
    )

    search_fields = (
        "title_h1",
        "paragraph_1",
        "category__category_name",
    )

    prepopulated_fields = {
        "slug": ("title_h1",)
    }

    readonly_fields = (
        "created_at",
        "updated_at",
        "seo_check",
    )

    ordering = ("-created_at",)

    fieldsets = (

        ("Basic Information", {
            "fields": (
                "category",
                "title_h1",
                "slug",
                "paragraph_1",
            )
        }),

        ("Service Images", {
            "fields": (
                "image1",
                "image2",
            )
        }),

        ("Content Section 1", {
            "fields": (
                "h1_1",
                "p1_1",
            )
        }),

        ("Content Section 2", {
            "fields": (
                "h2_2",
                "p2_2",
            )
        }),

        ("Content Section 3", {
            "fields": (
                "h3_3",
                "p3_3",
            )
        }),

        ("Content Section 4", {
            "fields": (
                "h4_4",
                "p4_4",
            )
        }),

        ("FAQ Section 1", {
            "fields": (
                "q1_1",
                "a1_1",
            )
        }),

        ("FAQ Section 2", {
            "fields": (
                "q2_2",
                "a2_2",
            )
        }),

        ("FAQ Section 3", {
            "fields": (
                "q3_3",
                "a3_3",
            )
        }),

        ("FAQ Section 4", {
            "fields": (
                "q4_4",
                "a4_4",
            )
        }),

    ) + SEO_FIELDSETS + (

        ("Timestamps", {
            "fields": (
                "created_at",
                "updated_at",
            )
        }),

    )


@admin.register(StaticPageSEO)
class StaticPageSEOAdmin(SEOAdminMixin, admin.ModelAdmin):
    """One row per fixed page (home, about, ...). Rows are created by migration 0004."""

    list_display = ("page_key", "meta_title", "robots_index", "schema_enabled", "updated_at")
    list_filter = ("robots_index",)
    readonly_fields = ("seo_check", "updated_at")
    fieldsets = (
        ("Page", {"fields": ("page_key", "updated_at")}),
    ) + SEO_FIELDSETS

    def _effective(self, obj):
        default = DEFAULT_PAGES.get(obj.page_key, {})
        return (clean_text(obj.meta_title or default.get("title", ""), 120),
                clean_text(obj.meta_description or default.get("description", ""), 320))

    def get_readonly_fields(self, request, obj=None):
        fields = super().get_readonly_fields(request, obj)
        return fields + ("page_key",) if obj else fields

    def has_add_permission(self, request):
        return StaticPageSEO.objects.count() < len(StaticPageSEO.PAGE_CHOICES)

    def has_delete_permission(self, request, obj=None):
        return False
