# Paperclip 2026.916.1, resolved from the public release tag on 2026-09-22.
# Keep the upstream entrypoint (tini, volume ownership, unprivileged server).
FROM ghcr.io/paperclipai/paperclip@sha256:a02ac35ac41df911af477422ea0e781cf41d2b2c600c66f0a5ac9d8c63f52c2c

ENV PAPERCLIP_DEPLOYMENT_MODE=authenticated \
    PAPERCLIP_DEPLOYMENT_EXPOSURE=public \
    PAPERCLIP_BIND=custom \
    PAPERCLIP_BIND_HOST=0.0.0.0 \
    HOST=0.0.0.0 \
    PORT=3100 \
    PAPERCLIP_HOME=/paperclip \
    HEARTBEAT_SCHEDULER_ENABLED=false \
    DO_NOT_TRACK=1
