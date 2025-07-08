FROM node:23-alpine AS builder

ARG VER

COPY ./website /opt/service/website

WORKDIR /opt/service/website
RUN npm ci

WORKDIR /opt/service/website/editor
RUN npm ci

# builds both editor and riot templates, output in website/dist
WORKDIR /opt/service/website
RUN npm run build 

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

RUN sed -i -e "s/@VERSION@/${VER}/g" /opt/service/website/index*html


ENTRYPOINT ["python3", "lexonomy.py", "0.0.0.0:8000"]
