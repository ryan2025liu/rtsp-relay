#!/bin/sh
# [INPUT]: RTSP_URL; optional RTMP_OUT or (RTMP_BASE + STREAM_ID); optional FFMPEG_EXTRA_ARGS, FFMPEG_LOGLEVEL
#          TRANSCODE_H264=1 — re-encode to H.264/AAC for HTTP-FLV + flv.js (H.265 RTMP often breaks SRS FLV mux)
# [OUTPUT]: Long-running ffmpeg pushing to SRS
# [POS]: Container entrypoint for rtsp-relay image
# [PROTOCOL]: Logic change → update this header and ../.folder.md

set -eu

log() {
  printf '%s %s\n' "$(date -u +"%Y-%m-%dT%H:%M:%SZ")" "$*"
}

if [ -z "${RTSP_URL:-}" ]; then
  log "WARN: RTSP_URL is empty; idling (sleep). Set RTSP_URL and recreate this container."
  exec sleep infinity
fi

# ffmpeg requires a scheme; allow "user:pass@host:554/path" from operators who omit rtsp://
case "${RTSP_URL}" in
  *://*) ;;
  *)
    RTSP_URL="rtsp://${RTSP_URL}"
    log "INFO: prepended rtsp:// (no scheme in RTSP_URL)."
    ;;
esac

RTMP_TARGET=""
if [ -n "${RTMP_OUT:-}" ]; then
  RTMP_TARGET="${RTMP_OUT}"
else
  if [ -z "${STREAM_ID:-}" ]; then
    log "ERROR: Set RTMP_OUT or STREAM_ID (with RTMP_BASE)"
    exit 1
  fi
  BASE="${RTMP_BASE:-rtmp://localhost:1935/live}"
  # trim trailing slash on BASE then append /STREAM_ID
  BASE="${BASE%/}"
  RTMP_TARGET="${BASE}/${STREAM_ID}"
fi

LOGLEVEL="${FFMPEG_LOGLEVEL:-info}"
EXTRA="${FFMPEG_EXTRA_ARGS:-}"

# Avoid leaking credentials into logs: show scheme + host only when possible
case "${RTSP_URL}" in
  *://*@*)
    SAFE_RTSP="(redacted RTSP URL)"
    ;;
  *)
    SAFE_RTSP="${RTSP_URL}"
    ;;
esac

log "Starting ffmpeg: input=${SAFE_RTSP} output_rtmp=${RTMP_TARGET}"

transcode_h264() {
  case "${TRANSCODE_H264:-}" in
    1|true|TRUE|yes|YES) return 0 ;;
    *) return 1 ;;
  esac
}

if transcode_h264; then
  log "INFO: TRANSCODE_H264 on — output H.264/AAC (browser-friendly FLV)."
  # shellcheck disable=SC2086
  exec ffmpeg -hide_banner -loglevel "${LOGLEVEL}" \
    -rtsp_transport tcp \
    -i "${RTSP_URL}" \
    -c:v libx264 -preset veryfast -tune zerolatency -pix_fmt yuv420p \
    -g 50 -keyint_min 50 -sc_threshold 0 \
    -c:a aac -b:a 64k \
    -f flv \
    ${EXTRA} \
    "${RTMP_TARGET}"
else
  # shellcheck disable=SC2086
  exec ffmpeg -hide_banner -loglevel "${LOGLEVEL}" \
    -rtsp_transport tcp \
    -i "${RTSP_URL}" \
    -c copy \
    -f flv \
    ${EXTRA} \
    "${RTMP_TARGET}"
fi
