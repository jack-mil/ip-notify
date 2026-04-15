#!/bin/sh

set -eu

mkdir -p /data

CRONTAB_FILE="/tmp/ip-notify.crontab"
JOB_COMMAND="python /app/ip_notify.py"

cat > "${CRONTAB_FILE}" <<EOF
${SCHEDULE} ${JOB_COMMAND}
EOF

# Execute once on start to test webhook
python /app/ip_notify.py --test

# Execute supercronic daemon
exec /usr/local/bin/supercronic "${CRONTAB_FILE}"
