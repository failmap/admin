import logging

from failmap.app.management.commands._private import ScannerTaskCommand
from failmap.scanners.scanner import debug, dnssec, dummy, ftp, mail, onboard, plain_http, security_headers, tls_qualys

log = logging.getLogger(__name__)

scanners = {
    'onboard': onboard,
    'dummy': dummy,
    'debug': debug,
    'dnssec': dnssec,
    'headers': security_headers,
    'plain': plain_http,
    'tlsq': tls_qualys,
    'ftp': ftp,
    'mail': mail
}


class Command(ScannerTaskCommand):
    """ Can perform a host of scans. Run like: failmap scan [scanner_name] and then options."""

    help = __doc__

    def add_arguments(self, parser):
        parser.add_argument('scanner', nargs=1, help='The scanner you want to use.', choices=scanners)
        super().add_arguments(parser)

    def handle(self, *args, **options):

        try:
            if options['scanner'][0] not in scanners:
                print("Scanner does not exist. Please specify a scanner: %s " % scanners.keys())
                return

            self.scanner_module = scanners[options['scanner'][0]]
            return super().handle(self, *args, **options)

        except KeyboardInterrupt:
            log.info("Received keyboard interrupt. Stopped.")
