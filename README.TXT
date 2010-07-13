.. This file is written in ReStructuredText__
__ http://en.wikipedia.org/wiki/ReStructuredText

INTRODUCTION
============

See ABOUT.TXT


LICENSE
=======

GridCalendar is licensed under the GNU Affero General Public License. See the file LICENSE.TXT


CONTACT
=======

> GridMind Vorgründungsgesellschaft Iván Fernando Villanueva Barrio EU
> Malmöer Str. 6
> 10439 Berlin
> Germany
> 
> Tel. +49 3039820596
> E-Mail: info ät gridmind.org


INSTALLATION
============

See INSTALL.TXT


NOTES FOR DEVELOPERS
=====================

* For strings to be translated in python code, use named-string interpolation (e.g., %(day)s)
  instead of positional interpolation (e.g., %s or %d). Example:
    output = _('Today is %(month)s, %(day)s.') % {'month': m, 'day': d}
  For more about translations, see (after installing the package python-django-doc):
  file:///usr/share/doc/python-django-doc/html/topics/i18n.html#topics-i18n

* Using the Django Shell, an example ::
        ./manage shell
        from gridcalendar.events.models import *
        e = Event.objects.get(pk=1)
        g = e.group_set.all()

* If you use Postgresql, and if you want to clone a data base for development purposes, you can do * something like: ::
        createdb -U gridcalendar -O gridcalendar gridcalendar-dev
        pg_dump -U gridcalendar gridcalendar | psql -U gridcalendar gridcalendar-dev
        psql -U gridcalendar gridcalendar-dev -c "UPDATE django_site SET domain = 'dev.yourdomain.net' WHERE id = 1"

* There is an interesting package: incf.countryutils * (http://pypi.python.org/pypi/incf.countryutils/1.0) ::
        >>> from incf.countryutils import transformations
        >>> transformations.cca2_to_ccn('de')
        '276'
        >>> transformations.ccn_to_cn(276)
        'Germany'
  In Debian based systems it can be installed with: ::
        aptitude install python-pip
        pip install incf.countryutils
    
* There is a full-featured geographical application for django. In Debian based systems it can be installed with: ::
        aptitude install libgdal1-1.5.0 postgresql-8.3-postgis postgresql-server-dev-8.3 python-geoip geoip-database
  For python-geoip a version higher then 1.2.1-2 is needed, for example 1.2.4-1, because 1.2.1 doesn't have continent support.
  After installation of PostGIS you must issue commands like these as root: ::
        su postgres
        cd /usr/share/postgresql-8.3-postgis/
        createlang plpgsql gridcalendar
        psql -d gridcalendar -f lwpostgis.sql
        psql -d gridcalendar -f spatial_ref_sys.sql

