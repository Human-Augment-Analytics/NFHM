ARG PY_VERSION=3
FROM mcr.microsoft.com/devcontainers/python:$PY_VERSION
COPY ./backend/requirements.txt /tmp/pip-tmp/
RUN pip3 --disable-pip-version-check --no-cache-dir install -r /tmp/pip-tmp/requirements.txt \
    && rm -rf /tmp/pip-tmp

# TODO: We should probably have a separate namespace for ingestor dependencies
# to keep them sequestered from the backend dependencies.
# One possibility is to have an entirely seperate container & dockerfile for the ingestor
# But for now we can just install the ingestor dependencies in the same container since they are not conflicting,
# and it's simpler
COPY ./ingestor/requirements.txt /tmp/pip-tmp/
RUN pip3 --disable-pip-version-check --no-cache-dir install -r /tmp/pip-tmp/requirements.txt \
    && rm -rf /tmp/pip-tmp
