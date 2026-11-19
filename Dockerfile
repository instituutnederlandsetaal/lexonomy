FROM node:22-alpine AS builder
WORKDIR /opt/service/website

COPY website/package.json website/package-lock.json ./
COPY website/editor/package.json website/editor/package-lock.json ./editor/
RUN --mount=type=cache,target=/root/.npm npm ci && npm --prefix editor ci

COPY website/ ./
RUN npm run build

FROM python:3.12-alpine3.24
WORKDIR /opt/service/website

COPY website/requirements.txt ./
RUN apk add --no-cache icu libxslt \
    && apk add --no-cache --virtual .build-deps g++ icu-dev libxslt-dev \
    && pip install --no-cache-dir -r requirements.txt \
    && apk del .build-deps

COPY website/ ./
COPY --from=builder /opt/service/website/dist ./dist

ARG VER=dev
RUN case "$VER" in \
        ''|*[!A-Za-z0-9_.-]*) echo 'VER must contain letters, digits, dots, underscores, or hyphens only' >&2; exit 1 ;; \
    esac \
    && mkdir -p ../data \
    && cp siteconfig.json.template siteconfig.json \
    && cp config.js.template config.js \
    && printf '%s\n' "$VER" > version.txt \
    && sed -i "s/@VERSION@/$VER/g" index.html

EXPOSE 8000
CMD ["sh", "-c", "python adminscripts/init.py && python adminscripts/updates.py && python migrate.py && exec python lexonomy.py 0.0.0.0:8000"]
