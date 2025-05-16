Einsatzvereinbarungen (ScopeStatement)
=====================================

Das ScopeStatement-Model repräsentiert die Einsatzvereinbarung gemäss EIS.

Attribute
---------

* ``eis_number``: EIS-Nummer der Vereinbarung
* ``specification_set``: Verknüpfte Specifications (mit/ohne Unterkunft)

Verwendung
---------

.. code-block:: python

    from zivinetz.models import ScopeStatement

    # Beispiel für die Erstellung einer Einsatzvereinbarung
    scope = ScopeStatement.objects.create(
        eis_number='12345',
        # weitere Felder...
    ) 