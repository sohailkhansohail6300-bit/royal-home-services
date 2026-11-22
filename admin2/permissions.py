"""Access control for the custom admin dashboard (server-side, every request)."""
from functools import wraps
from urllib.parse import urlencode

from zoneinfo import ZoneInfo

from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.cache import never_cache


def is_dashboard_admin(user):
    """Only active staff members or superusers. Ordinary customers/users never qualify."""
    return bool(user and user.is_authenticated and user.is_active and (user.is_staff or user.is_superuser))


def staff_required(view):
    """Anonymous -> redirect to the admin login (keeps ?next=). Logged in but not staff ->
    403. Responses are never cached, so a logged-out browser cannot show them via Back."""

    @wraps(view)
    @never_cache
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            target = reverse("adminlogin")
            if request.method == "GET":
                target += "?" + urlencode({"next": request.get_full_path()})
            return redirect(target)
        if not is_dashboard_admin(request.user):
            raise PermissionDenied("Staff access required.")
        # Show AND filter dates in local (Pakistan) time for the whole request/response cycle.
        zone = ZoneInfo(getattr(settings, "ADMIN_DASHBOARD_TIMEZONE", settings.TIME_ZONE))
        with timezone.override(zone):
            return view(request, *args, **kwargs)

    return wrapper
