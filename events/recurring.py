#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vi:expandtab:tabstop=4 shiftwidth=4 textwidth=79
# GPL {{{1
###############################################################################
# Copyright 2011 Ivan Villanueva <ivan ät gridmind.org>
#                Thomas Fricke <mail ät thomasfricke.de>
#
# This file is part of GridCalendar.
#
# GridCalendar is free software: you can redistribute it and/or modify it under
# the terms of the GNU Affero General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your option) any
# later version.
#
# GridCalendar is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the Affero GNU General Public License for more
# details.
#
# You should have received a copy of the GNU Affero General Public License
# along with GridCalendar. If not, see <http://www.gnu.org/licenses/>.
###############################################################################

from datetime import date, timedelta

from settings import DEFAULT_RECURRING_DURATION_IN_DAYS as DURATION
from settings import MAX_DAYS_IN_FUTURE

class Weekly():
    """Describes a every delta weekly repeating event, default is starting
    today and stopping settings.DEFAULT_RECURRING_DURATION_IN_MONTHS after.

    The constructor raises an ValueError if ``end`` is later than
    MAX_MONTHS_IN_FUTURE from now, or if ``end`` is before ``start``.
    
    >>> weekly = Weekly( start = date( 2011, 3, 5 ),
    ...     end = date( 2011, 9, 3 ) )
    >>> for instance in weekly: print instance.isoformat()
    2011-03-05
    2011-03-12
    2011-03-19
    2011-03-26
    2011-04-02
    2011-04-09
    2011-04-16
    2011-04-23
    2011-04-30
    2011-05-07
    2011-05-14
    2011-05-21
    2011-05-28
    2011-06-04
    2011-06-11
    2011-06-18
    2011-06-25
    2011-07-02
    2011-07-09
    2011-07-16
    2011-07-23
    2011-07-30
    2011-08-06
    2011-08-13
    2011-08-20
    2011-08-27
    2011-09-03
    """
    def __init__( self, start = date.today(), end = None, delta = 1 ):
        if end and end < date.today():
            raise ValueError('end date was before today')
        if end and end > date.today() + timedelta( days = MAX_DAYS_IN_FUTURE ):
            raise ValueError('end was later than MAX_MONTHS_IN_FUTURE')
        self.start = start
        self.current = self.start
        if not end:
            end = start + timedelta( months = DURATION )
        self.end = end
        self.delta = 7 * delta

    def __iter__( self ):
        while self.current <= self.end:
            yield self.current
            self.current += timedelta( days = self.delta )

class Monthly():
    """ describes a monthly repeating event, default is starting today and
    stopping settings.DEFAULT_RECURRING_DURATION_IN_MONTHS after

    The constructor raises an ValueError if ``end`` is later than
    MAX_MONTHS_IN_FUTURE from now.
    
    >>> monthly = Monthly(
    ...     start = date( 2011, 3, 5 ), end = date( 2011, 9, 3 ) )
    >>> for instance in monthly: print instance.isoformat()
    2011-03-05
    2011-04-02
    2011-05-07
    2011-06-04
    2011-07-02
    2011-08-06
    2011-09-03
    """
    def __init__( self, start = date.today(), end = None ):
        if end and end < date.today():
            raise ValueError('end date was before today')
        if end and end > date.today() + timedelta( days = MAX_DAYS_IN_FUTURE ):
            raise ValueError('end was later than MAX_MONTHS_IN_FUTURE')
        self.start = start
        self.current = start
        if not end:
            end = start + timedelta( months = DURATION )
        self.end = end
       
    def __iter__( self ):
        while self.current <= self.end:
            yield self.current
            old_current = self.current
            self.current += timedelta( days = 28 )
            if self.current.isoweekday() != self.start.isoweekday() or \
                    old_current.month == self.current.month:
                self.current += timedelta( days = 7 )

if __name__ == "__main__":
    import doctest
    doctest.testmod()
