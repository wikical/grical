Legacy database migration guide
===============================

This is a guide on how to migrate legacy grical databases to version
1.0, which uses Django database migrations. If you pulled a more
recent version than 1.0 with Django>=1.11, it is suggested you update
to 1.11, import the data, then update to tip and run django migrations.

By legacy database we mean the schema of grical version as of the year
2012, Django version 1.3 and not any migration application used (such
as django south).

This guide is about migrating data from a PostgreSQL database to a
another PostgreSQL, it does not cover cases of other RDBMS's.

Here are the steps:


Dump legacy database to file
----------------------------

Suppose the owner of the legacy database is the user ``gridcalendar``
and the name of the database is ``gridcalendar`` as well. Dump the
database with a so-called "Custom format" (option ``-Fc``).

.. code-block:: bash

    pg_dump -U gridcalendar -p 5432 -h localhost -Fc -b -v -f grical.pg_dump gridcalendar


Create the new production database
----------------------------------

Most likely you migrate data from an older PostgreSQL version (<9)
to PostgreSQL 9.6. We suppose that new production db is installed in
a new server.

Create a db role (user) who will own the new database, let's call her
``grical``. Create also a role with the username used for the
legacy db owner, let's call her ``gridcalendar``.

Create a blank database. Let's assume the database is called
``grical``, we will first set the owner to ``gridcalendar`` to import
data. As root:

.. code-block:: bash

    su postgres -c "createdb --owner gridcalendar -T template1 grical"

It is a good time to spatially enable the newly created db. As root:

.. code-block:: bash

    su postgres -c "psql -d grical -c 'CREATE EXTENSION IF NOT EXISTS postgis;'"


Migrate PostGIS of the dump to the current version
--------------------------------------------------

The utility is in postgresql contrib packages and should reside in::

    /usr/share/postgresql/9.5/contrib/postgis-2.2

Change directory to above location and run:

.. code-block:: bash

    su postgres -c "perl postgis_restore.pl /location_to_dump/grical.pg_dump > /tmp/grical.pg_dump.sql"


Restore data to the new database
--------------------------------

su to user postgres (should be superuser because of some posgis
objects ownership) and restore from database dump. Then change
ownership of the database to ``grical`` the user that will hold
the production database. As root:

.. code-block:: bash

    su postgres -c "psql -d grical -f /tmp/grical.pg_dump.sql"

    su postgres -c "psql -d grical -c 'ALTER DATABASE grical OWNER TO grical'"


Move the schema
---------------

We move the ``public`` schema that holds a copy of the legacy database
to a schema called ``old_public``. Use the script ``move_schema.sql``
from the current directory. As root:

.. code-block:: bash

    cd to_the_current_directory_where_move_schema.sql_is_found

    su postgres -c "psql -d grical -f move_schema.sql"


Create the new tables in the new production db
----------------------------------------------

Using django tools, create new tables, create db cache if desired. As
the user running the django application:

.. code-block:: bash

    python manage.py migrate

    python manage.py createcachetable cache


Check auth_permission / oembed_providerrule
-------------------------------------------

Normally ``auth_permission`` is created on database migration. Records
will differ from the legacy database. Most likely you have not added
custom permissions for specific grical users, as also grical does not
use permissions nor admin interface usage is encouraged. If however
you did, then you have to check permissions in the legacy db and
replicate them in new database after data migration. Our migration
script does not copy data for permissions / user permissions / group
permissions.

NOTE: following is deprecated, oembed is not installed in new
production grical, nor migrated, since oembed is unmaintained for many
years, and it is fully incompatible with Django 1.11.

The oembed application creates some initial data with fixtures. We
don't migrate these initial data. Most likely there are no any
differences from legacy to new db and it is considered safe to skip
checking. However if you want to check run the following SQL in
``grical`` and check id numbers are same in both schemas:

.. code-block:: sql

    select public.oembed_providerrule.id, old_public.oembed_providerrule.id, public.oembed_providerrule.name from public.oembed_providerrule LEFT JOIN old_public.oembed_providerrule ON public.oembed_providerrule.name=old_public.oembed_providerrule.name;


Migrate data
------------

Use the ``migrate.sql`` script we provide in this directory to migrate
data from ``old_public`` schema to ``public``. As root:

.. code-block:: bash

    cd to_the_current_directory_where_migrate.sql_is_found

    su postgres -c "psql -d grical -f migrate.sql"


Conclusions
-----------

Start web server. You should normally see the grical site working
serving the migrated data.

Django ``settings.SECRET_KEY`` should match the new site, or else user
passwords, sessions etc won't work.

If everything goes well you may drop the ``old_public`` schema as well
the ``grical`` role from the production server.
