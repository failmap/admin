"""This module is imported by failmap.__init__ to register Signal hooks."""

import logging
import shutil
import sys
import tempfile

from celery.signals import celeryd_init, worker_shutdown
from django.conf import settings

from .celery.worker import tls_client_certificate, worker_configuration

log = logging.getLogger(__name__)


@celeryd_init.connect
def configure_workers(sender=None, conf=None, **kwargs):
    """Configure workers when Celery is initialized."""

    try:
        # create a universal temporary directory to be removed when the application quits
        settings.WORKER_TMPDIR = tempfile.mkdtemp()
        # configure worker queues
        conf.update(worker_configuration())

        # for remote workers configure TLS key and certificate from PKCS12 file
        conf.update(tls_client_certificate())
    except BaseException:
        log.exception('Failed to setup worker configuration!')
        sys.exit(1)


@worker_shutdown.connect
def cleanup_certificates(sender=None, conf=None, **kwargs):
    """Remove worker temporary directory."""

    shutil.rmtree(settings.WORKER_TMPDIR)
