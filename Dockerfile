FROM python:3.6

RUN apt-get update
COPY . /app
WORKDIR /app
RUN pip install virtualenv
RUN pip install -r requirements.txt
