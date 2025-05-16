Installation
===========

Voraussetzungen
--------------

1. Python 3.10 oder höher
2. pip (Python Package Manager)
3. virtualenv (empfohlen)

Installationsschritte
--------------------

1. Virtualenv erstellen und aktivieren::

    python -m venv venv
    source venv/bin/activate  # Unter Linux/Mac
    # oder
    venv\Scripts\activate  # Unter Windows

2. Zivinetz installieren::

    pip install -e .

3. Datenbank einrichten::

    python manage.py migrate

4. Entwicklungsserver starten::

    python manage.py runserver 