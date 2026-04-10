# Phase 18 Single-Node Wazuh Lab Bundle

This directory contains the reviewed repository-local assets for the Phase 18 single-node Wazuh lab target.

It exists to make one explicit substrate package available for the first live path:

`single-node Wazuh lab target -> reviewed reverse proxy -> bootable AegisOps control-plane runtime boundary -> PostgreSQL-backed control-plane state`

GitHub audit remains the only approved first live source family for this slice.

This bundle is not an approved production deployment.

Use the files here as reviewed scaffolding only:

- `docker-compose.yml` keeps the Wazuh manager, indexer, and dashboard topology explicit for lab review while leaving service interfaces internal-only.
- `bootstrap.env.sample` lists the reviewed non-secret inputs that operators must supply in an untracked env file.
- `ossec.integration.sample.xml` keeps the reviewed custom integration template shape for `Wazuh -> AegisOps`.
- `render-ossec-integration.sh` reads `AEGISOPS_WAZUH_AEGISOPS_SHARED_SECRET_FILE`, materializes `AEGISOPS_WAZUH_AEGISOPS_SHARED_SECRET`, and renders literal `<hook_url>` and `<api_key>` values before operators load the integration into Wazuh.

Operator expectations:

- Keep the AegisOps ingress target on the reviewed reverse proxy HTTPS path.
- Keep the shared bearer secret in an untracked secret file.
- Run `render-ossec-integration.sh` in the manager container or another shell where `AEGISOPS_WAZUH_AEGISOPS_SHARED_SECRET_FILE` resolves to the mounted secret path so the helper can populate the template’s `AEGISOPS_WAZUH_AEGISOPS_SHARED_SECRET` placeholder before copying the integration block into active Wazuh config.
- Keep GitHub audit as the only approved first live family.
- Keep service interfaces internal-only unless a separate reviewed lab access path is supplied.
- Keep the bundle narrow and reviewable.

This bundle must not publish the control-plane backend port directly, must not route first live traffic through Shuffle or n8n, and must not be treated as approval for multi-node or production-scale Wazuh.
