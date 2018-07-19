import logging

from failmap.app.management.commands._private import ScannerTaskCommand
from failmap.scanners.scanner import (dnssec, dummy, ftp, http, onboard, plain_http, screenshot,
                                      security_headers, tls_osaft, tls_qualys)

log = logging.getLogger(__name__)


class Command(ScannerTaskCommand):
    """Can perform a host of scans. Run like: failmap scan [scanner_name] and then options."""

    help = __doc__

    def add_arguments(self, parser):
        parser.add_argument('scanner', nargs=1, help='The scanner you want to use.')
        super().add_arguments(parser)

    def handle(self, *args, **options):

        scanners = {
            'dnssec': dnssec,
            'headers': security_headers,
            'plain': plain_http,
            'endpoints': http,
            'tls': tls_osaft,
            'tlsq': tls_qualys,
            'ftp': ftp,
            'screenshot': screenshot,
            'onboard': onboard,
            'dummy': dummy
        }

        if options['scanner'][0] not in scanners:
            print("Scanner does not exist. Please specify a scanner: %s " % scanners.keys())
            return

        self.scanner_module = scanners[options['scanner'][0]]
        super().handle(self, *args, **options)
