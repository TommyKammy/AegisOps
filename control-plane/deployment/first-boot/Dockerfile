FROM python:3.12-slim-bookworm@sha256:d50fb7611f86d04a3b0471b46d7557818d88983fc3136726336b2a4c657aa30b

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update \
    && apt-get install -y --no-install-recommends postgresql-client \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir "psycopg[binary]>=3.2,<3.3"
RUN groupadd --system aegisops \
    && useradd --system --create-home --gid aegisops --home-dir /var/lib/aegisops --shell /usr/sbin/nologin aegisops \
    && mkdir -p /opt/aegisops/bin /opt/aegisops/control-plane /opt/aegisops/postgres-migrations \
    && chown -R aegisops:aegisops /opt/aegisops

WORKDIR /opt/aegisops/control-plane

COPY --chown=aegisops:aegisops control-plane /opt/aegisops/control-plane
COPY --chown=aegisops:aegisops postgres/control-plane/migrations /opt/aegisops/postgres-migrations
COPY --chown=aegisops:aegisops control-plane/deployment/first-boot/control-plane-entrypoint.sh /opt/aegisops/bin/first-boot-entrypoint.sh

RUN chmod 0555 /opt/aegisops/bin/first-boot-entrypoint.sh
USER aegisops:aegisops

ENTRYPOINT ["/opt/aegisops/bin/first-boot-entrypoint.sh"]
CMD ["python3", "main.py", "serve"]
