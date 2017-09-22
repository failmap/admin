import logging

from django.core.exceptions import ObjectDoesNotExist
from django.core.management.base import BaseCommand

from failmap_admin.organizations.models import Organization, Url
from failmap_admin.scanners.scanner_http import ScannerHttp

logger = logging.getLogger(__package__)


# todo: when tls scanner ends, it hangs.
# todo: add command line arguments: port and protocol.
class Command(BaseCommand):
    help = 'Discover http sites'

    def add_arguments(self, parser):
        parser.add_argument(
            '--organization',
            nargs=1
        )

    def handle(self, *args, **options):

        # urls without endpoints
        if not options['organization']:
            urls_without_endpoints = \
                Url.objects.all().filter(
                    not_resolvable=False, is_dead=False).exclude(
                    endpoint__protocol__in=['http', 'https'])
            logger.debug("Found %s urls that don't have http(s) endpoints yet. "
                         % urls_without_endpoints.count())
            ScannerHttp.scan_url_list_standard_ports(urls_without_endpoints)

        else:

            if options['organization'] and options['organization'] == "_ALL_":
                s = ScannerHttp()
                s.scan_multithreaded(port=8443, protocol="https")
            else:
                logging.debug("Looking for organization: %s" % options['organization'][0])
                try:
                    o = Organization.objects.get(name=options['organization'][0])
                    urls = Url.objects.all().filter(organization=o)
                    ScannerHttp.scan_url_list_standard_ports(urls)
                except ObjectDoesNotExist:
                    logging.debug("Organization was not found.")
