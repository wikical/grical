"""
Transactional version control for Django models.

Project sponsored by Etianen.com

<http://www.etianen.com/>
"""


from grical.reversion.revisions import revision


# Legacy registration methods, now delegating to the revision object.
register = revision.register
is_registered = revision.is_registered
unregister = revision.unregister

