FROM python:3.10.0a7-slim-buster
LABEL maintainer="dcruzf@home.org.au" 

# set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# install dependencies
COPY ./requirements.txt .
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# copy project
COPY ./app .
# set work directory
WORKDIR /app

USER user