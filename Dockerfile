FROM python:3.10-slim

LABEL maintainer="msuin"

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
      build-essential \
      libpq-dev \
      gcc \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /code

COPY requirements-prod.txt /code/requirements-prod.txt
RUN pip install --upgrade pip && \
    pip install -r /code/requirements-prod.txt

COPY . /code/

RUN mkdir -p /code/staticfiles && \
    python manage.py collectstatic --no-input

EXPOSE 8000

CMD ["gunicorn", "conf.wsgi:application", "--bind", "0.0.0.0:8000"]
