from django.http import HttpResponse
from django.views.decorators.http import require_GET

from .seo import site_root

DISALLOWED_PATHS = ["/admin/", "/adminlogin/", "/dashboard/"]


@require_GET
def robots_txt(request):
    """robots.txt - a crawling hint, NOT access control. Private pages must be protected
    by authentication. /media/ and /static/ stay crawlable so images, CSS and JS render."""
    lines = ["User-agent: *", "Allow: /"]
    lines += ["Disallow: %s" % path for path in DISALLOWED_PATHS]
    lines += ["", "Sitemap: %s/sitemap.xml" % site_root(request), ""]
    return HttpResponse("\n".join(lines), content_type="text/plain; charset=utf-8")
