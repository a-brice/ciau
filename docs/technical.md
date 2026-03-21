# CIAU — Technical Architecture

---

## Stack

| Layer | Technology |
|---|---|
| Web framework | Django 5.x |
| Database | SQLite3 (`db.sqlite3` at project root) |
| Templates | Jinja2 (via `django.template.backends.jinja2`) |
| Styling | TailwindCSS (CDN or local build) |
| File storage | Local `/uploads/` directory |
| Deployment | gunicorn + Nginx |

---

## Authentication

No user accounts, no role management.
Access is protected by a **single global password** defined in `.env`.

### How it works

- Every view is protected by a custom `@session_required` decorator.
- If the session is not authenticated, the user is redirected to `/login/`.
- On login, the submitted password is compared to `APP_PASSWORD` from settings.
- On success, `request.session['authenticated'] = True` is set.

### `.env`

```env
APP_PASSWORD=your_secret_password
SECRET_KEY=your-django-secret-key
DEBUG=True
```

### Session guard decorator

```python
# projets/utils.py
from django.shortcuts import redirect

def session_required(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.session.get('authenticated'):
            return redirect('login')
        return view_func(request, *args, **kwargs)
    return wrapper
```

### Login view

```python
# POST /login/
def login_view(request):
    if request.method == 'POST':
        if request.POST.get('password') == settings.APP_PASSWORD:
            request.session['authenticated'] = True
            return redirect('dashboard')
    return render(request, 'login.html', {'error': True})
```

---

## Project structure

```
ciau/
├── manage.py
├── .env
├── .env.example           # committed — no secrets, just keys with empty values
├── db.sqlite3             # gitignored
├── uploads/               # gitignored — see §File storage
│   └── <project_id>/
│       ├── deliverables/
│       └── references/
├── ciau/                  # Django project (settings, urls, wsgi)
│   ├── settings.py
│   ├── urls.py
│   └── jinja2.py          # Jinja2 environment config
├── projets/               # Main app
│   ├── models.py
│   ├── views.py
│   ├── urls.py
│   ├── forms.py
│   └── utils.py           # session_required, helpers
├── templates/             # Jinja2 templates
│   ├── base.html
│   ├── login.html
│   ├── dashboard.html
│   ├── projects/
│   │   ├── list.html
│   │   ├── detail.html
│   │   ├── form.html
│   │   └── archives.html
│   ├── activities/
│   │   └── week.html
│   └── contracts/
│       └── list.html
└── static/                # Static assets (committed)
    ├── css/
    │   └── main.css       # Tailwind output (if building locally)
    ├── js/
    │   └── main.js
    └── img/
        └── logo.svg
```

**`settings.py` — static files config:**

```python
STATIC_URL  = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'  # populated by collectstatic for production
```

---

## File storage

No external storage service. Files are stored locally under `/uploads/`.

### Directory layout

```
uploads/
└── <project_id>/             # e.g. uploads/42/
    ├── deliverables/         # Files attached to study phases
    │   ├── EP_site_plan.pdf
    │   └── APS_report.docx
    └── references/           # Contracts, photos, exported contacts
        └── signed_contract.pdf
```

### Rules

- `uploads/<project_id>/` is created automatically when a project is created.
- File names are **slugified** on upload (no spaces, no special characters).
- Max file size is set in `settings.py` via `FILE_UPLOAD_MAX_MEMORY_SIZE`.
- Files are served by Django in development (`MEDIA_URL` / `MEDIA_ROOT`), by Nginx in production.

### `settings.py`

```python
MEDIA_ROOT = BASE_DIR / 'uploads'
MEDIA_URL  = '/uploads/'
FILE_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024  # 10 MB
```

---

## Jinja2 setup

```python
# ciau/jinja2.py
from django.templatetags.static import static
from django.urls import reverse

def environment(**options):
    from jinja2 import Environment
    env = Environment(**options)
    env.globals.update({
        'static': static,
        'url': reverse,
    })
    return env
```

```python
# settings.py
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.jinja2.Jinja2',
        'DIRS': [BASE_DIR / 'templates'],
        'OPTIONS': {
            'environment': 'ciau.jinja2.environment',
        },
    },
    {
        # Keep Django templates backend for the admin only
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]
```

---

## Deployment

### Local development

```bash
cp .env.example .env        # fill in APP_PASSWORD and SECRET_KEY
python manage.py migrate
python manage.py runserver
```

### Production (gunicorn + Nginx)

```nginx
server {
    listen 80;
    server_name ciau.local;

    location /uploads/ {
        alias /path/to/ciau/uploads/;
    }

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
    }
}
```

```bash
gunicorn ciau.wsgi:application --bind 127.0.0.1:8000
```

---

## Do's and Don'ts

### Models

| ✅ Do | ❌ Don't |
|---|---|
| Use `get_object_or_404(Model, pk=pk)` in every view that fetches by ID | Use `Model.objects.get()` directly — it raises an unhandled `DoesNotExist` |
| Define `__str__` on every model | Leave models without a readable string representation |
| Use `class Meta: ordering` to set a default queryset order | Sort in the template or in every view separately |
| Keep business logic (solde calculation, slug generation) in model methods or `utils.py` | Put business logic inside views or templates |
| Use `DecimalField` for all monetary amounts (FCFA) | Use `FloatField` for money — floating-point errors on financial data |

### Views

| ✅ Do | ❌ Don't |
|---|---|
| Apply `@session_required` to every view except `login_view` | Forget to protect a view — all routes must be behind the session guard |
| Follow the **PRG pattern** (Post → redirect after every successful POST) | Render a template directly after a POST — causes duplicate submissions on refresh |
| Pass only what the template needs in the context dict | Pass entire querysets or raw model lists when a simple value would do |
| Validate file uploads (extension whitelist, size check) before saving | Save any uploaded file without validation |
| Use Django `Form` or `ModelForm` classes for all user input | Parse `request.POST` manually |

### Templates

| ✅ Do | ❌ Don't |
|---|---|
| Use `base.html` blocks (`{% block content %}`) for every page | Duplicate layout HTML across templates |
| Use the `url()` global (from `jinja2.py`) for all internal links | Hardcode URL paths in templates |
| Use `{{ value \| default('—') }}` for optional fields | Leave empty cells blank with no fallback |
| Keep templates thin — no calculations, no queries | Do filtering, arithmetic, or DB lookups inside templates |

### File uploads

| ✅ Do | ❌ Don't |
|---|---|
| Slugify and sanitize the file name before saving | Save files with the original user-provided name |
| Store files under `uploads/<project_id>/deliverables/` or `uploads/<project_id>/references/` | Dump all files in a flat `uploads/` directory |
| Create the project upload directory with `os.makedirs(..., exist_ok=True)` | Assume the directory already exists |

### CSS

| ✅ Do | ❌ Don't |
|---|---|
| Use plain CSS in separate file | Write custom CSS for things Tailwind already handles |
| Use semantic color aliases (`text-red-600` for errors, `text-green-600` for success) consistently | Mix arbitrary hex colors |
| Use `hidden` / `block` / `flex` to show/hide elements based on state | Use `style="display:none"` inline |

### JavaScript

| ✅ Do | ❌ Don't |
|---|---|
| Use plain `fetch()` for lightweight interactions (mark acompte as received, toggle state) | Pull in a full JS framework (React, Vue) — overkill for Jinja2-rendered pages |
| Scope JS to specific pages by adding a `data-page` attribute on `<body>` and checking it | Load all scripts on every page regardless of relevance |
| Use `<form>` + standard POST for all create/update/delete actions | Reimplement form submission logic in JS when a plain form works |
| Show a loading indicator on buttons during async requests (`button.disabled = true`) | Let the user click multiple times with no feedback |
| Handle `fetch()` errors explicitly and show a user-facing message | Silently swallow fetch errors |
