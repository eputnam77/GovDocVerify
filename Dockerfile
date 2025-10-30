# Use the latest stable Python base image that receives timely security fixes for PCRE2.
# The previous release-candidate image shipped libpcre2-8 10.45, which was affected by
# CVE-2025-58050. Moving to the maintained bookworm-based Python 3.12 image ensures the
# container picks up the patched Debian security update while keeping us on the supported
# interpreter version for the project.
FROM python:3.12.5-slim-bookworm

WORKDIR /app

# Install system dependencies and pull in the patched libgnutls30 build to
# address CVE-2024-0553 (double-free in certificate handling).
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    libgnutls30 \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN curl -sSL https://install.python-poetry.org | python3 -

# Copy poetry files
COPY pyproject.toml poetry.lock ./

# Install Python dependencies
RUN poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-ansi

# Copy the rest of the application
COPY . .

# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Expose the port the app runs on
EXPOSE 7860

# Command to run the application
CMD ["poetry", "run", "python", "-m", "govdocverify.app"] 