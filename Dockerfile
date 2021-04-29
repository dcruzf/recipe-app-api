FROM python:3.8-slim-buster

# set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# install dependencies
COPY ./requirements.txt .
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# copy project
RUN mkdir /app
WORKDIR /app
COPY ./app .
# set work directory
WORKDIR /app

RUN mkdir -p /vol/web/media
RUN mkdir -p /vol/web/static
RUN useradd -d /app/ -s /bin/bash user
RUN chown -R user:user /vol/
RUN chmod -R 755 /vol/
USER user