FROM node:22-alpine AS frontend
WORKDIR /opt/service/website

COPY website/package.json website/package-lock.json ./
RUN --mount=type=cache,target=/root/.npm npm ci
COPY website/ ./

ARG VER=dev
RUN VITE_LEXONOMY_VERSION="$VER" npm run build

FROM python:3.12-alpine3.24 AS backend
WORKDIR /opt/service/website

COPY website/requirements.txt ./
RUN apk add --no-cache icu libxslt \
    && apk add --no-cache --virtual .build-deps g++ icu-dev libxslt-dev \
    && pip install --no-cache-dir -r requirements.txt \
    && apk del .build-deps

COPY website/ ./
RUN mkdir -p ../data && cp siteconfig.json.template siteconfig.json

EXPOSE 8000
CMD ["sh", "-c", "python adminscripts/init.py && python adminscripts/updates.py && python migrate.py && exec python lexonomy.py 0.0.0.0:8000"]

FROM backend AS production
COPY --from=frontend /opt/service/website/dist ./dist

ARG VER=dev
RUN printf '%s\n' "$VER" > version.txt
