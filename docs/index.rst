Willkommen zur Zivinetz-Dokumentation
====================================

.. toctree::
   :maxdepth: 2
   :caption: Inhalt:

   installation
   getting_started
   models/index
   api/index
   deployment
   changelog

Über Zivinetz
------------

Zivinetz ist ein Django-basiertes System zur Verwaltung von Zivildiensteinsätzen.

Technische Voraussetzungen
-------------------------

* Python 3.10+
* Django 4.0+

Verwendete Bibliotheken
----------------------

* `Towel <https://github.com/matthiask/towel/>`_
* `towel-foundation <https://github.com/matthiask/towel-foundation/>`_
* `PDFDocument <https://github.com/matthiask/pdfdocument/>`_
* `reportlab <http://www.reportlab.com/>`_
* `FeinCMS <http://feincms.org>`_
* `Foundation 4 <http://foundation.zurb.com>`_

.. toctree::
   :maxdepth: 2
   :caption: Module:

   models/scope_statement
   models/drudge
   models/assignment
   models/compensation

Zivinetz
--------

Dieses Dokument ist für Entwickler gedacht. Es setzt ein grundsätzliches
Verständnis von Django und der rechtlichen Bestimmungen rund um den
Zivildienst voraus.

Im Zivinetz verwendet werden abgesehen von der Standard Library folgende
Python-Module verwendet:

- `Towel <https://github.com/matthiask/towel/>`_
- `towel-foundation <https://github.com/matthiask/towel-foundation/>`_
- `PDFDocument <https://github.com/matthiask/pdfdocument/>`_ und somit
  `reportlab <http://www.reportlab.com/>`_
- `FeinCMS <http://feincms.org>`_ für die Navigation

Voraussetzung für den Betrieb des Zivinetz ist Python 3.10 und Django 4.0.

Als Frontend-Framework wird `Foundation 4 <http://foundation.zurb.com>`_
verwendet.


Die Einsatzvereinbarung
-----------------------

Die Einsatzvereinbarungen werden in den Models ``ScopeStatement`` und
``Specification`` gespeichert. Das ``ScopeStatement`` ist die eigentliche
Einsatzvereinbarung gemäss EIS, und entält auch die EIS-Nummer. Für die
EIV selbst muss aber zwischen Einsätze mit Unterkunft und Einsätzen ohne
Unterkunft unterschieden werden -- dies ist der Sinn und Zweck des
``Specification``-Models. Für jede ``ScopeStatement``-Instanz existieren
minimal ein und maximal zwei ``Specification``-Instanzen. In der
``Specification`` wird festgelegt, ob Unterkunft, Essen und Bekleidung
entschädigt werden oder nicht. Die genauen Beträge werden aber nicht
an dieser Stelle festgelegt, sondern bei den aktuellen Spesensätzen weiter
unten.

Für Unterkunft, Morgenessen, Mittagessen und Abendessen wird jeweils
festgelegt, ob Entschädigung für Arbeitstage, Freitage und Krankheitstage
ausbezahlt wird oder nicht.

Die Felder ``accomodation_throughout`` und ``food_throughout`` haben
keinen Einfluss auf die Entschädigung. Diese wirken sich nur auf das generierte
Einsatzvereinbarungs-PDF aus.

Unter ``conditions`` kann ein PDF hochgeladen werden, welches zusätzliche
Bestimmungen und Informationen enthält, welche an die EIV angehängt werden
sollen.


Zivis und ihre Einsätze
-----------------------

Der Zivi
~~~~~~~~

Das ``Drudge``-Model enthält alle aktuellen, relevanten Informationen zum
Zivi. Das sind neben dem Wohnort unter anderem die Bankverbindung, die
Krankenkasse, Informationen zu absolvierten Kursen wie z.B. Fahrkurs,
Holzerkurs, Umweltkurs usw.

Wenn der Zivi seine Daten aktualisiert, wird keine Kopie gesichert. Wenn ein
Zivi also mehrere Einsätze absolviert, besteht die Möglichkeit dass die Angaben
nur für den aktuellsten Einsatz stimmen, für ältere aber nicht.

Name, Passwort und Emailadresse werden im ``User``-Model gespeichert welches
von Django schon mitgeliefert wird. Die ZDP-Nr. ist aber beim  ``Drudge``
gespeichert, trotzdem ist die Authentifizierung sowohl mit Emailadresse als
auch mit ZDP-Nr. möglich.

Der Einsatz
~~~~~~~~~~~

Geplante, vereinbarte und abgelehnte Einsätze werden im ``Assignment``-Model
gespeichert. Die wichtigsten Angaben sind:

- Die ``Specification``, womit sowohl das Pflichtenheft als auch die
  Spesenberechnung definiert wird.
- Das Regionalzentrum welches für den Einsatz zuständig ist. Dies wird unter
  anderem auch deswegen gespeichert, weil der Zivi im Laufe seiner
  Zivildienstpflicht das Regionalzentrum wechseln könnte, dies auf vergangene
  Einsätze aber keinen Einfluss haben soll.
- Verschiedene Datumsfelder, z.B. Einsatzbeginn, Einsatzende, Datum der
  Vereinbarung und Datum des Aufgebots. Der letzte Punkt ist vor allem deswegen
  wichtig, weil damit die für den Einsatz zu verwendenden Spesensätze bestimmt
  werden.


Bewertung und Arbeitszeugnis
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Jeder Einsatz kann mit einer Note bewertet und kommentiert werden. Der
Durchschnitt aller Bewertungen wird anschliessend im Zivinetz angezeigt.
Dazu wird das Model ``Assessment`` verwendet.

Ebenfalls können standardisierte Arbeitszeugnisse hinterlegt und nachher
für einzelne Einsätze übernommen werden. Die Vorlagen werden mittels
``JobReferenceTemplate``, die Arbeitszeugnisse mittels ``JobReference``
gespeichert. Die Vorlagen sind Lückentexte, verschiedene Werte wie Name,
Geburtsdatum, Heimatort und Einsatzzeitraum werden automatisch abgefüllt. Der
Text des Arbeitszeugnisses kann anschliessend individuell nachbearbeitet
werden.


Spesen
------

Aktuelle Spesensätze
~~~~~~~~~~~~~~~~~~~~

Die aktuellen Spesensätze werden im Model ``CompensationSet`` gesichert.
Spesensätze sind immer so lange gültig, bis vom Bund neue Spesensätze in Kraft
gesetzt werden. Deshalb wird zur Bestimmung der jeweiligen Spesensätze nur ein
einzelnes Datumsfeld, ``valid_from`` benötigt. Relevant für die Auswahl des
Spesensatzes ist dabei das Datum des Aufgebots, womit Zivis, welche ihren
Einsatz zur gleichen Zeit absolvieren, für dieselbe Leistung unterschiedliche
Entschädigung erhalten können.


Spesenrapporte
~~~~~~~~~~~~~~

Für jeden Monat des Einsatzes wird ein einzelnes Spesenblatt erstellt, sofern
ein Einsatz verlängert wurde für den Rest des Monats sogar ein zweites. Die
Spesenblätter enthalten jeweils Arbeitstage, Freitage, Krankheitstage,
Ferientage und Urlaubstage, Kleiderspesen, Transportspesen und Verschiedenes,
jeweils mit einem Bemerkungsfeld dazu.

Bei den Spesen werden Frankenbeträge gespeichert, die Tage werden als Ganzzahlen
hinterlegt und mit den aktuellen Spesensätzen zu einem auszuzahlenden Total
verrechnet.

Gespeichert wird ebenfalls das aktuelle Pflichtenheft für das Spesenblatt. Wenn
während eines Einsatzes z.B. von Einsatz mit Unterkunft zu Einsatz ohne
Unterkunft gewechselt wird (und somit auch andere Spesensätze gültig sind),
kann dies durch Umschalten der ``Specification`` für die Spesenblätter
bewerkstelligt werden. Nicht unterstützt wird der Wechsel der Pflichtenhefts
innerhalb eines Monats. In diesem Fall muss die Spesendifferenz von Hand
berechnet werden und das Feld ``Verschiedenes`` verwendet werden.


Hilfsdaten
----------

Regionalzentren
~~~~~~~~~~~~~~~

Eine Liste der Regionalzentren inkl. deren Postadresse.


Codewörter
~~~~~~~~~~

Codewörter können einfach und periodisch angepasst werden, damit verhindert
werden kann dass sich Zivis selbst eintragen ohne vorher mindestens Kontakt
mit dem Betrieb aufgenommen zu haben. Aktuell werden die Codewörter an
folgenden Stellen verwendet:

- ``einsatz``: Bei der Erstellung einer provisorischen Einsatzvereinbarung

Sofern das Codewort nicht definiert ist, wird ein leeres verwendet (was bei
den Formularen aber nicht erlaubt ist, da dort die Eingabe erzwungen wird) --
somit ist die Eintragung verunmöglicht.


Öffentliche Feiertage und Betriebsferien
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Für jeden öffentlichen Feiertag muss eine ``PublicHoliday``-Instanz erstellt
werden, damit die Einsatztage für die Spesenrapporte korrekt berechnet werden
können. Dasselbe gilt für die Betriebsferien, im Model ``CompanyHoliday``
können aber auch Datumsbereiche erfasst werden.

Öffentliche Feiertage für die Jahre 2000 bis 2030 können automatisch mit Hilfe
des Django-Befehls ``./manage.py public_holidays`` generiert werden.
