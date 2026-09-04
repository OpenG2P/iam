FROM python:3.12.11-alpine3.22

# External OpenG2P library ref (not part of this repo). Override via build-arg /
# workflow input. The IAM code (iam-core + the portal api) is installed from
# the LOCAL in-repo source, so the image always reflects the current branch.
ARG FASTAPI_COMMON_REF=1.2.1

RUN apk add --no-cache --virtual .build-deps gcc libc-dev linux-headers make \
 && apk add --no-cache bash git gettext libpq-dev libmagic

WORKDIR /app

# External libs (openg2p-fastapi-common)
RUN pip install --no-cache-dir \
    "git+https://github.com/openg2p/openg2p-fastapi-common@${FASTAPI_COMMON_REF}#subdirectory=openg2p-fastapi-common"

# Local IAM source (build context = repo root). iam-core must be installed
# before the portal api, which depends on it. Remaining deps resolve from PyPI
# via each package's pyproject.
COPY iam-core /src/iam-core
COPY iam-staff-portal-api /src/iam-staff-portal-api
RUN pip install --no-cache-dir /src/iam-core /src/iam-staff-portal-api

RUN apk del --no-network .build-deps

ENV PYTHONUNBUFFERED=1
ENV IAM_API_NO_OF_WORKERS=2
ENV IAM_API_HOST=0.0.0.0
ENV IAM_API_PORT=8000
ENV IAM_API_WORKER_TYPE=gunicorn

# Run DB migrations, then start Gunicorn with Uvicorn workers
CMD python3 -m iam_staff_portal_api.main migrate; \
    gunicorn "iam_staff_portal_api.main:app" --workers ${IAM_API_NO_OF_WORKERS} --worker-class uvicorn.workers.UvicornWorker --bind ${IAM_API_HOST}:${IAM_API_PORT}
