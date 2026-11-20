FROM python:3.12.11-alpine3.22

ARG FASTAPI_COMMON_REF=1.3

RUN apk add --no-cache --virtual .build-deps gcc libc-dev linux-headers make \
 && apk add --no-cache bash git gettext libpq-dev libffi-dev openssl-dev

WORKDIR /app

RUN pip install --no-cache-dir \
    "git+https://github.com/openg2p/openg2p-fastapi-common@${FASTAPI_COMMON_REF}#subdirectory=openg2p-fastapi-common"

COPY iam-core /src/iam-core
COPY celery/openg2p-iam-celery-worker /src/openg2p-iam-celery-worker
COPY celery/openg2p-iam-celery-beat /src/openg2p-iam-celery-beat
RUN pip install --no-cache-dir /src/iam-core /src/openg2p-iam-celery-worker /src/openg2p-iam-celery-beat

RUN apk del --no-network .build-deps

ENV PYTHONUNBUFFERED=1
ENV CELERY_APP=openg2p_iam_celery_worker.main:celery_app
ENV CELERY_OPTS="worker --loglevel=info -Q iam_celery"

COPY docker/iam-celery/run_celery.py /app/run_celery.py

CMD ["python3", "/app/run_celery.py"]
