import logging

from failmap.app.management.commands._private import VerifyTaskCommand
from failmap.scanners.scanner import ftp, http

log = logging.getLogger(__name__)


class Command(VerifyTaskCommand):
    """Can perform a host of scans. Run like: failmap scan [scanner_name] and then options."""

    help = __doc__

    # todo: subdomains, from scanner.dns
    scanners = {
        'ftp': ftp,
        'http': http,
    }

    def add_arguments(self, parser):
        parser.add_argument('scanner', nargs=1, help='The scanner you want to use.', choices=self.scanners)
        super().add_arguments(parser)

    def handle(self, *args, **options):

        if options['scanner'][0] not in self.scanners:
            print("Scanner does not exist. Please specify a scanner: %s " % self.scanners.keys())
            return

        self.scanner_module = self.scanners[options['scanner'][0]]
        return super().handle(self, *args, **options)
