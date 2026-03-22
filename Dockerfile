FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN pip install --upgrade pip

COPY ciau/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt gunicorn

COPY ciau/ .

RUN python manage.py collectstatic --noinput

EXPOSE 8000

CMD ["gunicorn", "ciau.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "2"]
