========
Zivinetz
========

A Django application for managing civil service personnel and assignments.

Description
-----------

Zivinetz is a specialized management system designed to handle the administration
of civil service personnel (Zivildienstleistende) in Switzerland. It provides
tools for scheduling, assignment tracking, and personnel management.


Installation
------------

1. Ensure you have Python 3.x and pip installed
2. Install the Naturnetz platform and its dependencies
3. Initialize the Zivinetz submodule::

.. code-block:: bash

    # In the Naturnetz root directory
    git submodule update --init

Development Setup
---------------

1. Clone both repositories:

.. code-block:: bash

    git clone [naturnetz-repo-url]
    git clone [zivinetz-repo-url]

2. Follow the installation steps above
3. Make sure all dependencies are installed in both projects

Requirements
-----------

* Python 3.x
* Django
* Naturnetz platform
* Additional dependencies (see requirements.txt)
