FROM node:22-alpine AS frontend
WORKDIR /opt/service/frontend

COPY frontend/package.json frontend/package-lock.json ./
RUN --mount=type=cache,target=/root/.npm npm ci
COPY frontend/ ./

ARG VER=dev
ARG GIT_REVISION
ARG GIT_MESSAGE
RUN VITE_LEXONOMY_VERSION="$VER" VITE_LEXONOMY_REVISION="$GIT_REVISION" \
    VITE_LEXONOMY_COMMIT_MESSAGE="$GIT_MESSAGE" npm run build

FROM python:3.12-alpine3.24 AS backend
WORKDIR /opt/service/api
ENV PYTHONDONTWRITEBYTECODE=1

RUN --mount=type=bind,source=api/requirements.txt,target=requirements.txt \
    apk add --no-cache icu-libs libxslt \
    && apk add --no-cache --virtual .build-deps g++ icu-dev libxslt-dev \
    && pip install --no-cache-dir -r requirements.txt \
    && apk del .build-deps

COPY api/lexonomy.py api/ops.py api/entryxml.py api/dictionary_document.py api/migrate.py api/siteconfig.py api/*.schema ./
COPY config/siteconfig.example.json /opt/service/siteconfig.example.json
COPY api/adminscripts/ ./adminscripts/
COPY api/dictTemplates/ ./dictTemplates/
COPY api/resources/ ./resources/

EXPOSE 8000
# Bottle/Paste handle SIGINT as a request to stop the server cleanly.
STOPSIGNAL SIGINT
CMD ["sh", "-c", "python adminscripts/init.py && python adminscripts/updates.py && python migrate.py && exec python lexonomy.py"]

FROM backend AS production
COPY --from=frontend /opt/service/frontend/dist /opt/service/frontend/dist

ARG VER=dev
RUN printf '%s\n' "$VER" > version.txt
