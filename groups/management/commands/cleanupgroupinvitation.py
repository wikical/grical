"""
A management command which deletes expired group invitations from the database.

Calls ``GroupInvitation.objects.delete_expired_invitations()``, which
contains the actual logic for determining which invitations are deleted.

"""

from django.core.management.base import NoArgsCommand

from groups.models import GroupInvitation


class Command(NoArgsCommand):
    help = "Delete expired group invitations from the database"

    def handle_noargs(self, **options):
        GroupInvitation.objects.delete_expired_invitations()
