FROM python:3.11-alpine

LABEL org.container.author="https://github.com/jack-mil"

# crond already installed but we can remove default
RUN apk add --no-cache tini
RUN rm -rf /etc/periodic /etc/crontabs/root

# Install python reqs
WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt
COPY ip_notify.py .

# Copy entrypoint
COPY --chmod=744 entrypoint.sh .

# Copy crontab config to be installed at runtime by script
WORKDIR /tmp
COPY crontab .

# Set default environment
ENV EMBED_COLOR="f1c40f"
ENV IP_CACHE="/data/ip.txt"

ENTRYPOINT ["/sbin/tini", "--", "/app/entrypoint.sh"]

# CMD ["python3", "/app/ip_notify.py"]
CMD ["crond", "-f", "-l", "0"]