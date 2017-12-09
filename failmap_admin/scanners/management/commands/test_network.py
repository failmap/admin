import logging

from django.core.management.base import BaseCommand

from failmap_admin.scanners.scanner_http import test_network

logger = logging.getLogger(__package__)


class Command(BaseCommand):
    help = 'Try to establish ipv4 and ipv6 connections to test the network, on both a worker and locally.'

    def handle(self, *args, **options):

        # on a worker
        task = test_network.s(code_location="worker")
        task.apply_async()

        # locally
        test_network(code_location="local")
