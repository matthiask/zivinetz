#!/bin/sh
venv/bin/python -Wall venv/bin/coverage run ./manage.py test testapp && venv/bin/coverage html
