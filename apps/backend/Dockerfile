FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app/apps/backend/src

WORKDIR /app/apps/backend

RUN apt-get update \
    && apt-get install --yes --no-install-recommends \
        libcairo2 \
        libfontconfig1 \
        libgdk-pixbuf-2.0-0 \
        libglib2.0-0 \
        libharfbuzz0b \
        libjpeg62-turbo \
        libpango-1.0-0 \
        libpangocairo-1.0-0 \
        shared-mime-info \
    && rm -rf /var/lib/apt/lists/*

COPY apps/backend/pyproject.toml ./pyproject.toml
COPY apps/backend/README.md ./README.md
COPY apps/backend/alembic.ini ./alembic.ini
COPY apps/backend/alembic ./alembic
COPY apps/backend/scripts ./scripts
COPY apps/backend/src ./src

RUN pip install --no-cache-dir .

EXPOSE 8000

CMD ["uvicorn", "mitonexus.main:app", "--host", "0.0.0.0", "--port", "8000"]
