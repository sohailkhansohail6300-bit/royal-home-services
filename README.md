# Royal Home Services

**Professional home and specialist cleaning services in Rawalpindi, Islamabad, Taxila, Tarnol, and nearby areas.**

Website: [https://royalhomeservices.site/](https://royalhomeservices.site/)

Royal Home Services is a service-business website that helps customers explore cleaning solutions, request a booking, contact the team, submit feedback, and learn about the company's services. The website presents a customer-focused cleaning experience for residential and selected commercial spaces.

> **Project note:** This README documents the publicly visible website and the project context provided for its development. Confirm the repository's actual settings, installed packages, environment-variable names, and deployment commands before using the setup instructions in a production environment.

---

## Contents

- [Project Overview](#project-overview)
- [Live Website](#live-website)
- [Services](#services)
- [Website Features](#website-features)
- [Customer Journey](#customer-journey)
- [Service Areas](#service-areas)
- [Technology Stack](#technology-stack)
- [Project Structure](#project-structure)
- [Local Development](#local-development)
- [Environment Configuration](#environment-configuration)
- [Database and Administration](#database-and-administration)
- [Deployment](#deployment)
- [SEO and Performance](#seo-and-performance)
- [Security Considerations](#security-considerations)
- [Contact](#contact)
- [Credits](#credits)

## Project Overview

Royal Home Services provides an online presence for a cleaning service business. The website is designed to make it straightforward for potential customers to:

- Discover available cleaning services.
- Understand what each service includes.
- Request a cleaning appointment.
- Contact the business by phone or WhatsApp.
- Read customer feedback and submit a review.
- Submit a complaint or service-related concern.
- Explore information about the company.
- Find service coverage and contact details.

The website focuses on clear service information, accessible booking actions, responsive layouts, and direct communication.

## Live Website

| Page | URL | Purpose |
|---|---|---|
| Home | [royalhomeservices.site](https://royalhomeservices.site/) | Main landing page, service highlights, booking form, and customer feedback |
| About | [About Royal Home Services](https://royalhomeservices.site/about/) | Company introduction, mission, vision, and values |
| Customer Support | [Customer Support](https://royalhomeservices.site/complaint/) | Complaint and feedback submission |
| Customer Reviews | [Customer Reviews](https://royalhomeservices.site/review/) | Published customer feedback and review submission |
| Join Us | [Join Our Team](https://royalhomeservices.site/employe/) | Employee/team application page |

Service detail pages:

- [Bed and Blind Cleaning](https://royalhomeservices.site/explor_views/bed-and-blind-cleaning/)
- [Carpet Cleaning](https://royalhomeservices.site/explor_views/Carpet-Cleaning/)
- [Rug Cleaning](https://royalhomeservices.site/explor_views/rug-cleaner/)
- [Sofa and Chair Cleaning](https://royalhomeservices.site/explor_views/sofa-chair-cleaning/)
- [Water Tank Cleaning](https://royalhomeservices.site/explor_views/water-tank-cleaning/)

## Services

Royal Home Services currently presents the following specialist cleaning services:

### 1. Bed and Blind Cleaning

Cleaning for mattresses, bed frames, headboards, and different blind types. The service description highlights material-appropriate cleaning methods and on-site blind cleaning.

### 2. Carpet Cleaning

Carpet cleaning for residential spaces, including inspection, dust removal, stain pre-treatment, suitable deep-cleaning methods, drying guidance, and a final quality check.

### 3. Rug Cleaning

Cleaning for household rugs, with the cleaning approach selected according to the rug's material, construction, and condition.

### 4. Sofa and Chair Cleaning

Upholstery cleaning for sofas, couches, and chairs in homes and offices. The service focuses on everyday dirt, stains, pet hair, and refreshing upholstered furniture.

### 5. Water Tank Cleaning

Cleaning for overhead and underground water tanks. The published service process describes draining, debris removal, scrubbing, sanitizing, rinsing, refilling, and final inspection.

Service availability, pricing, appointment timing, and the suitability of a cleaning method should be confirmed directly with the business.

## Website Features

### Customer-facing website

- Responsive home page and navigation.
- Company information and service-area details.
- Dedicated service detail pages.
- Service enquiry and booking form.
- Phone and WhatsApp contact actions.
- Customer reviews display and review submission.
- Customer support and complaint submission.
- Team recruitment/application page.
- Clear calls to action throughout the customer journey.

### Booking and enquiries

The home page provides a booking form that collects customer details, including:

- Full name
- Phone number
- Service address or city
- Requested cleaning service
- Preferred date

The website also offers direct phone and WhatsApp contact for customers who prefer to discuss their requirements before booking. A booking request should be treated as an enquiry until the business confirms the appointment.

### Customer support

The support page provides a complaint form for customers to share their contact details, service information, the issue, and their preferred follow-up method. The page states an expected response window of 24–48 hours; the business should ensure this service commitment is operationally maintained.

### Customer reviews

The reviews page displays published feedback and provides a form for customers to submit a review.

### Team recruitment

The Join Us page provides an online entry point for people interested in joining the service team. Review the live form and the application's backend before documenting specific application fields or approval workflows.

## Customer Journey

```text
Visit the website
       |
       v
Explore cleaning services
       |
       v
Choose a service
       |
       v
Submit booking enquiry
or contact the team directly
       |
       v
Business reviews the request
       |
       v
Appointment details confirmed
       |
       v
Cleaning service delivered
       |
       v
Customer can submit feedback
or contact customer support
```

## Service Areas

The website lists the following primary service locations:

- Rawalpindi, Pakistan
- Islamabad, Pakistan
- Taxila, Pakistan
- Tarnol, Pakistan
- Nearby areas, subject to confirmation

Customers should contact the team to confirm availability for an exact address.

## Technology Stack

The project context identifies the website as a Django-based application using Tailwind CSS. Confirm the exact versions and database configuration from the repository before publishing version-specific claims.

| Layer | Technology | Purpose |
|---|---|---|
| Backend | Python, Django | Server-side application, routing, business logic, and data handling |
| Frontend | HTML5, Tailwind CSS, JavaScript | Responsive pages, layouts, styling, and interactive behavior |
| Database | MySQL (project deployment context) | Persistent application data |
| Administration | Django Admin (where configured) | Administrative management of application records |
| Hosting | cPanel-based hosting (deployment context) | Website hosting and deployment |

If the repository uses a different database, frontend build process, or hosting setup, update this table to match the actual implementation.

## Project Structure

The exact repository tree was not available during preparation of this README. A typical Django project for this website may be organized as follows; use the real repository structure when adapting it:

# Project Structure

```text
home cleaning/
├── admin2/
│   ├── migrations/
│   │   ├── 0001_initial.py
│   │   └── __init__.py
│   ├── __init__.py
│   ├── admin.py
│   ├── apps.py
│   ├── dashboard_queries.py
│   ├── locations.py
│   ├── models.py
│   ├── permissions.py
│   ├── tests.py
│   ├── urls.py
│   └── views.py
├── backups/
│   └── db.sqlite3.before-seo-migrations
├── complaint/
│   ├── migrations/
│   │   ├── 0001_initial.py
│   │   └── __init__.py
│   ├── __init__.py
│   ├── admin.py
│   ├── apps.py
│   ├── models.py
│   ├── tests.py
│   └── views.py
├── config/
│   ├── __init__.py
│   ├── asgi.py
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── employes/
│   ├── migrations/
│   │   ├── 0001_initial.py
│   │   └── __init__.py
│   ├── __init__.py
│   ├── admin.py
│   ├── apps.py
│   ├── models.py
│   ├── tests.py
│   └── views.py
├── homepage/
│   ├── migrations/
│   │   ├── 0001_initial.py
│   │   ├── 0002_category_service.py
│   │   ├── 0003_seo_fields.py
│   │   ├── 0004_seed_static_page_seo.py
│   │   └── __init__.py
│   ├── static/
│   │   └── homepage/
│   │       └── css/
│   │           └── tailwind.css
│   ├── __init__.py
│   ├── admin.py
│   ├── apps.py
│   ├── context_processors.py
│   ├── middleware.py
│   ├── models.py
│   ├── seo.py
│   ├── seo_views.py
│   ├── sitemaps.py
│   ├── tests.py
│   └── views.py
├── media/
│   └── services/
├── services/
├── static/
│   ├── css/
│   │   └── tailwind.css
│   ├── images/
│   │   ├── favicon/
│   │   ├── home.jpeg
│   │   └── logo.jpg
│   ├── src/
│   │   └── input.css
│   └── video/
│       └── video1.mp4
├── templates/
│   ├── admin/
│   │   ├── _dash_complaint_detail.html
│   │   ├── _dash_complaints.html
│   │   ├── _dash_employee_detail.html
│   │   ├── _dash_employees.html
│   │   ├── _dash_order_detail.html
│   │   ├── _dash_orders.html
│   │   ├── _dash_pagination.html
│   │   ├── _dash_reviews.html
│   │   ├── adminlogin.html
│   │   ├── dasboard.html
│   │   └── review.html
│   ├── complaint/
│   │   ├── about.html
│   │   ├── complaint.html
│   │   └── explor_views.html
│   ├── employe/
│   │   └── employe.html
│   ├── seo/
│   │   └── head.html
│   ├── footer.html
│   ├── header.html
│   ├── home.html
│   ├── index1.html
│   └── litenave.html
├── .env.example
├── db.sqlite3
├── manage.py
├── package.json
├── README.md
├── requirements.txt
└── SEO_REPORT.md
```


Do not create these directories solely to match this example. Keep the documentation aligned with the actual source tree.

## Local Development

The following is a standard Django setup guide. The exact project settings module and dependency list must be taken from the repository.

### Prerequisites

- Python version supported by the project's Django version
- pip
- MySQL Server, if using the MySQL configuration
- Node.js and npm only if the project includes a Tailwind CSS build pipeline

### 1. Clone the repository

Replace the placeholder below with the actual GitHub repository URL:

```bash
git clone <your-repository-url>
cd <repository-directory>
```

### 2. Create and activate a virtual environment

Windows PowerShell:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
```

macOS / Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install Python dependencies

If the repository contains `requirements.txt`:

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Configure environment variables

Create a local `.env` file using the variable names expected by the Django settings. Do not copy example values into production.

Typical configuration values may include:

```env
DEBUG=True
SECRET_KEY=replace-with-a-local-development-secret
ALLOWED_HOSTS=localhost,127.0.0.1

DB_NAME=royal_home_services
DB_USER=your_database_user
DB_PASSWORD=your_database_password
DB_HOST=127.0.0.1
DB_PORT=3306
```

These names are illustrative. Use the exact names read by the project's settings and environment loader.

### 5. Apply migrations

```bash
python manage.py migrate
```

### 6. Create an administrator account

```bash
python manage.py createsuperuser
```

### 7. Run the development server

```bash
python manage.py runserver
```

Open:

```text
http://127.0.0.1:8000/
```

If the project uses a separate frontend development server or a different settings module, follow the commands defined by the repository.

## Environment Configuration

Keep environment-specific settings outside source control.

At minimum, review:

- Django secret key
- Debug mode
- Allowed hosts
- Database credentials
- Email provider configuration, if forms send email
- Media and static file settings
- HTTPS and secure-cookie settings
- Any external service credentials

A `.env.example` file should contain variable names and safe placeholder values only. Never commit real credentials, API keys, private customer information, or production database exports.

## Database and Administration

If the deployed application uses MySQL, configure the database and database user through the hosting control panel or the database administrator.

For a Django deployment:

1. Create the database and a dedicated database user.
2. Grant the user only the permissions required by the application.
3. Add the credentials to the server-side environment configuration.
4. Run Django migrations during deployment.
5. Create or verify the administrator account.
6. Confirm that booking, review, support, and recruitment submissions are stored and handled correctly.
7. Back up the database regularly and test restoration procedures.

Django Admin should be protected by strong credentials and should not be treated as a substitute for application-level authorization.

## Deployment

The live website is hosted at [royalhomeservices.site](https://royalhomeservices.site/). The project context indicates cPanel-based hosting.

A typical Django deployment workflow includes:

1. Upload or pull the reviewed application code to the hosting environment.
2. Configure the Python application and virtual environment supported by the hosting provider.
3. Install dependencies from the project's requirements file.
4. Configure production environment variables and database credentials.
5. Configure the WSGI entry point and application settings.
6. Run database migrations.
7. Configure static and media file handling.
8. Configure the domain, HTTPS, and allowed hosts.
9. Test all forms, email or messaging integrations, and administrative workflows.
10. Review application logs after deployment.

Hosting providers differ in their Python application support and deployment configuration. Follow the actual cPanel environment rather than assuming every cPanel account supports the same Django deployment process.

## SEO and Performance

The website targets customers searching for cleaning services in Rawalpindi and Islamabad and nearby service areas.

Recommended maintenance practices:

- Give every important page a unique, descriptive title and meta description.
- Use one clear primary heading per page and a logical heading hierarchy.
- Write original service descriptions that accurately describe the work offered.
- Use descriptive image filenames and meaningful alternative text.
- Compress images and serve appropriately sized formats.
- Use canonical URLs consistently.
- Maintain an XML sitemap and a suitable `robots.txt`.
- Link related service pages and contact/booking pages naturally.
- Keep business name, phone number, email, and service areas consistent.
- Add relevant structured data only when it accurately reflects visible and verifiable business information.
- Monitor indexing, search queries, and page performance in Google Search Console.
- Avoid publishing unsupported claims, fabricated reviews, or unverified business credentials.

## Security Considerations

Before making changes or deploying updates:

- Keep `DEBUG=False` in production.
- Use a strong, private Django `SECRET_KEY`.
- Restrict `ALLOWED_HOSTS` to the intended domains.
- Use HTTPS and secure session/CSRF cookie settings.
- Validate and sanitize all form input on the server.
- Apply CSRF protection to state-changing forms.
- Restrict access to administrative routes and sensitive records.
- Validate uploaded files by type and size.
- Keep dependencies updated and remove unused packages.
- Do not expose database credentials or private customer data.
- Back up the database and uploaded media.
- Test booking and complaint forms after every significant release.

## Contact

**Royal Home Services**

- Website: [https://royalhomeservices.site/](https://royalhomeservices.site/)
- Phone: [+92 305 300 0854](tel:+923053000854)
- WhatsApp: [Chat with Royal Home Services](https://wa.me/923053000854)
- Email: [ibrahimkhan07861122330@gmail.com](mailto:ibrahimkhan07861122330@gmail.com)

**Service coverage:** Rawalpindi, Islamabad, Taxila, Tarnol, and nearby areas in Pakistan.

## Credits

Website Development and Design credits:

- **Sohail**
- **Abid**

---

**Royal Home Services — A cleaner home, a better everyday.**
