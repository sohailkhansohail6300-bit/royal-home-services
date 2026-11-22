"""XML sitemap: public, indexable, canonical pages only.

Excluded by construction: /admin/, /adminlogin/, /dashboard/, pages set to noindex,
pages whose canonical points elsewhere, and categories with no service (they 404).
Services have no URL of their own - they are shown on their category page - so the
category URL is the single sitemap entry (no duplicates).
"""
from urllib.parse import urlsplit

from django.conf import settings
from django.contrib.sitemaps import Sitemap
from django.db.models import Max
from django.urls import reverse

from admin2.models import Review

from .models import Category, Service, StaticPageSEO
from .seo import (DEFAULT_PAGES, STATIC_URL_NAMES, category_canonical_is_self,
                  category_is_indexable, pick_service)


class _BaseSitemap(Sitemap):
    """Uses the configured production domain (SITE_URL) and https."""

    def get_domain(self, site=None):
        configured = getattr(settings, "SITE_URL", "")
        if configured:
            return urlsplit(configured).netloc
        return super().get_domain(site)

    def get_protocol(self, protocol=None):
        configured = getattr(settings, "SITE_URL", "")
        if configured:
            return urlsplit(configured).scheme
        return super().get_protocol(protocol)


class StaticPagesSitemap(_BaseSitemap):
    def items(self):
        rows = {r.page_key: r for r in StaticPageSEO.objects.all()}
        keys = []
        for key in STATIC_URL_NAMES:
            row = rows.get(key)
            indexable = row.robots_index if row else DEFAULT_PAGES[key]["index"]
            self_canonical = not (row and row.canonical_url and
                                  not _same_path(row.canonical_url, reverse(key)))
            if indexable and self_canonical:
                keys.append(key)
        return keys

    def location(self, key):
        return reverse(key)

    def lastmod(self, key):
        # Only dates that reflect real content changes; None => <lastmod> omitted.
        if key == "home":
            return Service.objects.aggregate(m=Max("updated_at"))["m"]
        if key == "review":
            return Review.objects.filter(is_approved=True).aggregate(m=Max("created_at"))["m"]
        return None


class CategorySitemap(_BaseSitemap):
    def items(self):
        entries = []
        for category in Category.objects.all():
            service = pick_service(category)
            if (service is not None and category_is_indexable(category, service)
                    and category_canonical_is_self(category, service)):
                entries.append((category, service))
        return entries

    def location(self, entry):
        return entry[0].get_absolute_url()

    def lastmod(self, entry):
        return entry[1].updated_at


def _same_path(url, path):
    return (urlsplit(url).path or "/").rstrip("/") == path.rstrip("/")


sitemaps = {"pages": StaticPagesSitemap, "categories": CategorySitemap}
