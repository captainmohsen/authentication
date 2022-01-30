FROM python:3.10

ENV PYTHONUNBUFFERED 1
ENV PYTHONDONTWRITEBYTECODE 1


RUN apt update \
  # dependencies for building Python packages
  && apt install -y build-essential \
  # mariadb dependencies
  && apt install -y libmariadb-dev \
  # Translations dependencies
  && apt install -y gettext \
  # cleaning up unused files
  && apt purge -y --auto-remove -o APT::AutoRemove::RecommendsImportant=false \
  && rm -rf /var/lib/apt/lists/*

# Copy source files
COPY . /authentication

# Requirements are installed here to ensure they will be cached.
RUN pip install -r /authentication/requirements/development.txt

COPY ./compose/development/entrypoint /entrypoint
RUN sed -i 's/\r$//g' /entrypoint && \
    chmod +x /entrypoint

COPY ./compose/development/start-authentication /start-authentication
RUN sed -i 's/\r$//g' /start-authentication && \
    chmod +x /start-authentication

COPY ./compose/development/start-celery-worker /start-celery-worker
RUN sed -i 's/\r$//g' /start-celery-worker && \
    chmod +x /start-celery-worker

COPY ./compose/development/start-celery-beat /start-celery-beat
RUN sed -i 's/\r$//g' /start-celery-beat && \
    chmod +x /start-celery-beat

COPY ./compose/development/start-celery-flower /start-celery-flower
RUN sed -i 's/\r$//g' /start-celery-flower && \
    chmod +x /start-celery-flower

WORKDIR /authentication

ENTRYPOINT ["/entrypoint"]
