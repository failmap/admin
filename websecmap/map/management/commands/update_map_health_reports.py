import logging

from django.core.management.base import BaseCommand

from websecmap.map.logic.map_health import update_map_health_reports

log = logging.getLogger(__package__)


class Command(BaseCommand):
    help = 'Clear all caches'

    def handle(self, *args, **options):
        log.warning('This does not clear your browsers chache. For JSON this might be relevant.')
        update_map_health_reports()