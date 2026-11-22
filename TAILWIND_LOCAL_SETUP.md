# Local Tailwind CSS for this Django project

This project is Django-based. Use Node.js and npm only to install Tailwind and compile a local CSS file. Django serves that generated file through its static-files system. The browser does **not** load Tailwind from a CDN.

Run npm commands from the project root, `D:\home cleaning` (the folder containing `manage.py`), not from `config` or `homepage`.

## Requirements

- Python with this project's Django dependencies
- Node.js and npm
- Access to npm or a configured private/local npm registry when installing packages

Check Node and npm from PowerShell:

```powershell
node --version
npm --version
```

Installing Tailwind needs a package registry unless the dependencies are already available from a local cache. Once compiled, the website uses the local generated CSS file and does not need a Tailwind CDN connection.

## File structure

The HTML page and Tailwind source are in project-level folders beside each other. Tailwind scans the project templates and writes generated CSS under `static/css`:

```text
D:\home cleaning\
├── config\
│   ├── settings.py
│   └── urls.py
├── static\
│   ├── src\
│   │   └── input.css
│   └── css\
│       └── tailwind.css           # Generated; do not edit by hand
├── templates\
│   └── index.html
├── homepage\
│   └── views.py
├── manage.py
├── package.json
└── package-lock.json
```

`STATICFILES_DIRS` in Django settings must include the root `static` directory so Django can find the generated CSS.

## 1. Create the npm package and install Tailwind

Open PowerShell and change to the project root:

```powershell
cd "D:\home cleaning"
```

If there is no `package.json` in this directory, create one:

```powershell
npm init -y
```

Install Tailwind and the CLI locally as development dependencies:

```powershell
npm install --save-dev tailwindcss @tailwindcss/cli
```

This creates or updates `package.json`, `package-lock.json`, and `node_modules`. The browser does not download Tailwind from npm; npm is used locally to compile the CSS.

## 2. Add npm build scripts

In the project-root `package.json`, add these two entries inside the existing `"scripts"` object. Keep existing metadata and dependencies:

```json
"tailwind:watch": "tailwindcss -i ./static/src/input.css -o ./static/css/tailwind.css --watch",
"tailwind:build": "tailwindcss -i ./static/src/input.css -o ./static/css/tailwind.css --minify"
```

For example, the scripts section can look like:

```json
"scripts": {
  "test": "echo \"Error: no test specified\" && exit 1",
  "tailwind:watch": "tailwindcss -i ./static/src/input.css -o ./static/css/tailwind.css --watch",
  "tailwind:build": "tailwindcss -i ./static/src/input.css -o ./static/css/tailwind.css --minify"
}
```

The `@tailwindcss/cli` package supplies the `tailwindcss` executable. npm automatically resolves the local executable when running scripts with `npm run`.

## 3. Create the Tailwind input and output folders

From `D:\home cleaning`, run:

```powershell
New-Item -ItemType Directory -Force -Path `
  .\static\src, `
  .\static\css
```

Create `static/src/input.css` with:

```css
@import "tailwindcss";

@source "../../templates";
```

The `@source` path is relative to `static/src/input.css`; it points to the project-level `templates` directory.

Tailwind scans source files as text. Use complete utility class names in templates. Avoid building a class from fragments such as `bg-{{ color }}-600`; Tailwind cannot reliably detect classes assembled dynamically.

## 4. Register the Django app

In `config/settings.py`, add the existing homepage app to `INSTALLED_APPS` while keeping the Django apps already listed:

```python
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'homepage.apps.HomepageConfig',
]
```

The project already has `APP_DIRS = True` and `STATIC_URL = 'static/'`; keep those settings. Add the project-level static directory so Django discovers `static/css/tailwind.css`:

```python
STATICFILES_DIRS = [
    BASE_DIR / 'static',
]
```

For production, set `STATIC_ROOT` if it is not already defined:

```python
STATIC_ROOT = BASE_DIR / 'staticfiles'
```

## 5. Add a base template and a page

Create the project-level template directory if needed:

```powershell
New-Item -ItemType Directory -Force -Path .\templates
```

Create `templates/index.html`:

```django
{% load static %}
<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <link rel="stylesheet" href="{% static 'css/tailwind.css' %}">
    <title>Django site</title>
  </head>
  <body>
    <main class="mx-auto max-w-3xl p-8">
      <h1 class="text-3xl font-bold text-slate-900">Tailwind is running locally</h1>
      <p class="mt-4 text-slate-600">This CSS was compiled locally and is served by Django.</p>
    </main>
  </body>
</html>
```

The stylesheet is referenced with Django's `{% static %}` template tag. Do not add a remote Tailwind `<script>` or `<link>` element.

## 6. Connect the homepage route

In `homepage/views.py`, render the project-level template:

```python
from django.shortcuts import render


def home(request):
    return render(request, 'index.html')
```

In `config/urls.py`, connect the root URL to this view while preserving the admin route.

## 7. Build Tailwind and run Django

Run these commands from `D:\home cleaning`, not the `config` directory.

For development, open two PowerShell terminals.

Terminal 1 — compile CSS and watch for template or input CSS changes:

```powershell
cd "D:\home cleaning"
npm run tailwind:watch
```

Terminal 2 — start Django:

```powershell
cd "D:\home cleaning"
python manage.py runserver
```

Open the local URL printed by Django, usually `http://127.0.0.1:8000/`. Keep both terminals running during development.

For a one-time minified CSS build:

```powershell
cd "D:\home cleaning"
npm run tailwind:build
```

## 8. Production static files

Build the CSS before collecting Django static files:

```powershell
cd "D:\home cleaning"
npm ci --include=dev
npm run tailwind:build
python manage.py collectstatic
```

The build machine needs Node.js/npm and the local Tailwind CLI. Configure production to serve collected files from `STATIC_ROOT` using the host's supported static-file server or service. Django's development server is not a production static-file server.

Commit `package.json` and `package-lock.json` for reproducible npm installs. Do not commit `node_modules/`.

## 9. Troubleshooting

- **`npm error ENOENT ... package.json`:** You are in a directory without a Node package manifest. Change to `D:\home cleaning` (the directory containing `manage.py`) and run `npm init -y`, then install Tailwind and add the scripts above.
- **`Missing script: tailwind:build`:** Add the `tailwind:build` script to the root `package.json`.
- **`tailwindcss` is not recognized:** Run `npm install` in the project root, then run the command as `npm run tailwind:build` or `npm run tailwind:watch`.
- **No CSS file is generated:** Confirm `static/src/input.css` exists, the output directory `static/css` exists, and the CLI reports no build errors.
- **Stylesheet returns 404:** Confirm `STATICFILES_DIRS` includes `BASE_DIR / 'static'`, the generated file exists at `static/css/tailwind.css`, and the template uses `{% static 'css/tailwind.css' %}`.
- **A utility class has no effect:** Confirm the full class name appears literally in a template under `templates/`, the `@source` path is correct, and the CSS build ran after the template change.
- **Changes do not appear:** Keep the Tailwind watcher running and refresh the browser; hard-refresh if the CSS may be cached.

## No-CDN rule

Do not include `cdn.tailwindcss.com` or any remote Tailwind script or stylesheet in templates. Tailwind is installed locally, compiled into `static/css/tailwind.css`, and loaded by Django from its static-files path. No Tailwind CDN is used.
