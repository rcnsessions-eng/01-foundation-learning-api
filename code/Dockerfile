FROM python:3.12.11-slim-bookworm AS runtime
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
COPY pyproject.toml requirements.lock ./
COPY app ./app
RUN pip install --no-cache-dir -c requirements.lock .
USER 10001:10001
EXPOSE 8000
CMD ["uvicorn", "app.main:create_app", "--factory", "--host", "0.0.0.0", "--port", "8000", "--no-access-log", "--log-level", "info"]

FROM runtime AS checks
USER root
COPY tests ./tests
RUN pip install --no-cache-dir -c requirements.lock ".[dev]"
USER 10001:10001
ENV MYPY_CACHE_DIR=/tmp/mypy RUFF_CACHE_DIR=/tmp/ruff
CMD ["sh", "-c", "ruff check app tests && ruff format --check app tests && mypy app && python -m pytest"]