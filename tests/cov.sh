#!/bin/sh
venv/bin/coverage run ./manage.py test testapp -v2 && venv/bin/coverage html
