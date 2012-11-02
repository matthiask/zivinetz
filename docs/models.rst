.. _models:

Die Struktur der Datenbank
==========================

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

Codewörter
~~~~~~~~~~

Öffentliche Feiertage
~~~~~~~~~~~~~~~~~~~~~

Betriebsferien
~~~~~~~~~~~~~~
