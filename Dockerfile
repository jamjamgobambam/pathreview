# Stage 1: Build
FROM python:3.11-slim as builder

WORKDIR /app
COPY pyproject.toml .
RUN pip install --no-cache-dir build && \
    pip install --no-cache-dir .

# Stage 2: Runtime
FROM python:3.11-slim

WORKDIR /app
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin
COPY . .

EXPOSE 8000

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
