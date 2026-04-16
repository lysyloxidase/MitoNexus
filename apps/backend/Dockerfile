FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app/apps/backend/src

WORKDIR /app/apps/backend

COPY apps/backend/pyproject.toml ./pyproject.toml
COPY apps/backend/README.md ./README.md
COPY apps/backend/src ./src

RUN pip install --no-cache-dir .

EXPOSE 8000

CMD ["uvicorn", "mitonexus.main:app", "--host", "0.0.0.0", "--port", "8000"]
