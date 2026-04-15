FROM python:3.14-alpine

LABEL org.container.author="https://codeberg.org/jack-mil/ip-notify"

# Latest releases available at https://github.com/aptible/supercronic/releases
ENV SUPERCRONIC_URL=https://github.com/aptible/supercronic/releases/download/v0.2.44/supercronic-linux-amd64 \
    SUPERCRONIC_SHA1SUM=6eb0a8e1e6673675dc67668c1a9b6409f79c37bc \
    SUPERCRONIC=supercronic-linux-amd64

RUN apk add --no-cache ca-certificates curl tzdata

RUN curl -fsSLO "$SUPERCRONIC_URL" \
 && echo "${SUPERCRONIC_SHA1SUM}  ${SUPERCRONIC}" | sha1sum -c - \
 && chmod +x "$SUPERCRONIC" \
 && mv "$SUPERCRONIC" "/usr/local/bin/${SUPERCRONIC}" \
 && ln -s "/usr/local/bin/${SUPERCRONIC}" /usr/local/bin/supercronic


WORKDIR /app
COPY --chmod=755 entrypoint.sh .
COPY ip_notify.py .

ENV EMBED_COLOR="f1c40f" \
    IP_CACHE="/data/ip" \
    LOG_FILE="/data/ip-notify.log" \
    SCHEDULE="*/30 * * * *"

ENTRYPOINT ["./entrypoint.sh"]
