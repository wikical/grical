INSTALLATION
------------
- Search for dev.cloca.net on all files and change it to your domain
- If using Apache edit apache/django.wsgi and replace the path of the installation. 
- Edit settings-TO-RENAME.py and set the variables accordingly to your installation. Then rename it
  to settings.py 

NOTES
-----
* events submitted by anonymous users can be edited by anyone, otherwise the submitter decides (only
  he, all, some groups)


For developement, in the /etc/apache2/apache2.conf file, this setting was included:

MaxRequestsPerChild 1

It makes the server reload every request, in order to be able to see changes immediately, but remove this in production version.

