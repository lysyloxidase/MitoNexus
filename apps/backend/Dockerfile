FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app/apps/backend/src

WORKDIR /app/apps/backend

RUN pip install --no-cache-dir \
    "fastapi>=0.115.0" \
    "uvicorn[standard]>=0.32.0" \
    "pydantic>=2.10.0" \
    "pydantic-settings>=2.6.0"

COPY apps/backend/src ./src

EXPOSE 8000

CMD ["uvicorn", "mitonexus.main:app", "--host", "0.0.0.0", "--port", "8000"]
