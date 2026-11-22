"""Location detection for the dashboard filters (no database fields needed).

How locations are stored today:
  * Booking.service_address / CustomerComplaint.service_address - free-text addresses
    ("House 5, Street 3, Bahria Town, Rawalpindi").
  * EmployeeRegistration.em_location - a short free-text value ("Islamabad"), may be NULL.

An address is classified as:
  * "rawalpindi" - mentions Rawalpindi (or a listed spelling variant) and NOT Islamabad
  * "islamabad"  - mentions Islamabad (or a listed spelling variant) and NOT Rawalpindi
  * "other"      - mentions neither (including empty / unknown) or mentions BOTH, because
                   which one is meant cannot be decided from the text.
Nothing is guessed from sector names, house numbers, "Bahria Town", "DHA" etc. - those exist
in both cities. To support another spelling, add it to the tuples below.
"""
from django.db.models import Q

RAWALPINDI = "rawalpindi"
ISLAMABAD = "islamabad"
OTHER = "other"

LOCATION_CHOICES = [
    ("", "All locations"),
    (RAWALPINDI, "Rawalpindi"),
    (ISLAMABAD, "Islamabad"),
    (OTHER, "Other / unknown"),
]
LOCATION_LABELS = {key: label for key, label in LOCATION_CHOICES if key}
VALID_LOCATIONS = set(LOCATION_LABELS)

# Case-insensitive substrings (spelling variants).
RAWALPINDI_TERMS = ("rawalpindi", "rawal pindi", "rawal-pindi", "rawalpindy", "rawalpandi", "rawlpindi")
ISLAMABAD_TERMS = ("islamabad", "islamabd", "islambad", "islamabaad", "isalamabad")

# Short abbreviations are only trusted when the WHOLE employee location equals them
# (a short field such as "RWP"); inside long addresses they could be false positives.
RAWALPINDI_EXACT = ("rwp", "pindi")
ISLAMABAD_EXACT = ("isb", "isl", "isbd")


def _contains_any(field, terms):
    q = Q()
    for term in terms:
        q |= Q(**{f"{field}__icontains": term})
    return q


def _exact_any(field, terms):
    q = Q()
    for term in terms:
        q |= Q(**{f"{field}__iexact": term})
    return q


def location_q(field, choice, *, exact_aliases=False):
    """Return a Q object selecting rows whose ``field`` falls in ``choice``.

    ``choice`` is one of rawalpindi / islamabad / other; anything else -> no filter.
    """
    if choice not in VALID_LOCATIONS:
        return Q()
    rwp = _contains_any(field, RAWALPINDI_TERMS)
    isb = _contains_any(field, ISLAMABAD_TERMS)
    if exact_aliases:
        rwp |= _exact_any(field, RAWALPINDI_EXACT)
        isb |= _exact_any(field, ISLAMABAD_EXACT)
    if choice == RAWALPINDI:
        return rwp & ~isb
    if choice == ISLAMABAD:
        return isb & ~rwp
    return (~rwp & ~isb) | (rwp & isb)


def classify_location(text, *, exact_aliases=False):
    """Python twin of ``location_q`` (used for the small area badge in the tables)."""
    value = (text or "").strip().lower()
    if not value:
        return OTHER
    rwp = any(t in value for t in RAWALPINDI_TERMS)
    isb = any(t in value for t in ISLAMABAD_TERMS)
    if exact_aliases:
        rwp = rwp or value in RAWALPINDI_EXACT
        isb = isb or value in ISLAMABAD_EXACT
    if rwp and not isb:
        return RAWALPINDI
    if isb and not rwp:
        return ISLAMABAD
    return OTHER
