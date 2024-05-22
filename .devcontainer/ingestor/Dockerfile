ARG PY_VERSION=3
FROM mcr.microsoft.com/devcontainers/python:$PY_VERSION
COPY ./ingestor/requirements.txt /tmp/pip-tmp/
RUN pip3 --disable-pip-version-check --no-cache-dir install -r /tmp/pip-tmp/requirements.txt \
    && rm -rf /tmp/pip-tmp
