FROM python:3.8.1-alpine
WORKDIR /usr/src/app
RUN set -eux \
    && apk add --no-cache --virtual .build-deps build-base \
        libressl-dev libffi-dev gcc musl-dev python3-dev \
        mariadb-dev mariadb-client \
    && pip install --upgrade pip setuptools wheel \
    && rm -rf /root/.cache/pip
COPY ./requirements.txt /usr/src/app/requirements.txt
RUN set -eux\
    && pip install -r /usr/src/app/requirements.txt \
    && rm -rf /root/.cache/pip
COPY . /usr/src/app
RUN rm -f /usr/src/app/words.json && rm -f /usr/src/app/quotes.json && rm -f /usr/src/app/perd.json
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
CMD ["python3", "-u", "moonbeam-bot.py"]
