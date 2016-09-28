**grical** is a platform for events web sites. It is the software
running behind `grical.org`__. Main coding language used is
`Python`__/`Django`__.

__ http://grical.org/
__ https://python.org/
__ https://www.djangoproject.com/


Setup a development environment
===============================

The following setup uses sqlite3 as database back end, virtualenv as
isolated Python environment and Linux host system. Other combinations
are possible e.g. linux container and PostgreSQL.

Clone repository
----------------

.. FIXME migrate to github link when it is known

.. code-block:: bash

    cd && hg clone ssh://hg@bitbucket.org/gridmind/grical


System packages requirements
----------------------------

Either to run tests or to setup a full working development environment
you need to install some system packages. For Ubuntu systems:

For 14.04LTS:

.. code-block:: bash

    cat ~/grical/requirements/development.trusty.apt | tr '\n' ' '|xargs sudo apt-get install

For 15.04+:

.. code-block:: bash

    cat ~/grical/requirements/development.xenial.apt | tr '\n' ' '|xargs sudo apt-get install


Run tests
---------

Setup `tox`_ either using system packages or with pip.

.. _tox: https://tox.readthedocs.io/

Running tests by issuing the `tox` command:

.. code-block:: bash

    cd ~/grical && tox


Setup development
-----------------

Create a settings file
~~~~~~~~~~~~~~~~~~~~~~

You need a Django settings file. You just need to copy
``settings-example.py`` which is ready for development. You may use it
instead by specifying ``--settings grical.settings.settings-example``
while running management commands, however making a copy of the file
is better for convenience.

.. code-block:: bash

  cd ~/grical/grical/settings && cp settings-example.py settings.py

Create a virtualenv
~~~~~~~~~~~~~~~~~~~

And then activate the virtualenv:

.. code-block:: bash

  virtualenv ~/virtualenvs/grical
  source ~/virtualenvs/grical/bin/activate

Assuming that you have a ``virtualenvs`` directory in your home where
you store virtualenvs.

Install python requirements
~~~~~~~~~~~~~~~~~~~~~~~~~~~

While using virtualenv:

.. code-block:: bash

    cd ~/grical/requirements && pip install -r development.pip

Migrate db
~~~~~~~~~~

While using virtualenv, migrate db to create database. Then initialize
``django_site`` table:

.. code-block:: bash

    cd ~/grical && python manage.py migrate

    sqlite3 grical_db.sql "UPDATE django_site SET domain='localhost:8000', name='Grical development';"

Install required js/css/bower packages
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Install bower package manager as root:

.. code-block:: bash

    sudo npm install bower -g

Install required packages for grical with bower:

.. code-block:: bash

    cd ~/grical/requirements && bower install --config.directory=../grical/static/bower_components

Start /access development server
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

    cd ~/grical && python manage.py runserver 0.0.0.0:8000

Now you can open the site in your browser, just visit:

http://localhost:8000


Setup grical server
===================

Instructions assume installation to a Linux host and PostgreSQL 9.5.
Different setup may need some modifications to these instructions.


Setup PostgreSQL
----------------

To setup PostgreSQL 9.5, e.g. following
http://tecadmin.net/install-postgresql-server-on-ubuntu/ instructions:

.. code-block:: bash

    sh -c 'echo "deb http://apt.postgresql.org/pub/repos/apt/ `lsb_release -cs`-pgdg main" >> /etc/apt/sources.list.d/pgdg.list'
    wget -q https://www.postgresql.org/media/keys/ACCC4CF8.asc -O - | apt-key add -
    apt-get update

Then follow next paragraph to install postgresql packages alongside
with other system packages.


Install system packages
-----------------------

.. code-block:: bash

    cat ~/grical/requirements/production.apt | tr '\n' ' '|xargs sudo apt-get install


Install required js/css/bower packages
--------------------------------------

Install bower package manager as root, in container:

  npm install bower -g

Install required packages for grical with bower:

  cd ~/grical/requirements && bower install --config.directory=../grical/static/bower_components


Create database, db user, etc
-----------------------------

  su postgres
  psql
then type in psql:
  CREATE EXTENSION IF NOT EXISTS postgis;
Exit psql with Ctrl+D
(possibly this step is not needed, but the next CREATE EXTENSION is
needed)

Run:
  createuser --pwprompt --no-createdb --no-createrole --no-superuser grical_user
password: "grical_password"
Run:
  createdb --owner grical_user -T template1 grical_db
We need also to create extension postgis for grical_db
  psql -d grical_db
then run in psql:
  CREATE EXTENSION IF NOT EXISTS postgis
Exit psql with Ctrl+D

logout as postgres
  exit

NOTE: grical_user needs some additional roles in order to create test
databases if this is desired

# Install pip packages

(always as grical root)
  cd /home/yourusername/grical/requirements/
  pip install -r development.pip

In host machine
---------------

  cd ~/grical/grical/settings
  cp settings-example.py settings.py

edit settings.py, set `DEBUG = True` for development.
Modify DATABASES section to use postgresql. Review also other changes
required to activate CACHES etc.

Login as regular user to grical
-------------------------------
  ssh grical

  cd grical
  python manage.py migrate

  psql -d grical_db -U grical_user -h localhost -p 5432 -c "UPDATE django_site SET (domain, name) = ('grical', 'Grical development')"
(password is "grical_password")

  python manage.py createcachetable cache
(if db_cache is activated in CACHES section, requiring a database)

Start the dev server
  python manage.py runserver 0.0.0.0:8000

in your browser visit: http://grical:8000



Discussion
----------
<ogai> stefanos_, would be nice you just copy the travis-ci config of
dsc for grical, and create an account in travis-ci if needed using
admin@gridmind.org

