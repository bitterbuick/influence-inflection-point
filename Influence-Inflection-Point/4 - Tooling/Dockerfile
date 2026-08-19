# syntax=docker/dockerfile:1
#
# corpus-presence-tracker — reproducible container for the infini-gram corpus
# presence tracker (Influence Inflection Point project).
#
# Build context is this folder ("4 - Tooling"). The .dockerignore keeps the
# context to just the script + requirements, so the image is small and stable.
#
#   docker build -t corpus-presence-tracker:1.1 .
#   docker run --rm -v "${PWD}/io:/data" corpus-presence-tracker:1.1 --list-indexes
#
# For full bit-for-bit reproducibility, pin the base image by digest:
#   FROM python:3.12-slim-bookworm@sha256:<digest-from-your-pull>

FROM python:3.12-slim-bookworm

LABEL org.opencontainers.image.title="corpus-presence-tracker"
LABEL org.opencontainers.image.description="infini-gram exact-match corpus presence tracker (Influence Inflection Point project)"
LABEL org.opencontainers.image.version="1.1"
LABEL org.opencontainers.image.licenses="MIT"

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Pinned dependency layer (cache-friendly; rebuilds only when requirements change).
COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

# Run as a non-root user.
RUN useradd --create-home --uid 10001 runner

# Application code.
COPY corpus_presence_tracker.py /app/corpus_presence_tracker.py

# /data is the persistent mount point for inputs (entities CSVs) and outputs (runs).
RUN mkdir -p /data && chown -R runner:runner /data /app
VOLUME ["/data"]
WORKDIR /data

USER runner
ENTRYPOINT ["python", "/app/corpus_presence_tracker.py"]
# Safe default when run with no arguments (no network call).
CMD ["--help"]
