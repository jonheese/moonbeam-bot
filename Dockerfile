FROM python:alpine
WORKDIR /usr/src/app
RUN set -eux \
    && apk add --no-cache --virtual .build-deps build-base \
        libffi-dev gcc musl-dev python3-dev \
        mariadb-dev mariadb-client tzdata \
    && pip install --upgrade pip setuptools wheel \
    && rm -rf /root/.cache/pip
COPY ./requirements.txt /usr/src/app/requirements.txt
RUN set -eux\
    && pip install --root-user-action=ignore -r /usr/src/app/requirements.txt \
    && rm -rf /root/.cache/pip
COPY . /usr/src/app
RUN rm -f /usr/src/app/words.json && rm -f /usr/src/app/quotes.json && rm -f /usr/src/app/perd.json
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV TZ=America/New_York
CMD ["python3", "-u", "moonbeam-bot.py"]
