FROM python:3.11-slim

WORKDIR /app

# Non-root user
RUN adduser --disabled-password --gecos "" appuser

# Install dependencies
COPY pyproject.toml ./
RUN pip install --no-cache-dir -e .

# Application code
COPY src/ ./src/
COPY scripts/ ./scripts/

USER appuser

ENV PORT=8080
EXPOSE 8080

# Default: run bot (webhook or polling via BOT_MODE)
CMD ["python", "-m", "src.main"]
