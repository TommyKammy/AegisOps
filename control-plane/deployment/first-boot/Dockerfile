FROM python:3.12-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update \
    && apt-get install -y --no-install-recommends postgresql-client \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir "psycopg[binary]>=3.2,<3.3"

WORKDIR /opt/aegisops/control-plane

COPY control-plane /opt/aegisops/control-plane
COPY postgres/control-plane/migrations /opt/aegisops/postgres-migrations
COPY control-plane/deployment/first-boot/control-plane-entrypoint.sh /opt/aegisops/bin/first-boot-entrypoint.sh

RUN chmod 0555 /opt/aegisops/bin/first-boot-entrypoint.sh

ENTRYPOINT ["/opt/aegisops/bin/first-boot-entrypoint.sh"]
CMD ["python3", "main.py", "serve"]
