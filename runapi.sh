#!/bin/bash

cd netapi
python3 manage.py runserver 0:8000& disown
exit
