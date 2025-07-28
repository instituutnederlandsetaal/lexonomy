#!/bin/sh

NAME="${NAME:-lexonomy:latest}"
DATE="$(git log | head -n 3 | grep Date | cut -d ' ' -f '6,5,8' | tr ' ' .)"
GIT_TAG=$(git describe --exact-match --tags 2>/dev/null || git rev-parse --short HEAD) && \


VERSION="$DATE:$GIT_TAG"
docker build --build-arg VER="$VERSION" -t "$NAME" ."

