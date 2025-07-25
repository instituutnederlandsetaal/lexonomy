# syntax=docker/dockerfile:1.7-labs

FROM node:23-alpine AS builder
ARG VER

WORKDIR /opt/service

RUN apk add --no-cache git

COPY .git .git
COPY --exclude=*.py website website 
WORKDIR /opt/service/website

# Get current git tag/commit hash (if no tag), and put in version.txt in /opt/service/website
RUN VERSION=$(git describe --exact-match --tags 2>/dev/null || git rev-parse --short HEAD) && \
echo "$VERSION" > version.txt


# Install dependencies for main website and vue-based editor with cache mounts
RUN --mount=type=cache,target=/opt/service/website/node_modules \
    npm ci
RUN --mount=type=cache,target=/opt/service/website/editor/node_modules \
    npm --prefix editor ci
# builds both editor and riot templates, output in website/dist
RUN --mount=type=cache,target=/opt/service/website/node_modules \
    --mount=type=cache,target=/opt/service/website/editor/node_modules \
    npm run build

FROM python:3.12-alpine

ARG VER

WORKDIR /opt/service/

COPY ./website/requirements.txt requirements.txt
RUN apk add --no-cache --virtual .build-deps gcc g++ libxslt-dev libffi-dev openssl-dev icu-dev && \ 
    apk add --no-cache libxml2 libxslt libffi openssl icu && \
    apk add --no-cache sqlite && \
    apk add --no-cache openjdk11-jre  $(: for Naisc ) && \
    pip install --no-cache-dir -r requirements.txt && \
    apk del .build-deps && \
    [ -z "$VER" ] || echo "$VER" > version.txt

COPY . /opt/service/
COPY --from=builder /opt/service/website/dist /opt/service/website/dist
# NOTE minor path difference here
# Builder puts version outside website dir to improve caching of image layers
COPY --from=builder /opt/service/website/version.txt /opt/service/website/version.txt

RUN sed -i -e "s/@VERSION@/$(cat /opt/service/website/version.txt)/g" /opt/service/website/index*html

WORKDIR /opt/service/website


# RUN pip install debugpy
# ENTRYPOINT ["/bin/sh", "-c", "python3 adminscripts/init.py && python3 adminscripts/updates.py && python3 migrate.py && debugpy --listen 0.0.0.0:5678 --wait-for-client lexonomy.py 0.0.0.0:8000"]

ENTRYPOINT ["/bin/sh", "-c", "python3 adminscripts/init.py && python3 adminscripts/updates.py && python3 migrate.py && python lexonomy.py 0.0.0.0:8000"]
