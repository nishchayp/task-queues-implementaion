FROM ubuntu:latest

MAINTAINER Nishchay Parashar "nishchayparashar98@gmail.com"

RUN apt-get update -y && \
    apt-get install -y python-pip python-dev

EXPOSE 5000

WORKDIR /app

COPY . /app

RUN pip install -r requirements.txt

CMD python main.py
