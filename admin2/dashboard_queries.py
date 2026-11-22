"""QuerySet builders for the three dashboard sections.

Each ``*_queryset(params)`` takes a plain dict of GET values and returns
``(queryset, filters, warnings)``:
  * queryset  - lazily evaluated; nothing is loaded into memory until the page is sliced
  * filters   - the cleaned filter values (used to re-fill the form and build page links)
  * warnings  - human-readable notes for ignored/invalid inputs
Only ORM lookups with bound parameters are used (no raw SQL, no string-built queries).
None of these models has a ForeignKey, so select_related()/prefetch_related() would have
nothing to join; list views use .only() so large text columns are not fetched needlessly.
"""
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.utils.dateparse import parse_date

from complaint.models import CustomerComplaint
from employes.models import EmployeeRegistration
from homepage.models import Booking

from .locations import LOCATION_LABELS, OTHER, VALID_LOCATIONS, location_q

PAGE_SIZE = 20
MAX_SEARCH_LENGTH = 100


# ------------------------------------------------------------------ small helpers
def _clean_search(params):
    return " ".join((params.get("q") or "").split())[:MAX_SEARCH_LENGTH]


def _search_q(search, text_fields):
    """Every word must match at least one of ``text_fields`` (icontains); a word that is
    numeric (optionally '#12') also matches the primary key."""
    q = Q()
    for word in search.split():
        term = Q()
        for field in text_fields:
            term |= Q(**{f"{field}__icontains": word})
        digits = word.lstrip("#")
        if digits.isdigit() and len(digits) <= 18:
            term |= Q(pk=int(digits))
        q &= term
    return q


def _date(params, key, label, warnings):
    raw = (params.get(key) or "").strip()
    if not raw:
        return None, ""
    parsed = None
    try:
        parsed = parse_date(raw)
    except ValueError:
        parsed = None
    if parsed is None:
        warnings.append("Ignored an invalid %s date." % label)
        return None, ""
    return parsed, parsed.isoformat()


def _choice_from_db(params, key, queryset, field):
    """A value is accepted only if it really exists in the database (so the filter list is
    always real data, never a hard-coded list)."""
    value = (params.get(key) or "").strip()
    if not value:
        return ""
    if queryset.filter(**{field: value}).exists():
        return value
    return ""


def _distinct(queryset, field):
    return list(
        queryset.exclude(**{f"{field}__isnull": True}).exclude(**{field: ""})
        .order_by(field).values_list(field, flat=True).distinct()
    )


def _location(params):
    value = (params.get("location") or "").strip().lower()
    return value if value in VALID_LOCATIONS else ""


def _swap_dates(start, end, warnings):
    if start and end and start > end:
        warnings.append("The 'from' date was after the 'to' date, so the two were swapped.")
        return end, start
    return start, end


def paginate(queryset, page_number, per_page=PAGE_SIZE):
    return Paginator(queryset, per_page).get_page(page_number)


# ------------------------------------------------------------------ orders (Booking)
def orders_queryset(params):
    warnings = []
    base = Booking.objects.all()
    qs = base.only("id", "full_name", "phone_number", "service_address",
                   "cleaning_service", "preferred_date", "created_at")

    search = _clean_search(params)
    qs = qs.filter(_search_q(search, ["full_name", "phone_number", "service_address", "cleaning_service"]))

    service = _choice_from_db(params, "service", base, "cleaning_service")
    if service:
        qs = qs.filter(cleaning_service=service)

    location = _location(params)
    if location:
        qs = qs.filter(location_q("service_address", location))

    date_from, from_str = _date(params, "date_from", "'preferred date from'", warnings)
    date_to, to_str = _date(params, "date_to", "'preferred date to'", warnings)
    date_from, date_to = _swap_dates(date_from, date_to, warnings)
    if date_from:
        qs = qs.filter(preferred_date__gte=date_from)
    if date_to:
        qs = qs.filter(preferred_date__lte=date_to)
    from_str = date_from.isoformat() if date_from else ""
    to_str = date_to.isoformat() if date_to else ""

    filters = {"q": search, "service": service, "location": location,
               "date_from": from_str, "date_to": to_str}
    return qs.order_by("-created_at", "-id"), filters, warnings


def orders_options():
    return {"services": _distinct(Booking.objects.all(), "cleaning_service")}


# ------------------------------------------------------------------ employees
def employees_queryset(params):
    warnings = []
    base = EmployeeRegistration.objects.all()
    qs = base.only("id", "username", "email", "phone_number", "department", "em_location", "created_at")

    search = _clean_search(params)
    qs = qs.filter(_search_q(search, ["username", "email", "phone_number", "department", "em_location"]))

    department = _choice_from_db(params, "department", base, "department")
    if department:
        qs = qs.filter(department=department)

    location = _location(params)
    if location:
        qs = qs.filter(location_q("em_location", location, exact_aliases=True))

    filters = {"q": search, "department": department, "location": location}
    return qs.order_by("-created_at", "-id"), filters, warnings


def employees_options():
    return {"departments": _distinct(EmployeeRegistration.objects.all(), "department")}


def employee_location_counts():
    """Counts for the location tabs, in ONE query (not one per tab)."""
    rwp = location_q("em_location", "rawalpindi", exact_aliases=True)
    isb = location_q("em_location", "islamabad", exact_aliases=True)
    oth = location_q("em_location", OTHER, exact_aliases=True)
    row = EmployeeRegistration.objects.aggregate(
        all=Count("id"),
        rawalpindi=Count("id", filter=rwp),
        islamabad=Count("id", filter=isb),
        other=Count("id", filter=oth),
    )
    return row


# ------------------------------------------------------------------ complaints
COMPLAINT_DATE_FIELDS = {
    "submitted": ("created_at__date", "submission date"),
    "service": ("date_of_service", "service date"),
}


def complaints_queryset(params):
    warnings = []
    base = CustomerComplaint.objects.all()
    qs = base.only("id", "full_name", "phone_number", "email_address", "date_of_service",
                   "service_address", "service_type", "technician_name", "what_went_wrong",
                   "created_at")

    search = _clean_search(params)
    qs = qs.filter(_search_q(search, [
        "full_name", "phone_number", "email_address", "service_address", "service_type",
        "technician_name", "what_went_wrong", "service_details",
    ]))

    service_type = _choice_from_db(params, "service_type", base, "service_type")
    if service_type:
        qs = qs.filter(service_type=service_type)

    location = _location(params)
    if location:
        qs = qs.filter(location_q("service_address", location))

    date_field = (params.get("date_field") or "submitted").strip()
    if date_field not in COMPLAINT_DATE_FIELDS:
        date_field = "submitted"
    lookup, label = COMPLAINT_DATE_FIELDS[date_field]
    date_from, _ = _date(params, "date_from", "'%s from'" % label, warnings)
    date_to, _ = _date(params, "date_to", "'%s to'" % label, warnings)
    date_from, date_to = _swap_dates(date_from, date_to, warnings)
    if date_from:
        qs = qs.filter(**{f"{lookup}__gte": date_from})
    if date_to:
        qs = qs.filter(**{f"{lookup}__lte": date_to})

    filters = {
        "q": search, "service_type": service_type, "location": location, "date_field": date_field,
        "date_from": date_from.isoformat() if date_from else "",
        "date_to": date_to.isoformat() if date_to else "",
    }
    return qs.order_by("-created_at", "-id"), filters, warnings


def complaints_options():
    return {"service_types": _distinct(CustomerComplaint.objects.all(), "service_type")}


__all__ = [
    "LOCATION_LABELS", "PAGE_SIZE", "paginate", "orders_queryset", "orders_options",
    "employees_queryset", "employees_options", "employee_location_counts",
    "complaints_queryset", "complaints_options", "COMPLAINT_DATE_FIELDS",
]
