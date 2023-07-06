FROM python:3.11-alpine

LABEL org.container.author="https://github.com/jack-mil"

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY --chmod=744 entrypoint.sh .
COPY ip_notify.py .

WORKDIR /tmp
COPY crontab .

WORKDIR /

ENV EMBED_COLOR="f1c40f"
ENV IP_CACHE="/data/ip.txt"

ENTRYPOINT ["/app/entrypoint.sh"]

# CMD ["python3", "/app/ip_notify.py"]
CMD ["crond", "-f"]