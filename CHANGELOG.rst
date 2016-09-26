Version 1.0
===========

* Upgraded Django to 1.8 LTS from 1.3, updated most of requirements


Incompatible changes
--------------------

* Capability to output to a Unix pipe was removed, by removing the
  related custom setting: `LOG_PIPE`.
* `irclogger.py` script removed, intended to be used in conjunction
  the `LOG_PIPE` setting.

