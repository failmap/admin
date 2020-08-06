"""
Implementation of Internet.nl API v2.0

Docs: https://api.internet.nl/v2/documentation/

Internet.nl scans for modern web and web standards. Such as https, dnssec, security headers, etc
"""

import logging

from celery import Task, group

from websecmap.celery import app
from websecmap.organizations.models import Url
from websecmap.scanners import plannedscan
from websecmap.scanners.scanner.__init__ import (allowed_to_scan, q_configurations_to_scan,
                                                 unique_and_random, url_filters)
from websecmap.scanners.scanner.internet_nl_v2_websecmap import initialize_scan

log = logging.getLogger(__name__)


def filter_scan(organizations_filter: dict = dict(),
                urls_filter: dict = dict(),
                endpoints_filter: dict = dict(),
                **kwargs):
    default_filter = {"is_dead": False, "not_resolvable": False}
    urls_filter = {**urls_filter, **default_filter}
    urls = Url.objects.all().filter(q_configurations_to_scan(level='url'), **urls_filter)

    endpoints_filter = {'is_dead': False, "protocol": 'dns_a_aaaa'}
    urls = url_filters(urls, organizations_filter, urls_filter, endpoints_filter)
    urls = urls.only("url")

    urls = unique_and_random(urls)

    return urls


@app.task(queue='storage')
def compose_planned_scan_task(**kwargs):
    urls = plannedscan.pickup(activity="scan", scanner="internet_nl_v2_web", amount=kwargs.get('amount', 500))
    return compose_scan_task(urls)


@app.task(queue='storage')
def plan_scan(organizations_filter: dict = dict(),
              urls_filter: dict = dict(),
              endpoints_filter: dict = dict(),
              **kwargs
              ):

    if not allowed_to_scan("internet_nl_web"):
        return group()

    urls = filter_scan(organizations_filter, urls_filter, endpoints_filter, **kwargs)
    plannedscan.request(activity="scan", scanner="internet_nl_v2_web", urls=urls)


def compose_scan_task(urls):
    return group([initialize_scan.si("web", urls)
                  | plannedscan.finish_multiple.si('scan', 'internet_nl_v2_web', urls)])


def compose_manual_scan_task(
    organizations_filter: dict = dict(),
    urls_filter: dict = dict(),
    endpoints_filter: dict = dict(),
    **kwargs
) -> Task:
    if not allowed_to_scan("internet_nl_web"):
        return group()

    urls = filter_scan(organizations_filter, urls_filter, endpoints_filter, **kwargs)
    log.info('Creating internet.nl api web scan task for %s urls.', len(urls))
    return compose_scan_task(urls)
