#!/bin/sh
# Fix ownership of the runtime volumes, then drop privileges.
#
# The image builds as root and chowns /app, but docker creates named volumes
# (media_data, static_data) as root at mount time — after that chown. The app
# runs as appuser, so saving an upload to /app/media raised PermissionError
# and surfaced as a 500 on the transfer-proof screen.
#
# This runs as root for exactly as long as it takes to chown those two
# directories, then execs the real command as appuser via gosu. Nothing in
# the application itself runs privileged.
set -eu

if [ "$(id -u)" = "0" ]; then
    mkdir -p /app/media /app/staticfiles
    chown -R appuser:appuser /app/media /app/staticfiles
    exec gosu appuser "$@"
fi

exec "$@"
