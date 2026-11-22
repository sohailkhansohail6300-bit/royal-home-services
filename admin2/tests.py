import datetime
import json

from django.contrib.auth import get_user_model
from django.contrib.sessions.models import Session
from django.core.cache import cache
from django.test import Client, TestCase, override_settings
from django.utils import timezone

from complaint.models import CustomerComplaint
from employes.models import EmployeeRegistration
from homepage.models import Booking

from .locations import classify_location, location_q
from .models import Review

User = get_user_model()
PW = "pw-for-tests-123"


def make_booking(i=1, **kw):
    data = dict(full_name="Customer %d" % i, phone_number="0300000%04d" % i,
                service_address="House %d, Bahria Town, Rawalpindi" % i,
                cleaning_service="deep", preferred_date=datetime.date(2026, 12, 1))
    data.update(kw)
    return Booking.objects.create(**data)


def make_complaint(i=1, **kw):
    data = dict(full_name="Complainant %d" % i, phone_number="0311000%04d" % i,
                email_address="c%d@example.test" % i, date_of_service=datetime.date(2026, 10, 1),
                service_address="Street %d, Islamabad" % i, service_details="Details %d" % i,
                service_type="Deep Cleaning", technician_name="Tech %d" % i,
                what_went_wrong="Missed spots %d" % i, desired_resolution="Redo %d" % i,
                additional_details="Extra %d" % i, followup_preference="Phone")
    data.update(kw)
    return CustomerComplaint.objects.create(**data)


def make_employee(name, location, department="cleaning", **kw):
    data = dict(username=name, email=("%s@example.test" % name.replace(" ", ".")).lower(),
                phone_number="03001234567", department=department, em_location=location)
    data.update(kw)
    return EmployeeRegistration.objects.create(**data)


class BaseCase(TestCase):
    def setUp(self):
        cache.clear()
        self.staff = User.objects.create_user("staffer", "s@example.test", PW, is_staff=True)
        self.plain = User.objects.create_user("customer", "c@example.test", PW)
        self.client = Client()

    def login_staff(self):
        self.client.force_login(self.staff)


# ====================================================================== authentication
class AuthenticationTests(BaseCase):
    def post_login(self, username="staffer", password=PW, **extra):
        data = {"username": username, "password": password}
        data.update(extra)
        return self.client.post("/adminlogin/", data)

    def test_login_page_renders_form_posting_to_django(self):
        r = self.client.get("/adminlogin/")
        html = r.content.decode()
        self.assertEqual(r.status_code, 200)
        self.assertIn('action="/adminlogin/"', html)
        self.assertIn("csrfmiddlewaretoken", html)
        self.assertNotIn('action="#"', html)
        self.assertIn('name="robots" content="noindex, nofollow"', html)
        self.assertEqual(r["X-Robots-Tag"], "noindex, nofollow")
        # the malformed anchor wrapping the button is gone
        self.assertNotIn("<a href='/dashboard/'></a>", html)
        self.assertEqual(html.count("</button></a>"), 0)

    def test_valid_staff_login_redirects_to_dashboard(self):
        r = self.post_login()
        self.assertRedirects(r, "/dashboard/", fetch_redirect_response=False)
        self.assertIn("_auth_user_id", self.client.session)
        self.assertEqual(self.client.get("/dashboard/orders/").status_code, 200)

    def test_superuser_without_staff_flag_is_allowed(self):
        User.objects.create_user("boss", "b@example.test", PW, is_superuser=True)
        self.assertEqual(self.post_login("boss").status_code, 302)

    def test_invalid_password_rejected_with_generic_message(self):
        r = self.post_login(password="wrong")
        self.assertEqual(r.status_code, 401)
        self.assertContains(r, "Invalid username or password", status_code=401)
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_unknown_user_and_wrong_password_look_identical(self):
        a = self.post_login("nobody", "x").content.decode()
        b = self.post_login("staffer", "x").content.decode()
        strip = lambda h: h.split('name="csrfmiddlewaretoken"')[0].split("Invalid username")[1][:60]
        self.assertEqual(strip(a), strip(b))

    def test_non_staff_user_cannot_log_in_and_message_does_not_reveal_why(self):
        r = self.post_login("customer")
        self.assertEqual(r.status_code, 401)
        self.assertContains(r, "Invalid username or password", status_code=401)
        self.assertNotContains(r, "staff", status_code=401)
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_inactive_staff_rejected(self):
        self.staff.is_active = False
        self.staff.save()
        self.assertEqual(self.post_login().status_code, 401)

    def test_empty_fields_rejected(self):
        self.assertEqual(self.post_login("", "").status_code, 401)

    def test_csrf_enforced_on_login(self):
        strict = Client(enforce_csrf_checks=True)
        r = strict.post("/adminlogin/", {"username": "staffer", "password": PW})
        self.assertEqual(r.status_code, 403)

    def test_remember_me_checked_gives_persistent_session(self):
        r = self.post_login(remember_me="on")
        self.assertFalse(self.client.session.get_expire_at_browser_close())
        self.assertGreaterEqual(self.client.session.get_expiry_age(), 14 * 86400 - 5)
        self.assertEqual(r.cookies["sessionid"]["max-age"], 14 * 86400)

    def test_remember_me_unchecked_expires_with_browser(self):
        r = self.post_login()
        self.assertTrue(self.client.session.get_expire_at_browser_close())
        self.assertEqual(r.cookies["sessionid"]["max-age"], "")

    def test_session_cookie_flags(self):
        r = self.post_login()
        self.assertTrue(r.cookies["sessionid"]["httponly"])
        self.assertEqual(r.cookies["sessionid"]["samesite"], "Lax")

    def test_session_key_rotates_on_login(self):
        self.client.get("/adminlogin/")
        before = self.client.session.session_key
        self.post_login()
        self.assertNotEqual(before, self.client.session.session_key)

    def test_failed_login_throttle_locks_even_correct_password(self):
        for _ in range(5):
            self.assertEqual(self.post_login(password="bad").status_code, 401)
        r = self.post_login()  # correct password, but locked
        self.assertEqual(r.status_code, 429)
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_already_logged_in_admin_is_redirected_from_login_page(self):
        self.login_staff()
        self.assertRedirects(self.client.get("/adminlogin/"), "/dashboard/", fetch_redirect_response=False)

    def test_next_parameter_open_redirect_is_blocked(self):
        r = self.client.post("/adminlogin/", {"username": "staffer", "password": PW, "next": "https://evil.example/"})
        self.assertEqual(r["Location"], "/dashboard/")
        self.client.logout()
        r = self.client.post("/adminlogin/", {"username": "staffer", "password": PW, "next": "/dashboard/employees/?q=a"})
        self.assertEqual(r["Location"], "/dashboard/employees/?q=a")
        self.client.logout()
        r = self.client.post("/adminlogin/", {"username": "staffer", "password": PW, "next": "/admin/"})
        self.assertEqual(r["Location"], "/dashboard/")  # only dashboard URLs allowed


PROTECTED = ["/dashboard/", "/dashboard/orders/", "/dashboard/employees/", "/dashboard/complaints/"]


class DashboardAccessTests(BaseCase):
    def test_anonymous_redirected_to_login_for_every_endpoint(self):
        c = make_complaint()
        for url in PROTECTED + ["/dashboard/complaints/%d/" % c.pk, "/dashboard/orders/?q=x&page=2"]:
            r = self.client.get(url)
            self.assertEqual(r.status_code, 302, url)
            self.assertTrue(r["Location"].startswith("/adminlogin/"), url)

    def test_anonymous_never_sees_complaint_data(self):
        c = make_complaint(full_name="Secret Person")
        r = self.client.get("/dashboard/complaints/%d/" % c.pk, follow=True)
        self.assertNotContains(r, "Secret Person")

    def test_non_staff_authenticated_user_gets_403(self):
        c = make_complaint()
        self.client.force_login(self.plain)
        for url in PROTECTED + ["/dashboard/complaints/%d/" % c.pk]:
            self.assertEqual(self.client.get(url).status_code, 403, url)

    def test_staff_gets_200(self):
        self.login_staff()
        for url in PROTECTED[1:]:
            self.assertEqual(self.client.get(url).status_code, 200, url)
        self.assertRedirects(self.client.get("/dashboard/"), "/dashboard/orders/", fetch_redirect_response=False)

    def test_inactive_user_session_is_denied(self):
        self.login_staff()
        self.staff.is_active = False
        self.staff.save()
        self.assertEqual(self.client.get("/dashboard/orders/").status_code, 302)

    def test_dashboard_responses_not_cacheable_and_noindex(self):
        self.login_staff()
        r = self.client.get("/dashboard/orders/")
        self.assertIn("no-store", r["Cache-Control"])
        self.assertEqual(r["X-Robots-Tag"], "noindex, nofollow")
        self.assertContains(r, 'name="robots" content="noindex, nofollow"')

    def test_logout_requires_post(self):
        self.login_staff()
        self.assertEqual(self.client.get("/dashboard/logout/").status_code, 405)
        self.assertEqual(self.client.get("/dashboard/orders/").status_code, 200)  # still logged in

    def test_logout_post_destroys_session(self):
        self.login_staff()
        key = self.client.session.session_key
        r = self.client.post("/dashboard/logout/")
        self.assertRedirects(r, "/adminlogin/?logged_out=1", fetch_redirect_response=False)
        self.assertFalse(Session.objects.filter(session_key=key).exists())
        self.assertEqual(self.client.get("/dashboard/orders/").status_code, 302)
        self.assertContains(self.client.get("/adminlogin/?logged_out=1"), "You have been signed out")

    def test_logout_csrf_enforced(self):
        strict = Client(enforce_csrf_checks=True)
        strict.force_login(self.staff)
        self.assertEqual(strict.post("/dashboard/logout/").status_code, 403)
        self.assertEqual(strict.get("/dashboard/orders/").status_code, 200)

    def test_expired_session_is_rejected(self):
        self.client.post("/adminlogin/", {"username": "staffer", "password": PW})
        self.assertEqual(self.client.get("/dashboard/orders/").status_code, 200)
        Session.objects.update(expire_date=timezone.now() - datetime.timedelta(minutes=1))
        r = self.client.get("/dashboard/orders/")
        self.assertEqual(r.status_code, 302)
        self.assertTrue(r["Location"].startswith("/adminlogin/"))

    def test_only_three_sections_and_logout_in_navigation(self):
        self.login_staff()
        html = self.client.get("/dashboard/orders/").content.decode()
        nav = html.split('id="primaryNav"')[1].split("</nav>")[0]
        for label in ("Orders", "Employees", "Complaints"):
            self.assertIn(label, nav)
        self.assertNotIn("Overview", html)
        self.assertNotIn(">Dashboard<", html)
        self.assertIn("Logout", html)
        self.assertIn('action="/dashboard/logout/"', html)

    def test_no_demo_data_left(self):
        self.login_staff()
        for url in PROTECTED[1:]:
            html = self.client.get(url).content.decode()
            for demo in ("Sarah Chen", "ORD-10", "Mark Rivera", "homeserve.demo", "$24,580", "1,248"):
                self.assertNotIn(demo, html, url)


# ====================================================================== orders
class OrdersTests(BaseCase):
    def setUp(self):
        super().setUp()
        self.login_staff()

    def get(self, **params):
        return self.client.get("/dashboard/orders/", params)

    def test_empty_state_when_no_orders(self):
        r = self.get()
        self.assertContains(r, "No orders yet")
        self.assertContains(r, "0</span> total order")

    def test_displays_real_bookings_latest_first_with_pk_as_id(self):
        a = make_booking(1, full_name="Alice Real")
        b = make_booking(2, full_name="Bob Real")
        r = self.get()
        html = r.content.decode()
        self.assertContains(r, "Alice Real")
        self.assertContains(r, "#%d" % a.pk)
        self.assertLess(html.index("Bob Real"), html.index("Alice Real"))  # newest first
        for col in ("Order ID", "Customer", "Phone", "Cleaning service", "Service address", "Preferred date", "Booked on"):
            self.assertContains(r, col)
        for invented in (">Amount<", ">Status<", ">Employee<"):
            self.assertNotContains(r, invented)

    def test_search_by_name_phone_address_service_and_id(self):
        a = make_booking(1, full_name="Zainab Malik", phone_number="03451112222")
        make_booking(2, full_name="Other Person", service_address="Sector F-10, Islamabad", cleaning_service="regular")
        self.assertEqual([o.pk for o in self.get(q="zainab").context["page_obj"]], [a.pk])
        self.assertEqual([o.pk for o in self.get(q="3451112").context["page_obj"]], [a.pk])
        self.assertEqual(self.get(q="F-10").context["page_obj"].paginator.count, 1)
        self.assertEqual(self.get(q="regular").context["page_obj"].paginator.count, 1)
        self.assertEqual([o.pk for o in self.get(q="#%d" % a.pk).context["page_obj"]], [a.pk])
        self.assertEqual(self.get(q="zainab islamabad").context["page_obj"].paginator.count, 0)  # AND of words
        self.assertContains(self.get(q="nomatch"), "No orders match your search or filters")

    def test_service_filter_uses_real_values_only(self):
        make_booking(1, cleaning_service="deep")
        make_booking(2, cleaning_service="regular")
        self.assertEqual(self.get(service="regular").context["page_obj"].paginator.count, 1)
        self.assertEqual(self.get(service="not-a-service").context["page_obj"].paginator.count, 2)  # ignored
        self.assertEqual(sorted(self.get().context["services"]), ["deep", "regular"])

    def test_location_filter(self):
        rwp = make_booking(1, service_address="Saddar, RAWALPINDI")
        isb = make_booking(2, service_address="F-7 Markaz islamabad")
        both = make_booking(3, service_address="Rawalpindi side of Islamabad Highway")
        none = make_booking(4, service_address="Lahore")
        pks = lambda loc: sorted(o.pk for o in self.get(location=loc).context["page_obj"])
        self.assertEqual(pks("rawalpindi"), [rwp.pk])
        self.assertEqual(pks("islamabad"), [isb.pk])
        self.assertEqual(pks("other"), sorted([both.pk, none.pk]))  # ambiguous + unknown are not guessed
        self.assertEqual(len(pks("")), 4)
        self.assertEqual(len(pks("bogus")), 4)

    def test_preferred_date_filter_and_invalid_date_warning(self):
        make_booking(1, preferred_date=datetime.date(2026, 11, 1))
        make_booking(2, preferred_date=datetime.date(2026, 12, 15))
        r = self.get(date_from="2026-12-01", date_to="2026-12-31")
        self.assertEqual(r.context["page_obj"].paginator.count, 1)
        r = self.get(date_from="not-a-date")
        self.assertEqual(r.context["page_obj"].paginator.count, 2)
        self.assertContains(r, "Ignored an invalid")
        r = self.get(date_from="2026-12-31", date_to="2026-12-01")  # reversed -> swapped
        self.assertEqual(r.context["page_obj"].paginator.count, 1)

    def test_pagination_and_filters_are_preserved_in_page_links(self):
        for i in range(45):
            make_booking(i, service_address="Rawalpindi %d" % i)
        make_booking(99, service_address="Lahore")
        r = self.get(location="rawalpindi")
        self.assertEqual(r.context["page_obj"].paginator.num_pages, 3)
        self.assertEqual(len(r.context["page_obj"]), 20)
        self.assertContains(r, "?location=rawalpindi&amp;page=2")
        self.assertEqual(len(self.get(location="rawalpindi", page=3).context["page_obj"]), 5)
        self.assertEqual(self.get(location="rawalpindi", page="abc").context["page_obj"].number, 1)
        self.assertEqual(self.get(location="rawalpindi", page=999).context["page_obj"].number, 3)

    def test_query_count_does_not_grow_with_rows(self):
        make_booking(1)
        with self.assertNumQueries(6):
            self.get()
        for i in range(2, 20):
            make_booking(i)
        with self.assertNumQueries(6):
            self.get()

    def test_html_in_data_is_escaped(self):
        make_booking(1, full_name="<script>alert(1)</script>")
        self.assertNotContains(self.get(), "<script>alert(1)</script>")


# ====================================================================== employees
class EmployeesTests(BaseCase):
    def setUp(self):
        super().setUp()
        self.login_staff()
        self.rwp1 = make_employee("Rwp One", "Rawalpindi")
        self.rwp2 = make_employee("Rwp Two", "  rawalpindi cantt ", department="kitchen")
        self.rwp3 = make_employee("Rwp Three", "RWP")
        self.isb1 = make_employee("Isb One", "Islamabad")
        self.isb2 = make_employee("Isb Two", "Sector F-10, ISLAMABAD", department="kitchen")
        self.isb3 = make_employee("Isb Three", "isb")
        self.oth1 = make_employee("Other One", "Lahore")
        self.oth2 = make_employee("Other Two", None)
        self.oth3 = make_employee("Other Three", "")
        self.both = make_employee("Both", "Rawalpindi / Islamabad")

    def names(self, **params):
        r = self.client.get("/dashboard/employees/", params)
        return {e.username for e in r.context["page_obj"]}

    def test_displays_real_employees_with_required_columns(self):
        r = self.client.get("/dashboard/employees/")
        for col in ("Employee", "Email", "Phone", "Department", "Location", "Registered"):
            self.assertContains(r, col)
        self.assertContains(r, "Rwp One")
        self.assertContains(r, "rwp.one@example.test")
        self.assertContains(r, "10</span> total employees")

    def test_filter_rawalpindi(self):
        self.assertEqual(self.names(location="rawalpindi"), {"Rwp One", "Rwp Two", "Rwp Three"})

    def test_filter_islamabad(self):
        self.assertEqual(self.names(location="islamabad"), {"Isb One", "Isb Two", "Isb Three"})

    def test_filter_other_includes_null_blank_unknown_and_ambiguous(self):
        self.assertEqual(self.names(location="other"), {"Other One", "Other Two", "Other Three", "Both"})

    def test_all_locations_and_invalid_value(self):
        self.assertEqual(len(self.names()), 10)
        self.assertEqual(len(self.names(location="")), 10)
        self.assertEqual(len(self.names(location="mars")), 10)

    def test_location_tabs_show_correct_counts_and_links(self):
        r = self.client.get("/dashboard/employees/", {"department": "kitchen"})
        tabs = {t["key"]: t for t in r.context["location_tabs"]}
        self.assertEqual({k: t["count"] for k, t in tabs.items()},
                         {"": 10, "rawalpindi": 3, "islamabad": 3, "other": 4})
        self.assertIn("department=kitchen", tabs["islamabad"]["url"])  # other filters kept
        self.assertIn("location=islamabad", tabs["islamabad"]["url"])
        r = self.client.get("/dashboard/employees/", {"location": "islamabad"})
        self.assertTrue({t["key"]: t for t in r.context["location_tabs"]}["islamabad"]["active"])

    def test_search(self):
        self.assertEqual(self.names(q="rwp.two@"), {"Rwp Two"})
        self.assertEqual(self.names(q="f-10"), {"Isb Two"})
        self.assertEqual(self.names(q="kitchen"), {"Rwp Two", "Isb Two"})
        self.assertEqual(self.names(q="zzz"), set())

    def test_department_filter_and_combination_with_location(self):
        self.assertEqual(self.names(department="kitchen"), {"Rwp Two", "Isb Two"})
        self.assertEqual(self.names(department="kitchen", location="islamabad"), {"Isb Two"})
        self.assertEqual(self.names(department="kitchen", location="islamabad", q="two"), {"Isb Two"})
        self.assertEqual(self.names(department="unknown-dept"), self.names())
        self.assertEqual(sorted(self.client.get("/dashboard/employees/").context["departments"]), ["cleaning", "kitchen"])

    def test_pagination_keeps_location_filter(self):
        for i in range(30):
            make_employee("Bulk %d" % i, "Islamabad")
        r = self.client.get("/dashboard/employees/", {"location": "islamabad"})
        self.assertEqual(r.context["page_obj"].paginator.count, 33)
        self.assertEqual(r.context["page_obj"].paginator.num_pages, 2)
        self.assertContains(r, "?location=islamabad&amp;page=2")
        self.assertEqual(len(self.client.get("/dashboard/employees/", {"location": "islamabad", "page": 2}).context["page_obj"]), 13)

    def test_empty_states(self):
        EmployeeRegistration.objects.all().delete()
        self.assertContains(self.client.get("/dashboard/employees/"), "No employees registered yet")
        make_employee("Solo", "Lahore")
        self.assertContains(self.client.get("/dashboard/employees/", {"location": "islamabad"}),
                            "No employees match your search or filters")

    def test_no_invented_columns(self):
        r = self.client.get("/dashboard/employees/")
        for fake in (">Role<", ">Orders<", ">Status<", "Active", "On leave"):
            self.assertNotContains(r, fake)

    def test_delete_action_is_confirmed_and_csrf_protected(self):
        r = self.client.get("/dashboard/employees/")
        self.assertContains(r, "Delete registration")
        self.assertContains(r, 'onsubmit="return confirm(')
        self.assertContains(r, 'action="/dashboard/employees/%d/delete/"' % self.rwp1.pk)
        self.assertContains(r, 'name="csrfmiddlewaretoken"')

    def test_delete_employee_post_removes_registration_and_keeps_filters(self):
        response = self.client.post(
            "/dashboard/employees/%d/delete/" % self.rwp1.pk,
            {"q": "rwp one", "location": "rawalpindi", "page": "1"},
        )
        self.assertRedirects(
            response,
            "/dashboard/employees/?q=rwp+one&location=rawalpindi&page=1",
            fetch_redirect_response=False,
        )
        self.assertFalse(EmployeeRegistration.objects.filter(pk=self.rwp1.pk).exists())
        self.assertContains(self.client.get(response["Location"]), "Deleted the team registration")

    def test_employee_delete_is_post_only_and_staff_only(self):
        url = "/dashboard/employees/%d/delete/" % self.rwp1.pk
        self.assertEqual(self.client.get(url).status_code, 405)
        self.assertTrue(EmployeeRegistration.objects.filter(pk=self.rwp1.pk).exists())

        self.client.force_login(self.plain)
        self.assertEqual(self.client.post(url).status_code, 403)
        self.assertTrue(EmployeeRegistration.objects.filter(pk=self.rwp1.pk).exists())

    def test_employee_delete_requires_csrf(self):
        strict = Client(enforce_csrf_checks=True)
        strict.force_login(self.staff)
        url = "/dashboard/employees/%d/delete/" % self.rwp1.pk
        self.assertEqual(strict.post(url).status_code, 403)
        self.assertTrue(EmployeeRegistration.objects.filter(pk=self.rwp1.pk).exists())


# ====================================================================== complaints
class ComplaintsTests(BaseCase):
    def setUp(self):
        super().setUp()
        self.login_staff()

    def ids(self, **params):
        return [c.pk for c in self.client.get("/dashboard/complaints/", params).context["page_obj"]]

    def test_empty_state(self):
        self.assertContains(self.client.get("/dashboard/complaints/"), "No complaints yet")

    def test_list_shows_real_data_latest_first_and_view_details_link(self):
        a = make_complaint(1, full_name="First Complainant")
        b = make_complaint(2, full_name="Second Complainant")
        r = self.client.get("/dashboard/complaints/")
        html = r.content.decode()
        self.assertLess(html.index("Second Complainant"), html.index("First Complainant"))
        for col in ("ID", "Customer", "Phone", "Email", "Service date", "Service type",
                    "Service address", "Technician", "Complaint", "Submitted"):
            self.assertContains(r, col)
        self.assertContains(r, "View Details")
        self.assertContains(r, "/dashboard/complaints/%d/" % a.pk)
        self.assertContains(r, "Missed spots 1")

    def test_detail_page_shows_all_information(self):
        c = make_complaint(7)
        r = self.client.get("/dashboard/complaints/%d/" % c.pk)
        self.assertEqual(r.status_code, 200)
        for text in ("Complaint #%d" % c.pk, "Complainant 7", "0311000", "c7@example.test", "1 Oct 2026",
                     "Deep Cleaning", "Street 7, Islamabad", "Tech 7", "Details 7", "Missed spots 7",
                     "Redo 7", "Extra 7", "Phone", "Islamabad"):
            self.assertContains(r, text)

    def test_detail_404_for_missing(self):
        self.assertEqual(self.client.get("/dashboard/complaints/999999/").status_code, 404)

    def test_user_text_is_escaped_on_list_and_detail(self):
        c = make_complaint(1, what_went_wrong="<script>alert('x')</script>\nsecond line",
                           full_name="<img src=x onerror=alert(1)>")
        for url in ("/dashboard/complaints/", "/dashboard/complaints/%d/" % c.pk):
            r = self.client.get(url)
            self.assertNotContains(r, "<script>alert('x')")
            self.assertNotContains(r, "<img src=x onerror")
        self.assertContains(self.client.get("/dashboard/complaints/%d/" % c.pk), "second line")

    def test_search(self):
        a = make_complaint(1, full_name="Hira Noor", technician_name="Usman")
        make_complaint(2)
        self.assertEqual(self.ids(q="hira"), [a.pk])
        self.assertEqual(self.ids(q="usman"), [a.pk])
        self.assertEqual(self.ids(q="c1@example"), [a.pk])
        self.assertEqual(self.ids(q="#%d" % a.pk), [a.pk])
        self.assertEqual(self.ids(q="nomatch"), [])
        self.assertContains(self.client.get("/dashboard/complaints/", {"q": "nomatch"}), "No complaints match")

    def test_service_type_filter(self):
        a = make_complaint(1, service_type="Deep Cleaning")
        b = make_complaint(2, service_type="Regular Cleaning")
        self.assertEqual(self.ids(service_type="Regular Cleaning"), [b.pk])
        self.assertEqual(sorted(self.ids(service_type="nope")), sorted([a.pk, b.pk]))
        types = self.client.get("/dashboard/complaints/").context["service_types"]
        self.assertEqual(sorted(types), ["Deep Cleaning", "Regular Cleaning"])

    def test_date_filter_service_date_and_submission_date(self):
        a = make_complaint(1, date_of_service=datetime.date(2026, 9, 1))
        b = make_complaint(2, date_of_service=datetime.date(2026, 10, 20))
        self.assertEqual(self.ids(date_field="service", date_from="2026-10-01", date_to="2026-10-31"), [b.pk])
        self.assertEqual(self.ids(date_field="service", date_to="2026-09-30"), [a.pk])
        old = timezone.now() - datetime.timedelta(days=40)
        CustomerComplaint.objects.filter(pk=a.pk).update(created_at=old)
        cutoff = (timezone.now() - datetime.timedelta(days=10)).date().isoformat()
        self.assertEqual(self.ids(date_from=cutoff), [b.pk])                      # submitted (default)
        self.assertEqual(self.ids(date_field="submitted", date_to=cutoff), [a.pk])
        r = self.client.get("/dashboard/complaints/", {"date_from": "31/12/2026"})
        self.assertContains(r, "Ignored an invalid")

    def test_submission_date_filter_uses_pakistan_time(self):
        c = make_complaint(1)
        # 22:00 UTC on 10 Nov is already 03:00 on 11 Nov in Pakistan (UTC+5)
        CustomerComplaint.objects.filter(pk=c.pk).update(
            created_at=datetime.datetime(2026, 11, 10, 22, 0, tzinfo=datetime.timezone.utc))
        self.assertEqual(self.ids(date_from="2026-11-11", date_to="2026-11-11"), [c.pk])
        self.assertEqual(self.ids(date_from="2026-11-10", date_to="2026-11-10"), [])
        self.assertContains(self.client.get("/dashboard/complaints/"), "2026-11-11 03:00")

    def test_location_filter(self):
        rwp = make_complaint(1, service_address="Chaklala, Rawalpindi")
        isb = make_complaint(2, service_address="E-11, ISLAMABAD")
        oth = make_complaint(3, service_address="Murree road")
        self.assertEqual(self.ids(location="rawalpindi"), [rwp.pk])
        self.assertEqual(self.ids(location="islamabad"), [isb.pk])
        self.assertEqual(self.ids(location="other"), [oth.pk])

    def test_pagination_and_filter_preserved_and_detail_back_link(self):
        for i in range(25):
            make_complaint(i, service_type="Deep Cleaning")
        make_complaint(99, service_type="Other")
        r = self.client.get("/dashboard/complaints/", {"service_type": "Deep Cleaning", "page": 2})
        self.assertEqual(len(r.context["page_obj"]), 5)
        self.assertContains(r, "service_type=Deep+Cleaning&amp;page=1")
        first = r.context["page_obj"][0]
        detail = self.client.get("/dashboard/complaints/%d/" % first.pk,
                                 {"service_type": "Deep Cleaning", "page": "2", "evil": "<x>"})
        back = detail.context["back_url"]
        self.assertTrue(back.startswith("/dashboard/complaints/?"))
        self.assertIn("service_type=Deep+Cleaning", back)
        self.assertTrue(back.endswith("page=2"))
        self.assertNotContains(detail, "<x>")

    def test_no_invented_status_columns(self):
        make_complaint(1)
        r = self.client.get("/dashboard/complaints/")
        for fake in (">Status<", "Resolved", "Pending"):
            self.assertNotContains(r, fake)


# ====================================================================== location helpers
class LocationHelperTests(TestCase):
    def test_classify(self):
        self.assertEqual(classify_location("House 4, Rawalpindi"), "rawalpindi")
        self.assertEqual(classify_location("RAWAL PINDI cantt"), "rawalpindi")
        self.assertEqual(classify_location("islamabd G-11"), "islamabad")
        self.assertEqual(classify_location("Rawalpindi and Islamabad"), "other")
        self.assertEqual(classify_location("Bahria Town"), "other")  # exists in both cities: not guessed
        self.assertEqual(classify_location("DHA Phase 2"), "other")
        self.assertEqual(classify_location(""), "other")
        self.assertEqual(classify_location(None), "other")
        self.assertEqual(classify_location("RWP", exact_aliases=True), "rawalpindi")
        self.assertEqual(classify_location("RWP"), "other")
        self.assertEqual(classify_location("my rwp house", exact_aliases=True), "other")  # not trusted inside text

    def test_query_and_python_classifier_agree(self):
        samples = ["Rawalpindi", "islamabad", "ISLAMABAD sector", "Rawalpindi, Islamabad", "", "Lahore", "Rawal Pindi"]
        for i, text in enumerate(samples):
            make_booking(i, service_address=text or "-")
        for choice in ("rawalpindi", "islamabad", "other"):
            by_query = set(Booking.objects.filter(location_q("service_address", choice)).values_list("service_address", flat=True))
            by_python = {b.service_address for b in Booking.objects.all() if classify_location(b.service_address) == choice}
            self.assertEqual(by_query, by_python, choice)


# ====================================================================== public-site regression
class PublicSiteRegressionTests(TestCase):
    def test_public_pages_still_render(self):
        for url in ("/", "/about/", "/review/", "/complaint/", "/employe/", "/robots.txt", "/sitemap.xml"):
            self.assertEqual(self.client.get(url).status_code, 200, url)

    def test_booking_submission_still_works(self):
        r = self.client.post("/", {"name": "Test Cust", "phone": "03001234567", "address": "Rawalpindi",
                                   "service": "deep", "date": "2026-12-01"})
        self.assertTrue(json.loads(r.content)["success"])
        self.assertEqual(Booking.objects.get().full_name, "Test Cust")

    def test_booking_validation_still_works(self):
        r = self.client.post("/", {"name": "", "phone": "1", "address": "", "service": "", "date": ""})
        self.assertFalse(json.loads(r.content)["success"])
        self.assertEqual(Booking.objects.count(), 0)

    def test_employee_registration_still_works(self):
        r = self.client.post("/employe/", {"name": "New Emp", "email": "new@example.test", "phone": "03001234567",
                                           "department": "cleaning", "location": "Islamabad", "terms": "on"})
        self.assertTrue(json.loads(r.content)["success"])
        self.assertEqual(EmployeeRegistration.objects.get().em_location, "Islamabad")

    def test_complaint_submission_still_works(self):
        r = self.client.post("/complaint/", {
            "full_name": "C", "phone_number": "0300", "email_address": "c@example.test",
            "date_of_service": "2026-10-01", "service_address": "Islamabad", "service_type": "Deep Cleaning",
            "what_went_wrong": "Bad", "desired_resolution": "Fix", "followup_preference": "Phone"})
        self.assertTrue(json.loads(r.content)["success"])
        self.assertEqual(CustomerComplaint.objects.count(), 1)

    def test_complaint_without_service_date_returns_validation_error_not_500(self):
        r = self.client.post("/complaint/", {"full_name": "C", "phone_number": "0300",
                                             "email_address": "c@example.test", "what_went_wrong": "Bad"})
        data = json.loads(r.content)
        self.assertEqual(r.status_code, 200)
        self.assertFalse(data["success"])
        self.assertIn("date_of_service", data["errors"])
        self.assertEqual(CustomerComplaint.objects.count(), 0)

    def test_review_submission_still_works(self):
        r = self.client.post("/review/", {"name": "R", "review": "Great"})
        self.assertTrue(json.loads(r.content)["success"])
        self.assertFalse(Review.objects.get().is_approved)

    def test_public_complaint_data_not_exposed_on_public_urls(self):
        make_complaint(1, full_name="Hidden Person")
        for url in ("/", "/complaint/", "/about/", "/review/", "/sitemap.xml"):
            self.assertNotContains(self.client.get(url), "Hidden Person")
