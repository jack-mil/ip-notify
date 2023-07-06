#!/bin/sh
# Entrypoint into the docker container
# Only used for the docker image, ignore when running on host

# Copy the crontab into the bind mounted directory at runtime
# If the user hasn't overridden
[ -f /data/crontab ] || cp -a /tmp/crontab /data

# Install the crontab
crontab /data/crontab

# Execute once to ensure webhook working
python /app/ip_notify.py --test

# Then run the image CMD (crond -f)
exec "$@"