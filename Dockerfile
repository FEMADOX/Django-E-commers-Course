# Pull from Image
FROM python:3.13-slim-bookworm

# Set ENVIROMENT variables
ENV PIP_DISABLE_PIP_VERSION_CHECK=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Script start
RUN mkdir scripts
COPY ./start.sh /scripts/start.sh
RUN chmod +x /scripts/start.sh

# Set WORK directory
WORKDIR /app

# Install dependencies
RUN pip install uv
# COPY pyproject.toml .
COPY . .
RUN uv sync --link-mode symlink

# Setting Path ENV
ENV PATH="/app/.venv/bin:$PATH"
