FROM python:3.12.10-alpine3.21
RUN apk add --no-cache --update redis

RUN --mount=type=bind,source=requirements.txt,target=/tmp/requirements.txt \
    pip install --requirement /tmp/requirements.txt

COPY . /app
WORKDIR /app

RUN chmod +x /app/start.sh
CMD ["/app/start.sh"]