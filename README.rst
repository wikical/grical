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


Clone repository
----------------

First of all create some ``grical`` user that will own the software
directory.

.. FIXME migrate to github link when it is known

.. code-block:: bash

    su grical -c "cd ~grical && hg clone ssh://hg@bitbucket.org/gridmind/grical"


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


Create database, db user, etc
-----------------------------

Create user, database, then create postgis extension for database.
As root run:

.. code-block:: bash

    su postgres -c "createuser --pwprompt --no-createdb --no-createrole --no-superuser grical"
    su postgres -c "createdb --owner grical -T template1 grical"
    su postgres -c "psql -d grical -c 'CREATE EXTENSION IF NOT EXISTS postgis;'"

Keep ``grical`` password for next step


Django settings
---------------

Copy ``settings-example.py`` to ``settings.py``. As a begin start
setting ``DEBUG = False``. Review and set other values for production,
e.g. ``CACHES``, ``DATABASES``, ``ADMINS``, ``IMAP_*``,
``GEONAMES_*``, ``REPLY_TO``, ``DEFAULT_FROM_EMAIL``,
``SERVER_EMAIL``, ``EMAIL_SUBJECT_PREFIX``, ``EMAIL_*``, etc
Set a ``SECRET_KEY``.

For ``DATABASES`` use user name / db name / password created during
database creation.

Check ``settings_base.py`` for other customization options, documented
in that file.


Install python requirements
---------------------------

As root install python requirements in the host. If you wish better
isolation, install them in some virtualenv and specify virtualenv in
the proper python path. As root:

.. code-block:: bash

    cd ~grical/grical/requirements && pip install -r production.pip


Install required js/css/bower packages
--------------------------------------

Install bower package manager as root:

.. code-block:: bash

    npm install bower -g

Install required packages for grical with bower:

.. code-block:: bash

    su grical -c "cd ~grical/grical/requirements && bower install --config.directory=../grical/static/bower_components"


Celery setup
------------

`Run celery worker as a daemon`_. This is the best option for
production.

.. _Run celery worker as a daemon: http://docs.celeryproject.org/en/latest/tutorials/daemonizing.html

For broker we suggest `RabbitMQ`_. `Broker setup`_ for celery and
RabbitMQ is minimal and requires no options.

.. _RabbitMQ: http://www.rabbitmq.com/download.html
.. _Broker setup: http://docs.celeryproject.org/en/latest/getting-started/brokers/rabbitmq.html

#. Install RabbitMQ::

       aptitude install rabbitmq-server

#. Add a user and a vhost::

       rabbitmqctl add_user guest guest
       rabbitmqctl add_vhost "/"
       rabbitmqctl set_permissions -p "/" guest ".*" ".*" ".*"


Migrate db, create cache table
------------------------------

As root:

.. code-block:: bash

    su -grical -c "cd ~grical/grical && python manage.py migrate"

    su -grical -c "cd ~grical/grical && python createcachetable cache"

    psql -d grical_db -U grical_user -h localhost -p 5432 -c "UPDATE django_site SET (domain, name) = ('grical', 'Grical development')"

(you may be asked for the correct grical db user password)


Setup cron jobs / email submission
----------------------------------

Setup a cronjob to dispatch the custom Django management command
``imap`` which checks an email server for new event submissions. Setup
the command to run every e.g one or two minutes. Set the ``IMAP_*``
Django settings to an IMAP server.


memcached
---------

memcached_ is recommended on production environments; Grical
will automatically use it for performance. To install::

    apt-get install memcached

Edit then ``/etc/memcached.conf`` and restart memcached.
Set the Django settings as appropriate.


Deployment
----------

Refer to: `Deploying Django`_ for general notes. Preferred way to
deploy grical is by using `uWSGI and nginx`_.

.. _Deploying Django: https://docs.djangoproject.com/en/1.8/howto/deployment/
.. _uWSGI and nginx: http://uwsgi-docs.readthedocs.io/en/latest/tutorials/Django_and_nginx.html
