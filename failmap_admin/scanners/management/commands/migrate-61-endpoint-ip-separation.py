import logging

from django.core.exceptions import ObjectDoesNotExist
from django.core.management.base import BaseCommand


from failmap_admin.organizations.models import Organization, Url
from failmap_admin.scanners.models import Endpoint, UrlIp, \
    EndpointGenericScan, TlsQualysScan, Screenshot
from failmap_admin.scanners.scanner_http import scan_url, scan_urls

from .support.arguments import add_discover_verify, add_organization_argument

logger = logging.getLogger(__package__)


class Command(BaseCommand):
    help = 'Make the migration of issue 61: place IP addresses in a separate table'

    def handle(self, *args, **options):

        move_ip_information()
        merge_duplicate_endpoints()

        # Step: verify that everything works
        # rebuild-ratings: still works exactly the same, with the same bugs.
        #   todo: history slider does not change report over time. Also on original.
        # scanners should work differently: ip has to be stored separately.
        # life-cycle of discovery changes completely.

def move_ip_information():
    """
    Step 1

    This is pretty straight forward: create IP records in a new table, pointing to the old
    endpoints. Take over the same information about existance (or non-existance) and just delete
    the IP information.

    :return:
    """

    endpoints = Endpoint.objects.all()

    for endpoint in endpoints:
        epip = UrlIp()
        epip.url = endpoint.url
        epip.ip = endpoint.ip
        epip.discovered_on = endpoint.discovered_on
        epip.is_unused = endpoint.is_dead
        epip.is_unused_reason = endpoint.is_dead_reason
        epip.is_unused_since = endpoint.is_dead_since
        epip.save()

        endpoint.ip_version = 6 if ":" in endpoint.ip else 4
        endpoint.ip = ""  # and it's gone.
        endpoint.save()

    # deduplicate the same urls:

    epips = UrlIp.objects.all()
    for epip in epips:
        UrlIp.objects.all().filter(url=epip.url, ip=epip.ip).exclude(id=epip.id).delete()

"""
Going back:
rm db.sqlite3
failmap-admin migrate
failmap-admin createsuperuser

failmap-admin clear-database
failmap-admin load-dataset testdata  # we've not deleted columns till here.
failmap-admin migrate-61-endpoint-ip-separation
"""


def merge_duplicate_endpoints():
    """
    Step 2

    This is the hard part, as it reduces the amount of endpoints significantly.

    Well, it doesn't look that hard now that it's implemented. Thank you Django.

    :return:
    """

    # ordered by newest first, so you'll not have to figure out the current is_dead situation.
    endpoints = Endpoint.objects.all().order_by("-discovered_on")
    for endpoint in endpoints:
        similar_endpoints = Endpoint.objects.all().filter(ip_version=endpoint.ip_version,
                                                          port=endpoint.port,
                                                          protocol=endpoint.protocol,
                                                          url=endpoint.url).exclude(id=endpoint.id)
        for similar_endpoint in similar_endpoints:
            # migrate all scans to the same endpoint
            EndpointGenericScan.objects.all().filter(endpoint=similar_endpoint).update(endpoint=endpoint)
            TlsQualysScan.objects.all().filter(endpoint=similar_endpoint).update(endpoint=endpoint)
            Screenshot.objects.all().filter(endpoint=similar_endpoint).update(endpoint=endpoint)

            # goodbye
            similar_endpoint.delete()
