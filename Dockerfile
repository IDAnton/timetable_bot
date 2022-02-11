FROM python:3.8.3-alpine
# set work directory
# set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
# install dependencies

RUN apk update \
    && apk add postgresql-dev gcc python3-dev musl-dev

RUN pip install --upgrade pip
COPY requirements.prod.txt .
RUN pip install -r requirements.prod.txt && \
    apk add tzdata && cp /usr/share/zoneinfo/Asia/Novosibirsk /etc/localtime

# copy project
COPY . .