# Phase 18 Single-Node Wazuh Lab Bundle

This directory contains the reviewed repository-local assets for the Phase 18 single-node Wazuh lab target.

It exists to make one explicit substrate package available for the first live path:

`single-node Wazuh lab target -> reviewed reverse proxy -> bootable AegisOps control-plane runtime boundary -> PostgreSQL-backed control-plane state`

GitHub audit remains the only approved first live source family for this slice.

This bundle is not an approved production deployment.

Use the files here as reviewed scaffolding only:

- `docker-compose.yml` keeps the Wazuh manager, indexer, and dashboard topology explicit for lab review.
- `bootstrap.env.sample` lists the reviewed non-secret inputs that operators must supply in an untracked env file.
- `ossec.integration.sample.xml` shows the reviewed custom integration shape for `Wazuh -> AegisOps`.

Operator expectations:

- Keep the AegisOps ingress target on the reviewed reverse proxy HTTPS path.
- Keep the shared bearer secret in an untracked secret file.
- Keep GitHub audit as the only approved first live family.
- Keep the bundle narrow and reviewable.

This bundle must not publish the control-plane backend port directly, must not route first live traffic through Shuffle or n8n, and must not be treated as approval for multi-node or production-scale Wazuh.
