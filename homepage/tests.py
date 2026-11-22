import json
import re

from django.core.exceptions import ValidationError
from django.test import TestCase, override_settings

from .models import Category, Service, StaticPageSEO
from .seo import validate_canonical

SITE = "https://www.example.test"


def make_service(category, title="Deep Cleaning", **extra):
    data = dict(
        category=category, title_h1=title, paragraph_1="A thorough deep clean of your home.",
        h1_1="h1", p1_1="p1", h2_2="h2", p2_2="p2", h3_3="h3", p3_3="p3", h4_4="h4", p4_4="p4",
        q1_1="What is included?", a1_1="Kitchen, bathrooms and living areas.",
        q2_2="Do you bring supplies?", a2_2="Yes.", q3_3="Q3", a3_3="A3", q4_4="Q4", a4_4="A4",
    )
    data.update(extra)
    return Service.objects.create(**data)


def jsonld(response):
    blocks = re.findall(r'<script type="application/ld\+json">(.*?)</script>', response.content.decode(), re.S)
    return [json.loads(b) for b in blocks]


@override_settings(SITE_URL=SITE, ALLOWED_HOSTS=["testserver", "www.example.test"])
class SeoTests(TestCase):
    def setUp(self):
        self.category = Category.objects.create(category_name="Deep Cleaning")
        self.service = make_service(self.category)

    # --- migrations / data ---------------------------------------------------
    def test_static_rows_seeded_with_expected_indexing(self):
        rows = {r.page_key: r.robots_index for r in StaticPageSEO.objects.all()}
        self.assertEqual(set(rows), {"home", "about", "review", "complaint", "employe"})
        self.assertTrue(rows["home"])
        self.assertFalse(rows["complaint"])

    # --- head tags -----------------------------------------------------------
    def test_home_head_has_single_title_canonical_and_robots(self):
        html = self.client.get("/").content.decode()
        self.assertEqual(html.count("<title>"), 1)
        self.assertEqual(html.count('rel="canonical"'), 1)
        self.assertEqual(html.count('name="robots"'), 1)
        self.assertIn('<link rel="canonical" href="%s/" />' % SITE, html)
        self.assertIn('content="index, follow', html)
        self.assertEqual(html.count('name="description"'), 1)

    def test_complaint_page_is_noindex(self):
        html = self.client.get("/complaint/").content.decode()
        self.assertIn('content="noindex, follow"', html)
        self.assertNotIn("application/ld+json", html)

    def test_titles_are_unique_per_page(self):
        titles = set()
        for url in ("/", "/about/", "/review/", "/explor_views/%s/" % self.category.slug):
            html = self.client.get(url).content.decode()
            titles.add(re.search(r"<title>(.*?)</title>", html, re.S).group(1))
        self.assertEqual(len(titles), 4)

    def test_category_page_seo_overrides_and_schema(self):
        self.category.meta_title = "Deep Cleaning Services | Royal Home Services"
        self.category.save()
        response = self.client.get("/explor_views/%s/" % self.category.slug)
        html = response.content.decode()
        self.assertIn("<title>Deep Cleaning Services | Royal Home Services</title>", html)
        types = {n["@type"] for n in jsonld(response)[0]["@graph"]}
        self.assertTrue({"WebSite", "WebPage", "BreadcrumbList", "Service", "FAQPage"} <= types)

    def test_schema_never_contains_invented_business_data(self):
        graph = jsonld(self.client.get("/"))[0]["@graph"]
        business = next(n for n in graph if n["@id"].endswith("#business"))
        for key in ("address", "geo", "openingHours", "aggregateRating", "review"):
            self.assertNotIn(key, business)

    def test_schema_can_be_disabled(self):
        self.category.schema_enabled = False
        self.category.save()
        self.assertNotIn("ld+json", self.client.get("/explor_views/%s/" % self.category.slug).content.decode())

    def test_category_with_two_services_no_longer_500s(self):
        make_service(self.category, title="Second service", slug="second-service")
        self.assertEqual(self.client.get("/explor_views/%s/" % self.category.slug).status_code, 200)

    # --- canonical validation ------------------------------------------------
    def test_canonical_validation(self):
        self.assertIsNone(validate_canonical(SITE + "/about/"))
        self.assertIsNotNone(validate_canonical("https://other.test/about/"))
        self.assertIsNotNone(validate_canonical(SITE + "/admin/"))
        self.assertIsNotNone(validate_canonical(SITE + "/nope/"))
        self.assertIsNotNone(validate_canonical(SITE + "/about/?x=1"))
        self.category.canonical_url = "https://other.test/"
        with self.assertRaises(ValidationError):
            self.category.full_clean()

    def test_invalid_canonical_override_is_ignored_at_render_time(self):
        Category.objects.filter(pk=self.category.pk).update(canonical_url="https://other.test/x/")
        html = self.client.get("/explor_views/%s/" % self.category.slug).content.decode()
        self.assertIn('rel="canonical" href="%s/explor_views/%s/"' % (SITE, self.category.slug), html)

    # --- sitemap / robots ----------------------------------------------------
    def test_sitemap(self):
        response = self.client.get("/sitemap.xml")
        self.assertEqual(response.status_code, 200)
        self.assertIn("xml", response["Content-Type"])
        body = response.content.decode()
        self.assertIn("<loc>%s/</loc>" % SITE, body)
        self.assertIn("<loc>%s/explor_views/%s/</loc>" % (SITE, self.category.slug), body)
        self.assertIn("<loc>%s/about/</loc>" % SITE, body)
        for excluded in ("/admin", "/dashboard", "/adminlogin", "/complaint/", "/employe/"):
            self.assertNotIn(excluded, body)

    def test_sitemap_omits_noindex_category(self):
        Category.objects.filter(pk=self.category.pk).update(robots_index=False)
        self.assertNotIn("explor_views", self.client.get("/sitemap.xml").content.decode())

    def test_robots_txt(self):
        response = self.client.get("/robots.txt")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response["Content-Type"].startswith("text/plain"))
        body = response.content.decode()
        self.assertIn("Disallow: /admin/", body)
        self.assertIn("Sitemap: %s/sitemap.xml" % SITE, body)
        self.assertNotIn("Disallow: /static", body)
        self.assertNotIn("Disallow: /media", body)

    # --- admin ---------------------------------------------------------------
    def test_admin_seo_pages_render(self):
        from django.contrib.auth import get_user_model
        user = get_user_model().objects.create_superuser("seo-admin", "a@example.test", "pw-for-tests-123")
        self.client.force_login(user)
        for url in ("/admin/homepage/service/%d/change/" % self.service.pk,
                    "/admin/homepage/category/%d/change/" % self.category.pk,
                    "/admin/homepage/staticpageseo/",
                    "/admin/homepage/staticpageseo/%d/change/" % StaticPageSEO.objects.get(page_key="home").pk):
            self.assertEqual(self.client.get(url).status_code, 200, url)


# --------------------------------------------------------------------------- audit additions
from django.http import HttpResponse
from django.test import RequestFactory

from .middleware import CanonicalHostMiddleware, PrivateAreaRobotsMiddleware
from .seo import auto_category_description, auto_category_title


@override_settings(SITE_URL=SITE, ALLOWED_HOSTS=["testserver", "www.example.test"])
class SeoAuditTests(TestCase):
    def setUp(self):
        self.category = Category.objects.create(category_name="Deep Cleaning")

    def test_auto_title_names_service_areas_when_it_fits(self):
        self.assertEqual(auto_category_title("Deep Cleaning"),
                         "Deep Cleaning in Rawalpindi & Islamabad | Royal Home Services")
        long_name = "Complete Whole House Move In Move Out Deep Cleaning"
        self.assertEqual(auto_category_title(long_name), "%s | Royal Home Services" % long_name)

    def test_auto_description_ignores_placeholder_sized_intro(self):
        self.assertIn("Deep Cleaning in Rawalpindi & Islamabad from Royal Home Services", auto_category_description("Deep Cleaning", "le"))
        intro = "A thorough top-to-bottom deep clean covering kitchens, bathrooms, floors and living areas."
        self.assertEqual(auto_category_description("Deep Cleaning", intro), intro)

    def test_rendered_category_page_uses_improved_automatic_metadata(self):
        make_service(self.category, paragraph_1="x")
        html = self.client.get("/explor_views/%s/" % self.category.slug).content.decode()
        self.assertIn("<title>Deep Cleaning in Rawalpindi &amp; Islamabad | Royal Home Services</title>", html)
        self.assertNotIn('name="description" content="x"', html)
        self.assertEqual(html.count('name="description"'), 1)

    def test_admin_entered_metadata_is_never_overridden(self):
        self.category.meta_title = "Custom Title"
        self.category.meta_description = "Custom description that the admin wrote for this page."
        self.category.save()
        make_service(self.category)
        html = self.client.get("/explor_views/%s/" % self.category.slug).content.decode()
        self.assertIn("<title>Custom Title</title>", html)
        self.assertIn('content="Custom description that the admin wrote for this page."', html)

    def test_business_schema_type_is_valid_generic_local_business(self):
        graph = jsonld(self.client.get("/"))[0]["@graph"]
        business = next(n for n in graph if n["@id"].endswith("#business"))
        self.assertEqual(business["@type"], "LocalBusiness")

    def test_private_areas_send_noindex_header_public_pages_do_not(self):
        for url in ("/adminlogin/", "/dashboard/", "/admin/login/"):
            self.assertEqual(self.client.get(url)["X-Robots-Tag"], "noindex, nofollow", url)
        for url in ("/", "/about/", "/robots.txt"):  # (Django's own sitemap view adds its own header)
            self.assertNotIn("X-Robots-Tag", self.client.get(url), url)

    def test_private_pages_are_not_in_sitemap_and_are_disallowed_in_robots(self):
        body = self.client.get("/sitemap.xml").content.decode()
        for path in ("/adminlogin", "/dashboard", "/admin"):
            self.assertNotIn(path, body)
        robots = self.client.get("/robots.txt").content.decode()
        for path in ("/adminlogin/", "/dashboard/", "/admin/"):
            self.assertIn("Disallow: %s" % path, robots)

    def test_every_public_page_has_exactly_one_of_each_head_tag(self):
        make_service(self.category)
        for url in ("/", "/about/", "/review/", "/complaint/", "/employe/", "/explor_views/%s/" % self.category.slug):
            html = self.client.get(url).content.decode()
            for needle in ("<title>", 'name="robots"', 'rel="canonical"', 'property="og:title"',
                           'name="twitter:card"', 'name="description"'):
                self.assertEqual(html.count(needle), 1, (url, needle))

    @override_settings(DEBUG=False, ALLOWED_HOSTS=["example.com", "www.example.test"])
    def test_canonical_host_middleware_redirects_http_and_wrong_host_in_one_hop(self):
        mw = CanonicalHostMiddleware(lambda request: HttpResponse("ok"))
        rf = RequestFactory()
        r = mw(rf.get("/about/", HTTP_HOST="example.com"))
        self.assertEqual((r.status_code, r["Location"]), (301, "https://www.example.test/about/"))
        r = mw(rf.get("/about", HTTP_HOST="example.com"))  # trailing slash folded into the same hop
        self.assertEqual(r["Location"], "https://www.example.test/about/")
        r = mw(rf.get("/about/", HTTP_HOST="www.example.test"))  # right host, plain http
        self.assertEqual(r["Location"], "https://www.example.test/about/")
        r = mw(rf.get("/about/", HTTP_HOST="www.example.test", secure=True))
        self.assertEqual(r.status_code, 200)

    def test_private_area_middleware_unit(self):
        mw = PrivateAreaRobotsMiddleware(lambda request: HttpResponse("x"))
        self.assertEqual(mw(RequestFactory().get("/dashboard/orders/"))["X-Robots-Tag"], "noindex, nofollow")
        self.assertNotIn("X-Robots-Tag", mw(RequestFactory().get("/about/")))
