#!/bin/bash

celery -A main.celery worker -l info &

python main.py
