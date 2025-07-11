# syntax=docker/dockerfile:1
FROM python:3.10-slim

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN curl -sSL https://install.python-poetry.org | python3 - && \
    ln -s /root/.local/bin/poetry /usr/local/bin/poetry

# Set workdir
WORKDIR /app

# Copy pyproject.toml and poetry.lock
COPY pyproject.toml poetry.lock* ./

# Install dependencies
RUN poetry install --no-root --only main

# Install Playwright browsers
RUN poetry run playwright install --with-deps

# Copy the rest of the code
COPY . .

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Entrypoint
CMD ["poetry", "run", "python", "main.py"] 