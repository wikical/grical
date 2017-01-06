Version 1.0
===========

* Upgraded Django to 1.8 LTS from 1.3
* Updated requirements
* Fixed deprecated code.
* Introduced Bootstrap for CSS
* Introduced Bower for JS dependencies.

Incompatible changes
--------------------

* Capability to output to a Unix pipe was removed by removing the
  related custom setting: ``LOG_PIPE``.
* The ``irclogger.py`` script was removed, which was intended to be used in
  conjunction with the ``LOG_PIPE`` setting.
