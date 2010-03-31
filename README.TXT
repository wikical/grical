
============
INTRODUCTION
============

GridCalendar is a free software providing information about events which can be stored and retrieved
in different ways and formats.


=======
LICENSE
=======

GridCalendar is licensed under the GNU Affero General Public License. See the file LICENSE.TXT


=======
CONTACT
=======

GridMind Vorgründungsgesellschaft Iván Fernando Villanueva Barrio EU
Malmöer Str. 6
10439 Berlin
Germany

Tel. +49 3039820596
E-Mail: info@gridmind.org


=====
NOTES
=====

ABOUT THE PUBLIC-FLAG IN EVENTS
-------------------------------
Public events can be edited by anyone, otherwise only by the submitter and the members of the group
the event might belong to. A private event can belong to maximal one group. On the contrary, public
events can belong to many groups.

Events submitted by anonymous users are public.

The public-flag of an event cannot be changed after the first submission.

The rational of private events belonging only to a single group is also that events have comments,
and members of a group commenting on an event might not want non-members to see their comments.

USING THE DJANGO SHELL
----------------------
> ./manage shell
from gridcalendar.events.models import *
e = Event.objects.get(pk=1)
g = e.group_set.all()

INSTALLATION
------------
- Search for 'gridcalendar' on all files and change it accordingly
- If using Apache edit apache/django.wsgi and replace the path of the installation.
- Edit settings-TO-RENAME.py and set the variables accordingly to your installation. Then rename it
  to settings.py

MISCELANEOUS
------------
* events submitted by anonymous users can be edited by anyone, otherwise the submitter decides if
  the event is private or public

* For development, in the /etc/apache2/apache2.conf file, this setting was included:
  MaxRequestsPerChild 1
  It makes the server reload every request, in order to be able to see changes immediately, but
  remove this in production version.

