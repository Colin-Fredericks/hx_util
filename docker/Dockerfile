#
# based on the Dockerfile from https://github.com/dteslya/blog-dockerize-python-cli-tool
#

ARG APP_NAME=hx_util
ARG APP_PATH=/opt/$APP_NAME
ARG PYTHON_VERSION=3.12.7

#
# Stage: staging
#
FROM python:$PYTHON_VERSION-slim AS staging
ARG APP_NAME
ARG APP_PATH

ENV \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONFAULTHANDLER=1

RUN apt-get update && apt-get upgrade -y \
    && apt-get install --no-install-recommends -y \
        curl \
        build-essential

RUN pip install uv


# Import our project files
WORKDIR $APP_PATH
COPY . .

#
# Stage: build
#
FROM staging AS build
ARG APP_PATH

# create venv and make it the default python
# need pip to display version of package
ENV VENV_PATH=$APP_PATH/venv
WORKDIR $APP_PATH
RUN uv venv $VENV_PATH
ENV PATH="$VENV_PATH/bin:$PATH"
RUN uv pip install --upgrade pip
RUN uv pip install -r ./requirements.txt
RUN uv pip install .

#
# Stage: production
#
FROM python:$PYTHON_VERSION-slim AS production
ARG APP_NAME
ARG APP_PATH

ENV \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONFAULTHANDLER=1

RUN apt-get update && apt-get upgrade -y \
    && apt-get install --no-install-recommends -y tini \
    && apt-get clean

RUN useradd --create-home app

ENV VENV_PATH="$APP_PATH/venv"

# copy venv
WORKDIR $VENV_PATH
COPY --from=build --chown=app:app $VENV_PATH .

ENV PATH="$APP_PATH/venv/bin:$PATH"

# Entrypoint script
COPY --chmod=775 ./docker/wrapper_hx_util.sh ./bin/wrapper_hx_util.sh

# run as unprivileged user
USER app

WORKDIR $VENV_PATH/bin
ENTRYPOINT ["tini", "-g", "--" ]
