This file is part of GridCalendar and describes the structure of its html templates. It uses the
Django's template system which is well summarized on http://www.djangobook.com/en/2.0/chapter04/

---------
base.html
---------

It holds the main look and feel and uses the variables:

-------------     ---------------------------------------------------------------------
LANGUAGE_CODE     is the current user's preferred language, as a string. Example: en-us
DOMAIN            example: gridcalendar.net
MEDIA_URL         example: http://gridcalendar.net/media/
PROTOCOL          example: https
title             the title of the page, example: GridCalendar - home
VERSION           the version of the software, example: 1.0
-------------     ---------------------------------------------------------------------

It contains the blocks:

---------   ---------------------------------------------------------------
feeds       empty block in the header of the html page
blockbots   block in the header which blocks robots for indexing the pages
css         empty block in the header for potential custom css
column1     empty block for the content of the left column
column2     empty block for the content of the right column
---------   ---------------------------------------------------------------
