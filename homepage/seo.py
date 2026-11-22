"""Central SEO logic: head metadata, canonical handling and JSON-LD.

Everything the <head> needs is produced here as a plain dict (``seo``) and rendered by
``templates/seo/head.html``. Nothing in this module touches page body content.

Resolution order for every value is:
    admin-entered value  ->  sensible automatic fallback  ->  omitted (never output empty tags)
"""
import html
import json
import re
from urllib.parse import urlsplit

from django.conf import settings
from django.db.utils import DatabaseError
from django.templatetags.static import static
from django.urls import Resolver404, resolve
from django.utils.html import strip_tags
from django.utils.safestring import mark_safe
from django.utils.text import Truncator

# url_name values of public pages that may carry a canonical URL.
STATIC_URL_NAMES = ("home", "about", "review", "complaint", "employe")  # url_name == StaticPageSEO.page_key
PUBLIC_URL_NAMES = frozenset(STATIC_URL_NAMES) | {"explor"}

# Built-in defaults for static pages. Used whenever the admin has left a field blank.
# Wording only claims what the visible page content already says.
DEFAULT_PAGES = {
    "home": {
        "name": "Home",
        "title": "Cleaning Services in Rawalpindi & Islamabad | Royal Home Services",
        "description": (
            "Royal Home Services offers home cleaning in Rawalpindi and Islamabad, from a routine "
            "refresh to a full deep clean. Book online or message us on WhatsApp."
        ),
        "index": True,
        "type": "WebPage",
    },
    "about": {
        "name": "About",
        "title": "About Us | Professional Cleaners | Royal Home Services",
        "description": (
            "Meet the team behind Royal Home Services: professional, thoughtful home cleaning "
            "built on consistency and care for homes in Rawalpindi and Islamabad."
        ),
        "index": True,
        "type": "AboutPage",
    },
    "review": {
        "name": "Reviews",
        "title": "Customer Reviews | Royal Home Services",
        "description": (
            "Read approved feedback from Royal Home Services customers, and share your own "
            "experience of our home cleaning service."
        ),
        "index": True,
        "type": "WebPage",
    },
    "complaint": {
        "name": "Customer Support",
        "title": "Customer Support & Feedback | Royal Home Services",
        "description": (
            "If something didn't go as expected with your cleaning service, tell Royal Home "
            "Services and we will work to make it right."
        ),
        "index": False,
        "type": "WebPage",
    },
    "employe": {
        "name": "Join Our Team",
        "title": "Join Our Team | Royal Home Services",
        "description": (
            "Register your interest in working with Royal Home Services as a cleaning "
            "professional."
        ),
        "index": False,
        "type": "WebPage",
    },
}


# --------------------------------------------------------------------------- helpers
def business():
    return getattr(settings, "SEO_BUSINESS", {})


def site_name():
    return business().get("name", "Royal Home Services")


def site_root(request=None):
    """Preferred origin without trailing slash. Prefers settings.SITE_URL (the real
    production domain); falls back to the current request so local development works."""
    configured = getattr(settings, "SITE_URL", "")
    if configured:
        return configured.rstrip("/")
    if request is not None:
        return request.build_absolute_uri("/").rstrip("/")
    return ""


def absolute_url(request, url):
    if not url:
        return ""
    if url.startswith(("http://", "https://")):
        return url
    if url.startswith("//"):
        return "https:" + url
    return site_root(request) + (url if url.startswith("/") else "/" + url)


def clean_text(value, limit):
    """Strip tags/entities, collapse whitespace, truncate on a word boundary."""
    text = html.unescape(strip_tags(value or ""))
    text = re.sub(r"\s+", " ", text).strip()
    return Truncator(text).chars(limit) if text else ""


def first(*values):
    for value in values:
        if value:
            return value
    return ""


def file_url(field_file):
    """URL of an ImageField value, or '' if empty/unavailable."""
    try:
        return field_file.url if field_file and field_file.name else ""
    except ValueError:
        return ""


def robots_value(index, follow):
    parts = ["index" if index else "noindex", "follow" if follow else "nofollow"]
    if index:
        parts.append("max-image-preview:large")
    return ", ".join(parts)


def dump_jsonld(data):
    """Serialise with json.dumps, then neutralise characters that could break out of a
    <script> element. Output stays valid JSON."""
    text = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    for char, escaped in (("<", "\\u003c"), (">", "\\u003e"), ("&", "\\u0026"),
                          (" ", "\\u2028"), (" ", "\\u2029")):
        text = text.replace(char, escaped)
    return mark_safe(text)


# --------------------------------------------------------------------------- canonical
def validate_canonical(url, expected_host=None):
    """Return an error message, or None if ``url`` is an acceptable canonical override.

    Rules: absolute http(s) URL, no query/fragment, same host as the website, and the
    path must resolve to a real public page of this site (so a typo or a link to an
    unrelated/private page can never become a canonical)."""
    parts = urlsplit((url or "").strip())
    if parts.scheme not in ("http", "https") or not parts.netloc:
        return "Enter a full URL starting with https://"
    if parts.query or parts.fragment:
        return "A canonical URL must not contain a query string or #fragment."
    configured = getattr(settings, "SITE_URL", "")
    host = expected_host or (urlsplit(configured).netloc if configured else "")
    if host:
        if parts.netloc.lower() != host.lower():
            return "The canonical URL must be on this website (%s)." % host
        if configured and urlsplit(configured).scheme == "https" and parts.scheme != "https":
            return "Use https:// for the canonical URL."
        try:
            match = resolve(parts.path or "/")
        except Resolver404:
            return "That path does not match any page on this website."
        if match.url_name not in PUBLIC_URL_NAMES:
            return "The canonical URL must point to a public page."
    return None


def safe_canonical(request, override):
    """Use an admin override only if it passes validation; otherwise ignore it."""
    if override:
        host = urlsplit(site_root(request)).netloc
        if validate_canonical(override, expected_host=host) is None:
            return override
    return ""


# --------------------------------------------------------------------------- JSON-LD
def _business_node(request, root):
    biz = business()
    node = {
        "@type": biz.get("schema_type", "LocalBusiness"),
        "@id": root + "/#business",
        "name": site_name(),
        "url": root + "/",
    }
    if biz.get("telephone"):
        node["telephone"] = biz["telephone"]
    if biz.get("email"):
        node["email"] = biz["email"]
    if biz.get("logo_static"):
        logo = absolute_url(request, static(biz["logo_static"]))
        node["logo"] = {"@type": "ImageObject", "url": logo}
        node["image"] = logo
    if biz.get("same_as"):
        node["sameAs"] = list(biz["same_as"])
    if biz.get("service_areas"):
        country = biz.get("area_country")
        areas = []
        for name in biz["service_areas"]:
            area = {"@type": "City", "name": name}
            if country:
                area["containedInPlace"] = {"@type": "Country", "name": country}
            areas.append(area)
        node["areaServed"] = areas
    # Only emitted once real, verified values are added to settings.SEO_BUSINESS.
    if biz.get("address"):
        node["address"] = dict(biz["address"], **{"@type": "PostalAddress"})
    if biz.get("geo"):
        lat, lon = biz["geo"]
        node["geo"] = {"@type": "GeoCoordinates", "latitude": lat, "longitude": lon}
    if biz.get("opening_hours"):
        node["openingHours"] = list(biz["opening_hours"])
    return node


def _graph(request, *, root, canonical, title, description, page_type, trail, extra=None):
    business_id = {"@id": root + "/#business"}
    website_id = {"@id": root + "/#website"}
    nodes = [
        _business_node(request, root),
        {
            "@type": "WebSite",
            "@id": root + "/#website",
            "url": root + "/",
            "name": site_name(),
            "inLanguage": "en",
            "publisher": business_id,
        },
    ]
    page = {
        "@type": page_type,
        "@id": canonical + "#webpage",
        "url": canonical,
        "name": title,
        "inLanguage": "en",
        "isPartOf": website_id,
        "about": business_id,
    }
    if description:
        page["description"] = description
    nodes.append(page)
    if trail:  # trail = [(name, absolute_url), ...] excluding Home
        items = [{"@type": "ListItem", "position": 1, "name": "Home", "item": root + "/"}]
        for position, (name, url) in enumerate(trail, start=2):
            items.append({"@type": "ListItem", "position": position, "name": name, "item": url})
        nodes.append({"@type": "BreadcrumbList", "@id": canonical + "#breadcrumb", "itemListElement": items})
        page["breadcrumb"] = {"@id": canonical + "#breadcrumb"}
    nodes.extend(extra or [])
    return {"@context": "https://schema.org", "@graph": nodes}


def _service_nodes(request, root, canonical, category, service):
    """Service + FAQPage nodes. Both mirror content that is visible on the category page."""
    if service is None:
        return []
    business_id = {"@id": root + "/#business"}
    service_node = {
        "@type": "Service",
        "@id": canonical + "#service",
        "name": service.title_h1,
        "serviceType": category.category_name,
        "url": canonical,
        "provider": business_id,
    }
    description = clean_text(service.paragraph_1, 300)
    if description:
        service_node["description"] = description
    areas = business().get("service_areas")
    if areas:
        service_node["areaServed"] = [{"@type": "City", "name": a} for a in areas]
    images = [absolute_url(request, u) for u in (file_url(service.image1), file_url(service.image2)) if u]
    if images:
        service_node["image"] = images
    nodes = [service_node]

    faq = []
    for q, a in ((service.q1_1, service.a1_1), (service.q2_2, service.a2_2),
                 (service.q3_3, service.a3_3), (service.q4_4, service.a4_4)):
        question, answer = clean_text(q, 300), clean_text(a, 1500)
        if question and answer:
            faq.append({"@type": "Question", "name": question,
                        "acceptedAnswer": {"@type": "Answer", "text": answer}})
    if faq:
        nodes.append({"@type": "FAQPage", "@id": canonical + "#faq", "url": canonical, "mainEntity": faq})
    return nodes


# --------------------------------------------------------------------------- composition
def _compose(request, *, title, description, index, follow, schema_enabled, canonical_override,
             og_title, og_description, og_image, page_type, trail=None, extra=None):
    root = site_root(request)
    canonical = safe_canonical(request, canonical_override) or root + request.path
    og_image_abs = absolute_url(request, og_image or static(getattr(settings, "SEO_DEFAULT_OG_IMAGE", "images/home.jpeg")))
    og_title = og_title or title
    og_description = og_description or description

    seo = {
        "title": title,
        "description": description,
        "robots": robots_value(index, follow),
        "indexable": bool(index),
        "canonical": canonical,
        "site_name": site_name(),
        "og_type": "website",
        "og_url": canonical,
        "og_title": og_title,
        "og_description": og_description,
        "og_image": og_image_abs,
        "twitter_card": "summary_large_image",
        "twitter_title": og_title,
        "twitter_description": og_description,
        "twitter_image": og_image_abs,
        "jsonld": "",
    }
    if schema_enabled and index:
        seo["jsonld"] = dump_jsonld(_graph(
            request, root=root, canonical=canonical, title=title, description=description,
            page_type=page_type, trail=trail, extra=extra(canonical) if extra else None,
        ))
    return seo


def get_static_row(page_key):
    from .models import StaticPageSEO
    try:
        return StaticPageSEO.objects.filter(page_key=page_key).first()
    except DatabaseError:  # e.g. migrations not applied yet: serve defaults instead of a 500
        return None


def static_page_seo(request, page_key):
    default = DEFAULT_PAGES[page_key]
    row = get_static_row(page_key)
    title = clean_text(first(row and row.meta_title, default["title"]), 120)
    description = clean_text(first(row and row.meta_description, default["description"]), 320)
    trail = None
    if page_key != "home":
        trail = [(default["name"], site_root(request) + request.path)]
    return _compose(
        request,
        title=title,
        description=description,
        index=row.robots_index if row else default["index"],
        follow=row.robots_follow if row else True,
        schema_enabled=row.schema_enabled if row else True,
        canonical_override=row.canonical_url if row else "",
        og_title=clean_text(row.og_title, 120) if row else "",
        og_description=clean_text(row.og_description, 320) if row else "",
        og_image=file_url(row.og_image) if row else "",
        page_type=default["type"],
        trail=trail,
    )


AUTO_TITLE_MAX = 65          # automatic titles longer than this drop the area suffix
AUTO_DESCRIPTION_MIN = 50    # a service intro shorter than this is not a usable snippet


def service_areas_text():
    """'Rawalpindi & Islamabad' - from settings.SEO_BUSINESS['service_areas'] (never invented)."""
    areas = [a for a in (business().get("service_areas") or []) if a]
    return " & ".join(areas)


def auto_category_title(name):
    """Automatic title when the admin left it blank. Adds the service areas only when the
    result stays within a normal title length; admin-entered titles are never touched."""
    areas = service_areas_text()
    if areas:
        local = "%s in %s | %s" % (name, areas, site_name())
        if len(local) <= AUTO_TITLE_MAX:
            return local
    return "%s | %s" % (name, site_name())


def auto_category_description(name, intro):
    """Automatic description: the service intro if it is long enough to be a real snippet,
    otherwise a short factual sentence (the site's existing calls to action)."""
    text = clean_text(intro, 155)
    if len(text) >= AUTO_DESCRIPTION_MIN:
        return text
    areas = service_areas_text()
    where = " in %s" % areas if areas else ""
    return clean_text("%s%s from %s. Book online or message us on WhatsApp." % (name, where, site_name()), 155)



def pick_service(category):
    """The service shown on a category page (newest first, same as Service.Meta.ordering)."""
    return category.services.order_by("-created_at").first()


def category_page_seo(request, category, service):
    """Category page SEO. Category settings win; the displayed service's settings are the
    fallback, then automatic values built from the visible content."""
    s = service
    name = category.category_name
    title = clean_text(first(category.meta_title, s and s.meta_title, auto_category_title(name)), 120)
    description = (
        clean_text(first(category.meta_description, s and s.meta_description), 320)
        or auto_category_description(name, s.paragraph_1 if s else "")
    )
    own = site_root(request) + request.path
    return _compose(
        request,
        title=title,
        description=description,
        index=category.robots_index and (s.robots_index if s else True),
        follow=category.robots_follow and (s.robots_follow if s else True),
        schema_enabled=category.schema_enabled and (s.schema_enabled if s else True),
        canonical_override=first(category.canonical_url, s and s.canonical_url),
        og_title=clean_text(first(category.og_title, s and s.og_title), 120),
        og_description=clean_text(first(category.og_description, s and s.og_description), 320),
        og_image=first(file_url(category.og_image), s and file_url(s.og_image),
                       s and file_url(s.image1), s and file_url(s.image2)),
        page_type="WebPage",
        trail=[(name, own)],
        extra=lambda canonical: _service_nodes(request, site_root(request), canonical, category, s),
    )


def category_is_indexable(category, service):
    return bool(category.robots_index and (service.robots_index if service else True))


def category_canonical_is_self(category, service):
    """False when a validated canonical override points at a different page (so the page
    must stay out of the sitemap, which lists canonical URLs only)."""
    override = first(category.canonical_url, service and service.canonical_url)
    if not override or validate_canonical(override) is not None:
        return True
    own = category.get_absolute_url()
    return (urlsplit(override).path or "/").rstrip("/") == own.rstrip("/")
