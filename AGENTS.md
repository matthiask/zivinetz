# Agent notes

## Tests

Requires a local PostgreSQL database:

    DATABASE_URL=postgres:///zivinetz tox -e tests

Or, once the tox env exists:

    DATABASE_URL=postgres:///zivinetz .tox/tests/bin/coverage run tests/manage.py test testapp
