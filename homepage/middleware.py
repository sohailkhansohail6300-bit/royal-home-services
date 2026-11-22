"""One preferred host + HTTPS, in a single redirect (no chains).

Active only when settings.SITE_URL is set AND DEBUG is False, so local development is
unaffected. Behind a reverse proxy, also set SECURE_PROXY_SSL_HEADER so Django can tell
the request was already HTTPS (otherwise this would redirect forever).
"""
from urllib.parse import urlsplit

from django.conf import settings
from django.http import HttpResponsePermanentRedirect
from django.urls import is_valid_path
from django.utils.encoding import iri_to_uri

LOCAL_HOSTS = {"localhost", "127.0.0.1", "[::1]", "testserver"}


class CanonicalHostMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        site = urlsplit(getattr(settings, "SITE_URL", "") or "")
        self.scheme = site.scheme
        self.netloc = site.netloc
        self.enabled = bool(self.scheme and self.netloc) and not settings.DEBUG

    def __call__(self, request):
        if self.enabled:
            host = request.get_host()
            if host.split(":")[0] not in LOCAL_HOSTS:
                wrong_host = host.lower() != self.netloc.lower()
                wrong_scheme = self.scheme == "https" and not request.is_secure()
                if wrong_host or wrong_scheme:
                    path = request.path
                    # Fold Django's APPEND_SLASH redirect into this one so it is never a second hop.
                    if (settings.APPEND_SLASH and not path.endswith("/")
                            and not is_valid_path(path) and is_valid_path(path + "/")):
                        path += "/"
                    query = request.META.get("QUERY_STRING", "")
                    url = "%s://%s%s" % (self.scheme, self.netloc, iri_to_uri(path))
                    if query:
                        url += "?" + query
                    return HttpResponsePermanentRedirect(url)
        return self.get_response(request)


class PrivateAreaRobotsMiddleware:
    """Adds ``X-Robots-Tag: noindex, nofollow`` to the private areas.

    This complements (never replaces) authentication: it also covers Django's own /admin/
    pages, which have no <meta robots> tag. robots.txt + noindex are hints, not security.
    """

    PREFIXES = ("/admin/", "/adminlogin/", "/dashboard/")

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        if request.path.startswith(self.PREFIXES):
            response["X-Robots-Tag"] = "noindex, nofollow"
        return response
