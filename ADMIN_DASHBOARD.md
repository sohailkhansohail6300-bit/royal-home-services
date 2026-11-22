# Admin login and dashboard (admin2 app)

## URLs
| URL | Purpose |
|---|---|
| `/adminlogin/` | Login (Django `authenticate()` + `login()`) |
| `/dashboard/` | Redirects to Orders (there is no overview page) |
| `/dashboard/orders/` | Orders: `homepage.Booking` |
| `/dashboard/employees/` | Employees: `employes.EmployeeRegistration`, with Rawalpindi / Islamabad / Other tabs |
| `/dashboard/complaints/` | Complaints: `complaint.CustomerComplaint` |
| `/dashboard/complaints/<id>/` | Full complaint details |
| `/dashboard/logout/` | Logout (POST + CSRF only) |

Filenames were kept as they are in the project: `templates/admin/adminlogin.html` and `templates/admin/dasboard.html` (the original spelling). The dashboard page is split into small includes next to it: `_dash_orders.html`, `_dash_employees.html`, `_dash_complaints.html`, `_dash_complaint_detail.html`, `_dash_pagination.html`.

## Who can sign in
Active users with **Staff status** or **Superuser status**. Ordinary users get the same generic "Invalid username or password" message as a wrong password (the page never reveals whether an account exists). A signed-in non-staff user who opens a dashboard URL gets HTTP 403; anonymous visitors are redirected to the login page.

## Create or authorize an admin account
```
python manage.py createsuperuser                       # new administrator
```
or, for an existing user: open `/admin/` -> Users -> tick **Staff status** (and **Active**) -> save. To revoke access, untick Staff status (and Superuser status).
Your database already contains one staff superuser (`abid`); the password is not stored in readable form, so use `python manage.py changepassword abid` if you do not remember it.

## Commands
```
cd "home cleaning"
pip install "django>=5.2,<5.3" pillow    # plus opencv-python only if you use admin2/face_tracking.py
python manage.py migrate                 # already applied in the shipped db.sqlite3; harmless to re-run
python manage.py check
python manage.py test                    # 94 tests
python manage.py runserver
```
No new models or migrations were needed for the dashboard.

## Behaviour notes
* **Remember me**: checked = session cookie lasts 14 days (`ADMIN_REMEMBER_ME_AGE`); unchecked = ends when the browser closes.
* **Brute-force throttle**: 5 failed attempts per IP + username within 15 minutes lock that pair for the rest of the window (HTTP 429). It uses Django's cache (per-process memory by default); configure a shared cache (Redis/Memcached/database) if you run several workers.
* **Cookies**: HttpOnly, SameSite=Lax; `Secure` is switched on automatically when `DJANGO_DEBUG=0`.
* **Time zone**: data is stored in UTC as before; dashboard pages display and filter dates in Pakistan time (`ADMIN_DASHBOARD_TIMEZONE`).
* **Responses are `no-store`** and carry `X-Robots-Tag: noindex`, so the Back button does not reveal data after logout.
* The brand text "HomeServe" in the dashboard header is from your original design and was left as is.

## How locations are decided (no new fields)
* Employees: `em_location` (case-insensitive; spelling variants such as "rawalpindi cantt", "Islamabd"; whole-value abbreviations RWP, ISB). Other = anything else, empty/NULL, or a value naming both cities.
* Orders and complaints: the free-text `service_address`. Rawalpindi = mentions Rawalpindi and not Islamabad; Islamabad = the reverse; **Other / unknown** = neither, or both. Sector names, "Bahria Town", "DHA" etc. exist in both cities and are never used to guess.
* Spelling variants live in `admin2/locations.py` (one tuple per city) - add more there.
* Your current records are placeholder text ("f", "vwd", "jdvds"), so on today's data every row falls under Other / unknown; real addresses that include the city name will filter correctly.

## Optional improvements (not implemented, would need a migration)
* A `status` field on `CustomerComplaint` (New / In progress / Resolved) and on `Booking`. Not added because it was not required and the values would be invented.
* Normalised `city` columns on all three models, if you later want faster filtering or to collect the city as a separate form field.
