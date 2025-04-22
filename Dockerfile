# 1) «легковесный» образ с Python 3.13
FROM python:3.13-slim

# 2) Автор и метаданные
LABEL maintainer="msuin"

# 3) Системные переменные, чтобы Python не кешировал .pyc и не буферизовал вывод
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# 4) Обновляем apt и ставим нужные библиотеки для сборки зависимостей
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
      build-essential \
      libpq-dev \
      gcc \
    && rm -rf /var/lib/apt/lists/*

# 5) Создаём рабочую директорию внутри контейнера
WORKDIR /code

# 6) Копируем файл с зависимостями и устанавливаем их
#    это гарантирует, что при изменении кода Docker пересоберёт только
#    слои с кодом, а зависимости будут кешироваться
COPY requirements.txt /code/
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# 7) Копируем в контейнер весь исходный код проекта
COPY . /code/

# 8) Собираем статику (если используешь collectstatic и WhiteNoise или аналог)
RUN python manage.py collectstatic --no-input

# 9) Открываем порт 8000
EXPOSE 8000

# 10) По умолчанию запускаем Gunicorn — более «продакшн‑готовый» WSGI‑сервер
CMD ["gunicorn", "conf.wsgi:application", "--bind", "0.0.0.0:8000"]
