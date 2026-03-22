import os
import unicodedata
import re
from datetime import date, timedelta
from functools import wraps

from django.shortcuts import redirect


# ---------------------------------------------------------------------------
# Session guard
# ---------------------------------------------------------------------------

def session_required(view_func):
    """Redirect to login if the session is not authenticated."""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.session.get('authenticated'):
            return redirect('login')
        return view_func(request, *args, **kwargs)
    return wrapper


# ---------------------------------------------------------------------------
# File helpers
# ---------------------------------------------------------------------------

def slugify_filename(filename):
    """Normalize a filename: remove accents, replace spaces, strip special chars."""
    name, _, ext = filename.rpartition('.')
    name = unicodedata.normalize('NFKD', name).encode('ascii', 'ignore').decode('ascii')
    name = re.sub(r'[^\w\s-]', '', name).strip()
    name = re.sub(r'[\s]+', '_', name)
    return f"{name}.{ext}" if ext else name


def deliverable_upload_to(instance, filename):
    slug = slugify_filename(filename)
    return f"{instance.project_id}/deliverables/{slug}"


def reference_upload_to(instance, filename):
    slug = slugify_filename(filename)
    return f"{instance.project_id}/references/{slug}"


ALLOWED_EXTENSIONS = {
    '.pdf', '.doc', '.docx', '.xls', '.xlsx',
    '.jpg', '.jpeg', '.png', '.gif',
    '.dwg', '.dxf', '.zip',
}


def is_allowed_file(filename):
    ext = os.path.splitext(filename)[1].lower()
    return ext in ALLOWED_EXTENSIONS


# ---------------------------------------------------------------------------
# Date helpers
# ---------------------------------------------------------------------------

def get_monday(d=None):
    """Return the Monday of the week containing date d (defaults to today)."""
    d = d or date.today()
    return d - timedelta(days=d.weekday())


def parse_monday(date_str):
    """Parse a YYYY-MM-DD string and snap it to its Monday."""
    try:
        d = date.fromisoformat(date_str)
        return get_monday(d)
    except (ValueError, TypeError):
        return get_monday()
