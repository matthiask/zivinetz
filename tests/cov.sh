#!/bin/sh
venv/bin/coverage run ./manage.py test testapp -v 2 && venv/bin/coverage html
