import ipaddress
import logging

import tldextract
from django.core.exceptions import ObjectDoesNotExist
from django.core.management.base import BaseCommand

from failmap_admin.organizations.models import Organization
from failmap_admin.scanners.models import Endpoint, TlsQualysScan, Url

logger = logging.getLogger(__package__)


class Command(BaseCommand):
    help = 'Some help to get your twitter handles in the database.'

    """
    Enjoy your typing!
    """

    # https://docs.djangoproject.com/en/1.11/howto/custom-management-commands/

    def handle(self, *args, **options):
        organisations = Organization.objects.all().filter(twitter_handle__isnull=True)

        # todo: you can of course just ask duckduckgo
        try:
            for organisation in organisations:
                print("Twitter gemeente %s" % organisation.name)
                twitter_handle = input("Type the twitter handle, including the @:")
                print("U typed the following exploit: %s" % twitter_handle)
                organisation.twitter_handle = twitter_handle
                organisation.save()
        except KeyboardInterrupt:
            # a nice suprise when getting suicidal entering data...
            trollface = """
77777777777777777777777777777777777777777777777777777777777777777777777777777777777777777777777777
77777777777777777777777777777777777777777777777777777777777777777777777777777777777777777777777777
777777777777777777777777777777777............................................777777777777777777777
7777777777777777777777777................7777777777777777777777777777777777.....777777777777777777
7777777777777777777...........7777777777.....777777777777777..7777777777777777...77777777777777777
77777777777777777....77777777777777777777777777777777777777777777..7777777777777...777777777777777
77777777777777....7777.77......777777777777...77777777777777..777777.777777777777...77777777777777
777777777777....7777777777777777777777777777777777777777777777777..7777.7777777777...7777777777777
77777777777...777777777777.....77777777777777777777.7777777777...777.7777.777777777...777777777777
7777777777..77777777777.7777777777777777777777777.7777777777777777..777.7777.7777777...77777777777
7777777777..777777777.777777777777.7777777777777777777777777777777777.77.7777.7777777..77777777777
7777777777..77777777.77777777777777777777777777777777777777777777777777.77.77777777777..7777777777
777777777..777777777777777777777777777777777777777777..............7777777777777777777...777777777
77777777...777777777777........7777777777777777777.....777............77777777777777777...77777777
7777....77777777777..............7777777777777....777777........77...777777777777777777...77777777
777...777.....7...7...............77777777777...77777.................7777.7777........7....777777
77..777.777777777777777777.............7777777.........77777777777..777.777777777777777777...77777
7..77.777..777777777777777777777....77777777777.....777777...77777777777777..........7777777..7777
7..7.77.777......7777777777777777..7777777777777777777777777....7777777......777777....7777.7..777
7...77777..........7777.777777777..777777777777777777777777777...........77777..77777...777.77...7
7...77777.7777777........77777777..7777777777777777777777777777777777777777777..777777..777.77...7
7...77.7777777..77....77777777....77777777777777777777777777777777777777777.....7777777..77.777..7
7..7777.777777..77777777777....7777777777777777........7777777777777777.....777......77..77.777..7
7....777..77....7777777777.....77777777777777777777..77777777777777......77777...7...7...77.77...7
77..7..77777....7777777..77.....777777777.......777..7777777777.......77777777..777777..777777...7
77...7777.77..7...777.77777777...77777777777777.7...777777........7..7777777....77777..777.77...77
777...77777.........777777777777......777777777777777........777777..7777......777777777..77..7777
7777...7777..7..7......77777777777...77777777777........7777777777...7........7777777.77777...7777
77777..7777....77..77........77777777..............77..7777777777.......77...7777777777.....777777
77777..7777....77..7777....................7777777777..777777........7777...777777777777...7777777
77777..7777....77..777...7777777..7777777..7777777777...7.........7..777...77777777777...777777777
77777..7777........777..77777777..7777777..777777777...........7777..77...77777777777...7777777777
77777..7777.................................................7777777......777777777777..77777777777
77777..7777...........................................7..77777777777...7777777777777...77777777777
77777..77777....................................7777777..777777777...77777777777777...777777777777
77777..77777..7...........................7..7777777777...77777....777777777777777...7777777777777
77777..777777..7..77..777..77777...77777777..77777777777..777....777777777777777...777777777777777
77777..777777......7...777..77777..77777777..777777777777......7777777777777777...7777777777777777
77777..7777777....777...77...7777..77777777..777777777......7777777.77777.777...777777777777777777
77777..777777777.........77..7777...7777777..77.........77777777.77777..777....7777777777777777777
77777..77777777777777...............................777777777..7777..7777.... 77777777777777777777
7777...77777777.777777777777777777777777777777777777777777.77777..7777.....77777777777777777777777
7777..7777777777.777777777777777777777777777777777777..777777.77777.....77777777777777777777777777
7777..777777777777.777777777777777777777777777777..777777..77777.....77777777777777777777777777777
77..77777..77777777...77777777777..........777777..7777777......7777777777777777777777777777777777
7..777777777.7777777777777777777777777...777777777777.....7777777777777777777777777777777777777777
7...7777777777...............777777777777777777777.....7777777777777777777777777777777777777777777
7...777777777777777777777777777777777777777777.....77777777777777777777777777777777777777777777777
77...77777777777777777777777777777777777..7.....77777777777777777777777777777777777777777777777777
777....7777777777777777777777777777..........77777777777777777777777777777777777777777777777777777
7777.....7777777777777777777.........7777777777777777777777777777777777777777777777777777777777777
7777777........................7777777777777777777777777777777777777777777777777777777777777777777
77777777777777777777777777777777777777777777777777777777777777777777777777777777777777777777777777
"""
            print(trollface)
            print("U Done!? :)")
