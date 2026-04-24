# [INPUT]: Build context (Alpine + ffmpeg)
# [OUTPUT]: Image skybrain/rtsp-relay:local (or tagged)
# [POS]: RTSP pull → RTMP push to SRS for external SkyBrain streams
# [PROTOCOL]:
#   1. Change entrypoint behavior → update entrypoint.sh and this comment
#   2. Change compose wiring → update ../docker-compose.yml and docs

FROM alpine:3.20

RUN apk add --no-cache ffmpeg tini ca-certificates \
    && rm -rf /var/cache/apk/*

COPY entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh

ENTRYPOINT ["/sbin/tini", "--", "/usr/local/bin/entrypoint.sh"]
