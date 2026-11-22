from urllib.parse import urlencode

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.core.cache import cache
from django.http import Http404, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_POST

from complaint.models import CustomerComplaint
from employes.models import EmployeeRegistration
from homepage.models import Booking

from . import dashboard_queries as dq
from .locations import LOCATION_CHOICES, LOCATION_LABELS, classify_location
from .models import Review
from .permissions import is_dashboard_admin, staff_required

GENERIC_LOGIN_ERROR = "Invalid username or password. Please try again."
LOCKED_LOGIN_ERROR = "Too many failed attempts. Please wait a few minutes and try again."


# ============================================================== authentication
def _client_ip(request):
    # REMOTE_ADDR only: X-Forwarded-For is client-controlled unless a trusted proxy sets it.
    return request.META.get("REMOTE_ADDR", "unknown")


def _throttle_key(request, username):
    return "adminlogin:%s:%s" % (_client_ip(request), username.lower()[:150])


def _is_locked(key):
    return cache.get(key, 0) >= getattr(settings, "ADMIN_LOGIN_MAX_FAILURES", 5)


def _register_failure(key):
    lock = getattr(settings, "ADMIN_LOGIN_LOCK_SECONDS", 900)
    cache.add(key, 0, lock)
    try:
        cache.incr(key)
    except ValueError:  # key expired between add() and incr()
        cache.set(key, 1, lock)


def _safe_next(request):
    target = request.POST.get("next") or request.GET.get("next") or ""
    if target and url_has_allowed_host_and_scheme(
            target, allowed_hosts={request.get_host()}, require_https=request.is_secure()):
        # Only dashboard URLs are valid destinations.
        if target.startswith(reverse("dashboard")):
            return target
    return ""


@never_cache
@csrf_protect
def adminlogin(request):
    if is_dashboard_admin(request.user):
        return redirect(_safe_next(request) or "dashboard")

    context = {"error": "", "username": "", "next": _safe_next(request),
               "logged_out": request.GET.get("logged_out") == "1"}

    if request.method == "POST":
        username = (request.POST.get("username") or "").strip()
        password = request.POST.get("password") or ""
        remember = request.POST.get("remember_me") == "on"
        context["username"] = username[:150]
        key = _throttle_key(request, username)

        if _is_locked(key):
            context["error"] = LOCKED_LOGIN_ERROR
            return render(request, "admin/adminlogin.html", context, status=429)

        user = authenticate(request, username=username, password=password) if username and password else None

        # Wrong credentials and "valid user but not staff" produce the SAME message, so the
        # page never reveals whether an account exists or what rights it has.
        if user is None or not is_dashboard_admin(user):
            _register_failure(key)
            context["error"] = GENERIC_LOGIN_ERROR
            return render(request, "admin/adminlogin.html", context, status=401)

        cache.delete(key)
        login(request, user)  # rotates the session key (prevents session fixation)
        if remember:
            request.session.set_expiry(getattr(settings, "ADMIN_REMEMBER_ME_AGE", 60 * 60 * 24 * 14))
        else:
            request.session.set_expiry(0)  # expires when the browser closes
        return redirect(_safe_next(request) or "dashboard")

    return render(request, "admin/adminlogin.html", context)


@require_POST
@csrf_protect
def admin_logout(request):
    """POST-only (CSRF-protected) so a link or image on another site cannot sign admins out."""
    logout(request)  # flushes the session data and cookie
    return redirect(reverse("adminlogin") + "?logged_out=1")


# ============================================================== dashboard
def _qs_without_page(params):
    """Query string of the current filters without ``page`` (used by page links)."""
    pairs = []
    for key, values in params.lists():
        if key == "page":
            continue
        pairs.extend((key, value) for value in values if value != "")
    return urlencode(pairs)


def _base_context(request, section):
    return {"section": section, "page_title": {
        "orders": "Orders", "order_detail": "Order details", "employees": "Employees", "employee_detail": "Employee details", "complaints": "Complaints", "reviews": "Reviews",
        "complaint_detail": "Complaint details"}.get(section, "Dashboard")}


def _list_context(request, section, queryset, filters, warnings, options, total_all):
    for text in warnings:
        messages.warning(request, text)
    page = dq.paginate(queryset, request.GET.get("page"))
    # The default "date_field" is only meaningful together with a date, so keep URLs clean.
    has_dates = bool(filters.get("date_from") or filters.get("date_to"))
    qs_base = urlencode([(k, v) for k, v in filters.items() if v and (k != "date_field" or has_dates)])
    context = _base_context(request, section)
    context.update({
        "page_obj": page,
        "filters": filters,
        "filters_active": any(filters.get(k) for k in filters if k != "date_field"),
        "qs_base": qs_base,                                   # filters without page
        # query string that returns to exactly this page of exactly these filters
        "qs_current": qs_base + (("&" if qs_base else "") + "page=%d" % page.number if page.number > 1 else ""),
        "total_all": total_all,
        "location_choices": LOCATION_CHOICES,
        "page_numbers": _page_window(page),
    })
    context.update(options)
    return context


def _page_window(page, span=2):
    total = page.paginator.num_pages
    if total <= 1:
        return []
    numbers = sorted({1, total, *range(max(1, page.number - span), min(total, page.number + span) + 1)})
    result, previous = [], 0
    for n in numbers:
        if n - previous > 1:
            result.append(None)  # ellipsis
        result.append(n)
        previous = n
    return result


@staff_required
def dashboard(request):
    # There is deliberately no overview page: the dashboard opens on Orders.
    return redirect("dashboard_orders")


@staff_required
def orders_view(request):
    queryset, filters, warnings = dq.orders_queryset(request.GET)
    context = _list_context(request, "orders", queryset, filters, warnings,
                            dq.orders_options(), total_all=Booking.objects.count())
    for order in context["page_obj"].object_list:
        order.area = LOCATION_LABELS.get(classify_location(order.service_address), "Other / unknown")
    return render(request, "admin/dasboard.html", context)


@staff_required
def order_detail_view(request, pk):
    order = get_object_or_404(Booking, pk=pk)
    context = _base_context(request, "order_detail")
    context.update({
        "order": order,
        "area": LOCATION_LABELS.get(classify_location(order.service_address), "Other / unknown"),
    })
    return render(request, "admin/dasboard.html", context)


@staff_required
@require_POST
def order_delete_view(request, pk):
    order = get_object_or_404(Booking, pk=pk)
    order_id = order.pk
    order.delete()
    messages.success(request, "Deleted order #%s." % order_id)
    return redirect("dashboard_orders")


@staff_required
def employees_view(request):
    queryset, filters, warnings = dq.employees_queryset(request.GET)
    counts = dq.employee_location_counts()
    context = _list_context(request, "employees", queryset, filters, warnings,
                            dq.employees_options(), total_all=counts["all"])
    base = [(k, v) for k, v in filters.items() if v and k != "location"]
    tabs = []
    for key, label in LOCATION_CHOICES:
        params = base + ([("location", key)] if key else [])
        tabs.append({
            "key": key, "label": label.replace("All locations", "All"), "count": counts[key or "all"],
            "url": reverse("dashboard_employees") + ("?" + urlencode(params) if params else ""),
            "active": filters["location"] == key,
        })
    context["location_tabs"] = tabs
    for employee in context["page_obj"].object_list:
        employee.area = LOCATION_LABELS.get(
            classify_location(employee.em_location, exact_aliases=True), "Other / unknown")
        employee.initials = "".join(w[0] for w in (employee.username or "?").split()[:2]).upper() or "?"
    return render(request, "admin/dasboard.html", context)


@staff_required
def employee_detail_view(request, pk):
    employee = get_object_or_404(EmployeeRegistration, pk=pk)
    context = _base_context(request, "employee_detail")
    context.update({
        "employee": employee,
        "area": LOCATION_LABELS.get(
            classify_location(employee.em_location, exact_aliases=True), "Other / unknown"),
    })
    return render(request, "admin/dasboard.html", context)


@staff_required
@require_POST
def employee_delete_view(request, pk):
    employee = get_object_or_404(EmployeeRegistration, pk=pk)
    employee_name = employee.username
    employee.delete()
    messages.success(request, "Deleted the team registration for %s." % employee_name)

    params = []
    for key in ("q", "location", "department", "page"):
        value = (request.POST.get(key) or "").strip()
        if value:
            params.append((key, value))
    query = urlencode(params)
    return redirect(reverse("dashboard_employees") + ("?" + query if query else ""))


@staff_required
def complaints_view(request):
    queryset, filters, warnings = dq.complaints_queryset(request.GET)
    context = _list_context(request, "complaints", queryset, filters, warnings,
                            dq.complaints_options(), total_all=CustomerComplaint.objects.count())
    for complaint in context["page_obj"].object_list:
        complaint.area = LOCATION_LABELS.get(classify_location(complaint.service_address), "Other / unknown")
    return render(request, "admin/dasboard.html", context)


@staff_required
def complaint_detail_view(request, pk):
    complaint = get_object_or_404(CustomerComplaint, pk=pk)
    back = reverse("dashboard_complaints")
    query = _qs_without_page(request.GET)
    page = request.GET.get("page", "")
    if page.isdigit():
        query = (query + "&" if query else "") + "page=" + page
    context = _base_context(request, "complaint_detail")
    context.update({
        "complaint": complaint,
        "area": LOCATION_LABELS.get(classify_location(complaint.service_address), "Other / unknown"),
        "back_url": back + ("?" + query if query else ""),
    })
    return render(request, "admin/dasboard.html", context)


@staff_required
def reviews_view(request):
    queryset = Review.objects.order_by("is_approved", "-created_at", "-id")
    page = dq.paginate(queryset, request.GET.get("page"))
    context = _base_context(request, "reviews")
    context.update({
        "page_obj": page,
        "page_numbers": _page_window(page),
        "qs_base": "",
        "total_all": Review.objects.count(),
        "pending_count": Review.objects.filter(is_approved=False).count(),
        "approved_count": Review.objects.filter(is_approved=True).count(),
    })
    return render(request, "admin/dasboard.html", context)


@staff_required
@require_POST
def review_approval_view(request, pk):
    review_record = get_object_or_404(Review, pk=pk)
    review_record.is_approved = not review_record.is_approved
    review_record.save(update_fields=["is_approved"])
    state = "approved and published" if review_record.is_approved else "unpublished"
    messages.success(request, "Review by %s was %s." % (review_record.name, state))
    page = (request.POST.get("page") or "").strip()
    url = reverse("dashboard_reviews")
    if page.isdigit() and int(page) > 1:
        url += "?page=%s" % int(page)
    return redirect(url)


# ============================================================== public reviews (unchanged)
def review(request):

    if request.method == 'POST':

        name = request.POST.get('name', '').strip()
        review_text = request.POST.get('review', '').strip()

        if not name or not review_text:
            return JsonResponse({
                'success': False,
                'message': 'Please fill in both fields.'
            }, status=400)

        if len(name) > 100 or len(review_text) > 2000:
            return JsonResponse({
                'success': False,
                'message': 'Maximum character limit exceeded.'
            }, status=400)

        Review.objects.create(
            name=name,
            review=review_text
        )

        return JsonResponse({
            'success': True,
            'message': 'Thank you! Your review is awaiting admin approval.'
        })

    reviews = Review.objects.filter(is_approved=True)

    return render(request, 'admin/review.html', {
        'reviews': reviews,
        'total_reviews': reviews.count()
    })
