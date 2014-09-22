#!/bin/sh
coverage run ./manage.py test testapp && coverage html
