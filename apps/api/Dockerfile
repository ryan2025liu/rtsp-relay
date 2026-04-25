# [INPUT]: API source tree and requirements
# [OUTPUT]: Local relay-api image with Python runtime and ffmpeg installed
# [POS]: Container build definition for single-node local deployment
# [PROTOCOL]:
#   1. Keep image purpose limited to local API + worker execution.
#   2. Dependency/runtime changes must be reflected in README and compose docs.

FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends ffmpeg curl \
    && rm -rf /var/lib/apt/lists/*

COPY apps/api/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

COPY . /app

EXPOSE 18081

CMD ["python", "-m", "uvicorn", "apps.api.main:app", "--host", "0.0.0.0", "--port", "18081"]
