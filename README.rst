Introduction
============

**grical** is a Django__ web application for maintaining and finding
events. It is the Python__ software running behind `grical.org`__ and other
sites.

__ https://www.djangoproject.com/
__ https://python.org/
__ http://grical.org/


Howto setup a development environment
=====================================

The following setup uses sqlite3 as the database backend, virtualenv for the
isolated Python environment and a GNU/Linux host system. Other combinations
are possible like using PostgreSQL.

- Clone the repository

.. code-block:: bash

   cd ~
   hg clone ssh://hg@bitbucket.org/gridmind/grical

- Install the OS requirement packages. For Ubuntu 14.04LTS there is a list of
  OS package requirements at
  ``grical/requirements/development.trusty.apt``. You can install them with:

.. code-block:: bash

    cat ~/grical/requirements/development.trusty.apt | tr '\n' ' '|xargs sudo apt-get install

  For Ubuntu 15.04+ use:

.. code-block:: bash

    cat ~/grical/requirements/development.xenial.apt | tr '\n' ' '|xargs sudo apt-get install

- Rename ``settings-example.py`` as ``settings.py`` which is ready for
  development. You may also use it directly by specifying ``--settings
  grical.settings.settings-example`` while running management commands.

.. code-block:: bash

  cd ~/grical/grical/settings && cp settings-example.py settings.py


- Create and activate a Python virtual environment, and setup Django:

.. code-block:: bash

  mkdir ~/virtualenvs
  virtualenv ~/virtualenvs/grical
  source ~/virtualenvs/grical/bin/activate
  pip install -r ~/grical/requirements/development.pip
  python manage_development.py migrate
  sqlite3 grical_db.sql "UPDATE django_site SET domain='localhost:8000', name='Grical development';"

Install bower:

.. code-block:: bash

    cd ~/grical
    sudo npm install bower -g

Install the required packages for grical with bower:

.. code-block:: bash

    cd ~/grical/requirements
    bower install --config.directory=../grical/static/bower_components

- Start the Django Development Server

.. code-block:: bash

    cd ~/grical && python manage_development.py runserver 0.0.0.0:8000

Now you can open the site in your browser by just visiting
http://localhost:8000 and edit the source code.

To run the tests, install `tox`_ either using a OS package or with pip.

.. _tox: https://tox.readthedocs.io/

Run tests by issuing the `tox` command:

.. code-block:: bash

    cd ~/grical
    tox


Howto deploy grical
===================

These instructions assume the installation is taking place in a GNU/Linux
system. The database used will be PostgreSQL 9.5.

Create a system user ``grical`` and clone the repository

.. code-block:: bash

    sudo adduser grical
    su grical -c "cd /home/grical && hg clone ssh://hg@bitbucket.org/gridmind/grical"

Setup PostgreSQL 9.5, e.g. following
http://tecadmin.net/install-postgresql-server-on-ubuntu/:

.. code-block:: bash

    sh -c 'echo "deb http://apt.postgresql.org/pub/repos/apt/ `lsb_release -cs`-pgdg main" >> /etc/apt/sources.list.d/pgdg.list'
    wget -q https://www.postgresql.org/media/keys/ACCC4CF8.asc -O - | apt-key add -
    apt-get update
    apt-get install postgresql-9.5 postgresql-9.5-postgis-2.2

Install the required OS packages:

.. code-block:: bash

    cat ~/grical/requirements/production.apt | tr '\n' ' '|xargs sudo apt-get install

Create a DB user, a database, and the postgis extension for the database:

.. code-block:: bash

    su postgres -c "createuser --pwprompt --no-createdb --no-createrole --no-superuser grical"
    su postgres -c "createdb --owner grical -T template1 grical"
    su postgres -c "psql -d grical -c 'CREATE EXTENSION IF NOT EXISTS postgis;'"

Keep the ``grical`` user password (you have been asked for) for the next step.

Copy ``grical/settings/development.py`` to ``grical/settings/settings.py``, and in it:

- Set ``DEBUG = False``
- Review and set ``CACHES``, ``DATABASES``, ``ADMINS``, ``IMAP_*``, ``GEONAMES_*``, ``REPLY_TO``, ``DEFAULT_FROM_EMAIL``, ``SERVER_EMAIL``, ``EMAIL_SUBJECT_PREFIX`` and ``EMAIL_*``.
- Set a ``SECRET_KEY``.

For ``DATABASES`` use user name, db name and password created above.

Optionally, have a look at ``settings_base.py`` for other customization
options, documented inline.

Copy ``manage_development.py`` to ``manage.py`` and replace ``development`` in it with ``settings``.

Install the Python requirements:

.. code-block:: bash

    cd ~grical/grical/requirements
    sudo pip install -r production.pip

Install the required JS and CSS packages with Bower:

.. code-block:: bash

    sudo npm install bower -g
    su grical -c "cd ~grical/grical/requirements && bower install --config.directory=../grical/static/bower_components"

Migrate the database and create a cache table:

.. code-block:: bash

    su -grical -c "cd ~grical/grical && python manage.py migrate"
    su -grical -c "cd ~grical/grical && python createcachetable cache"
    psql -d grical_db -U grical_user -h localhost -p 5432 -c "UPDATE django_site SET (domain, name) = ('grical', 'GriCal')"

Setup a cron jobs for accepting events submitted as email. It should run periodically the custom Django management command ``imap``.

Installing memcached_ is recommended as Grical will automatically use it for
performance::

    apt-get install memcached

.. _memcached: https://en.wikipedia.org/wiki/Memcached

Edit ``/etc/memcached.conf`` and restart memcached.
Set the Django settings as appropriate.

`Run a celery worker as a daemon`_. This is the best option for
production. For the broker we suggest `RabbitMQ`_. The `broker setup`_ for Celery and
RabbitMQ is minimal and requires no options.

.. _Run a celery worker as a daemon: http://docs.celeryproject.org/en/latest/tutorials/daemonizing.html
.. _RabbitMQ: http://www.rabbitmq.com/download.html
.. _broker setup: http://docs.celeryproject.org/en/latest/getting-started/brokers/rabbitmq.html

#. Install RabbitMQ::

       apt-get install rabbitmq-server

#. Add a user and a vhost::

       rabbitmqctl add_user guest guest
       rabbitmqctl add_vhost "/"
       rabbitmqctl set_permissions -p "/" guest ".*" ".*" ".*"

Refer further to `Deploying Django`_. We recommend using `uWSGI and nginx`_.

.. _Deploying Django: https://docs.djangoproject.com/en/1.8/howto/deployment/
.. _uWSGI and nginx: http://uwsgi-docs.readthedocs.io/en/latest/tutorials/Django_and_nginx.html
