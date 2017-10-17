from django.core.management.base import BaseCommand

from failmap_admin.map.determineratings import (default_ratings, rate_organizations_efficient,
                                                rerate_existing_urls)
from failmap_admin.map.models import OrganizationRating, UrlRating


class TaskCommand(Basecommand):
    """A command that performs it's intended behaviour through a Celery task.

    The task can be run directly, sync- and asynchronously.

    Direct execution will run the task as if it was a direct function call.

    Sync execution will use the Celery framework to execute the task on
    a (remote) worker destined to execute tasks of this type. It will wait for
    execution to complete and return the task result/logging.

    Async is like Synchronous execution but it will not wait for it to complete.
    No result or logging will be returned.

    Direct and sync methods allow the task to be interupted during execution
    using ctrl-c.
    """


# Remove ALL organization and URL ratings and rebuild them
class Command(TaskCommand):
    """Remove all organization and url ratings, then rebuild them from scratch."""

    help = __doc__

    # history
    # this has been made when a bug caused hunderds of thousands of ratings, slowing the top fail
    # The history code was present already to make the history for the map.
    # It has now been refactored into a command, so it's easier to work with.

    def handle(self, *args, **options):
        rerate_existing_urls()

        OrganizationRating.objects.all().delete()
        default_ratings()
        rate_organizations_efficient(create_history=True)
