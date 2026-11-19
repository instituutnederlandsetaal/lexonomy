FROM node:22-alpine AS frontend
WORKDIR /opt/service/frontend

COPY frontend/package.json frontend/package-lock.json ./
RUN --mount=type=cache,target=/root/.npm npm ci
COPY frontend/ ./

ARG VER=dev
RUN VITE_LEXONOMY_VERSION="$VER" npm run build

FROM python:3.12-alpine3.24 AS backend
WORKDIR /opt/service/api
ENV PYTHONDONTWRITEBYTECODE=1

RUN --mount=type=bind,source=api/requirements.txt,target=requirements.txt \
    apk add --no-cache icu-libs libxslt \
    && apk add --no-cache --virtual .build-deps g++ icu-dev libxslt-dev \
    && pip install --no-cache-dir -r requirements.txt \
    && apk del .build-deps

COPY api/lexonomy.py api/ops.py api/migrate.py api/siteconfig.py api/*.schema ./
COPY config/siteconfig.example.json /opt/service/siteconfig.example.json
COPY api/adminscripts/ ./adminscripts/
COPY api/dictTemplates/ ./dictTemplates/
COPY api/resources/ ./resources/

EXPOSE 8000
CMD ["sh", "-c", "python adminscripts/init.py && python adminscripts/updates.py && python migrate.py && exec python lexonomy.py 0.0.0.0:8000"]

FROM backend AS production
COPY --from=frontend /opt/service/frontend/dist /opt/service/frontend/dist

ARG VER=dev
RUN printf '%s\n' "$VER" > version.txt
