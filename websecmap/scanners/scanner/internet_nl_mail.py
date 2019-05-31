"""
Scans using internet.nl API.
Docs: https://batch.internet.nl/api/batch/documentation/

The Internet.nl scanner scans for a lot of things at the same time. We scan all those results, even though we might not
display them all. It might mean that some scans have a relationsship with each other.

This scanner focusses on the availability and implementation of SPF, DKIM, DMARC, DNSSEC and STARTTLS.

A scan is run in a batch of maximum 5000 urls. A batch request is made and then stored. A periodic task checks if there
are updates to the scan. If so, the updates are processed and on a good day the scan is closed and saved.

Since the result url stays valid for a while, you can port it to another server without costing more resources on i.nl.

A batch scan will take at least 30 minutes and can last days. Please don't add too much scans, as you'll get kicked.

To know what domains we need to scan, it's possible to search for domains with MX records using 'failmap discover mail'.
This optimization saves about 80% of resources, which is a whole lot.

Given this scanner is slow, we cannot add this to the onboarding routine unfortunately.

Todo:
[X] Store API username
[X] Store API password
[X] Request a scan
[X] Read a scan status
[X] Return the scan results
[X] Store the scan results
[X] Run a dig on a subdomain for MX records. If MX, then add to scan. If not, how do you delete / invalidate the scans?
[X] Schedule a scan request every 7 days
[X] Add MX records every 5 days
[X] Schedule the update task every 30 minutes
[ ] Create reports and relationships of findings. Also determine severity etc.
[ ] Handle NO MX return messages, do not save those scans and remove the capability... what happens with the last
    scan result....????

Commands:
# Search for MX records
failmap discover mail -o Zutphen

# scan the quality of the mail of an organization, only registers a scan
failmap scan mail -o Zutphen

# request the status of a scan, can finish the scan when ready
failmap internetnl_status_update

You can load up this file in ipython and run test_store() if needed.
"""

import logging
import uuid
from datetime import datetime
from typing import List

import pytz
import requests
from celery import Task, group
from constance import config
from requests.auth import HTTPBasicAuth

from websecmap.celery import app
from websecmap.organizations.models import Url
from websecmap.scanners.models import Endpoint, InternetNLScan
from websecmap.scanners.scanmanager import store_endpoint_scan_result
from websecmap.scanners.scanner.__init__ import (allowed_to_scan, q_configurations_to_scan,
                                                 url_filters)

log = logging.getLogger(__name__)


API_URL_MAIL = "https://batch.internet.nl/api/batch/v1.1/mail/"
MAX_INTERNET_NL_SCANS = 5000

# while internet.nl scans on port 25
# (see https://github.com/NLnetLabs/Internet.nl/blob/f003365b1d560bdfbb5bd772d735a41696277639/checks/tasks/tls.py)
# we will see if SMTP works on both standard ports.


def compose_task(
    organizations_filter: dict = dict(),
    urls_filter: dict = dict(),
    endpoints_filter: dict = dict(),
    **kwargs
) -> Task:

    if not allowed_to_scan("internet_nl_mail"):
        return group()

    default_filter = {"is_dead": False, "not_resolvable": False}
    urls_filter = {**urls_filter, **default_filter}
    urls = Url.objects.all().filter(q_configurations_to_scan(level='url'), **urls_filter)

    endpoints_filter = {'is_dead': False, "protocol": 'dns_mx_no_cname'}
    urls = url_filters(urls, organizations_filter, urls_filter, endpoints_filter)

    if not urls:
        log.warning('Applied filters resulted in no urls, thus no mail scan tasks!')
        return group()

    urls = list(set(urls))

    # do all in one. Throw exception at more than 5000.
    if len(urls) >= MAX_INTERNET_NL_SCANS:
        raise ValueError("Attempting to scan more than 5000 urls on internet.nl, which is above the daily limit. "
                         "Slice your scan requests to be at maximum 5000 urls per day.")

    log.info('Creating internetnl mail scan task for %s urls.', len(urls))

    return group([register_scan.si(urls, config.INTERNET_NL_API_USERNAME, config.INTERNET_NL_API_PASSWORD, 'mail',
                                   API_URL_MAIL)])


@app.task(queue='storage')
def check_running_scans():
    """
    Gets status on all running scans from internet, and try to handle/finish the scan when possible.

    This is not a task for Celery exponential backoffs, for the simple reason a scan can take a day or two and the queue
    might reset and stuff. Also someone might want to copy the result urls into other systems.

    :return: None
    """

    unfinished_scans = InternetNLScan.objects.all().filter(finished=False)
    for scan in unfinished_scans:
        response = get_scan_status(scan.status_url, config.INTERNET_NL_API_USERNAME, config.INTERNET_NL_API_PASSWORD)
        handle_running_scan_reponse(response, scan)


@app.task(queue='storage')
def get_scan_status(url, username, password):
    try:
        response = requests.get(
            url,
            auth=HTTPBasicAuth(username, password),
            # a massive timeout for a large file.
            timeout=(300, 300)
        )
        return response.json()
    except requests.exceptions.ConnectionError:
        log.exception("Could not connect to batch.internet.nl")
        return {}


@app.task(queue='storage')
def handle_running_scan_reponse(response, scan):
    """
    Some status messages you can expect:
        "message": "Batch request is registering domains",
        "message": "Batch request is running",
        "message": "Results are being generated",
    """

    if not response:
        log.debug('Recceived no updates from internet.nl')
        return None

    scan.message = response['message']
    scan.friendly_message = response['message']
    log.debug("Scan %s: %s" % (scan.pk, response['message']))

    if response['message'] == "OK":
        log.debug("Hooray, a scan has finished.")
        scan.finished = True
        # We'll NOT set the scan finished_on value just yet, as the new values need to be stored.
        # Reporting checks the finished on date, and tries to find the latest values 'before' that date...
        # if the values are updated after the date, we'll miss out on report data.
        # As this is async, there is no guarantee the finished on date is at a set time. It could be 10 minutesm
        # it could be 10 months.
        # scan.finished_on = datetime.now(pytz.utc)
        scan.success = True
        scan.message = response['message']
        scan.friendly_message = "Scan has finished."
        log.debug("Going to process the scan results.")

        # See above why finished on is stored later.
        (store.si(response, scan.type) | set_finished_on_date.si(scan)).apply_async()
        # store.apply_async([response, scan.type])

    if response['message'] in ["Error while registering the domains" or "Problem parsing domains"]:
        log.debug("Scan encountered an error.")
        scan.finished = True
        scan.finished_on = datetime.now(pytz.utc)

    scan.save()

    return None


@app.task(queue="storage")
def set_finished_on_date(scan):
    log.debug('Updating finished date for scan %s' % scan)
    scan.finished_on = datetime.now(pytz.utc)
    scan.save(update_fields=['finished_on'])


# exp backoff 2 = 2, 4, 8, 16, 32, 64, 128, 256 seconds
@app.task(queue="storage", autoretry_for=(Exception,), retry_backoff=True, retry_kwargs={'max_retries': 10},
          retry_jitter=False)
def register_scan(urls: List[Url], username, password, internet_nl_scan_type: str = 'mail', api_url: str = "",
                  scan_name: str = ""):
    """
    This registers a scan and results the URL where the scan results can be found later on.

    :param urls:
    :param username:
    :param password:
    :return:
    """

    """
    Register scan request:
    POST /api/batch/v1.0/web/ HTTP/1.1
    {
        "name": "My web test",
        "domains": ["nlnetlabs.nl", "www.nlnetlabs.nl", "opennetlabs.nl", "www.opennetlabs.nl"]
    }
    """
    scan_id = str(uuid.uuid4())
    urls = [url.url for url in urls]

    if scan_name:
        scan_name += " %s" % scan_id
    else:
        scan_name = "Web Security Map Scan %s" % scan_id

    data = {"name": scan_name, "domains": urls}
    answer = requests.post(api_url, json=data, auth=HTTPBasicAuth(username, password), timeout=(300, 300))
    log.debug("Received answer from internet.nl: %s" % answer.content)

    answer = answer.json()

    check_correct_user(answer)
    check_api_version(answer)

    """
    Expected answer:
    HTTP/1.1 200 OK
    Content-Type: application/json
    {
        "success": true,
        "message": "OK",
        "data": {
            "results": "https://batch.internet.nl/api/batch/v1.0/results/01c70c7972d143ffb0c5b45d5b8116cb/"
        }
    }
    """
    status_url = get_status_url(answer)
    log.debug('Received scan status url: %s' % status_url)

    scan = InternetNLScan()
    scan.started_on = datetime.now(pytz.utc)
    scan.started = True
    scan.status_url = status_url
    scan.message = answer.get('message', 'No message received.')
    scan.friendly_message = "Batch request has been registered"
    scan.type = internet_nl_scan_type

    scan.save()

    return scan


def check_correct_user(answer):
    # handle an unknown user error:
    if answer.get("message", None) == "Unknown user":
        raise AttributeError("Unknown user. Did you configure your internet.nl username and password?")


def check_api_version(answer):
    # handle API upgrades
    if answer.get("message", None) == "Make sure you are using a valid URL with the current batch API version (1.0)":
        raise AttributeError("API Changed. Review the documentation at "
                             "batch.internet.nl using your internet.nl credentials")


def get_status_url(answer):
    # When there are issues registering a scan, this message is returned, and data is not a dict but a list, a bug
    # in the internet.nl API. For python it does not matter if it's an empty [] or {}, so that's fine.
    # Received answer from internet.nl: b'{"message": "Problem parsing domains", "data": [], "success": false}'
    if not answer:
        return ''

    status_url = answer.get('data', {}).get('results', "")
    if not status_url:
        raise AttributeError("Could not get scanning status url. Response from server: %s" % answer)

    return status_url


@app.task(queue='storage')
def store(result: dict, internet_nl_scan_type: str = 'mail'):
    # Done: is the status set to finished AS SOON AS this is requested? Otherwise every half hour this data
    # will be added to be processed. As it might take some time before this task is processed. This is OK as the
    # Finished value is set before calling this. And this is called asycnronously.
    #
    """
    :param result: json blob from internet.nl
    :param internet_nl_scan_type: mail, mail_dashboard or web
    """

    # supported scan types: They determine what type of endpoint the scan results are stored at.
    scan_type_to_protocol = {'mail': 'dns_mx_no_cname', 'mail_dashboard': 'dns_soa', 'web': 'dns_a_aaaa'}

    domains = result.get('data', {}).get('domains', {})
    if not domains:
        raise AttributeError("Domains missing from scan results. What's going on?")

    for domain in domains:

        log.debug(domain)

        if domain['status'] != "ok":
            log.debug("%s scan failed on %s" % (internet_nl_scan_type, domain['domain']))
            continue

        # try to match the endpoint. Internet nl scans target port 25 and ipv4 primarily.
        endpoint = Endpoint.objects.all().filter(protocol=scan_type_to_protocol[internet_nl_scan_type],
                                                 url__url=domain['domain'],
                                                 is_dead=False).first()

        if not endpoint:
            log.debug("No matching endpoint found, perhaps this was deleted / resolvable meanwhile. Skipping")
            continue

        # link changes every time, so can't save that as message.
        store_endpoint_scan_result(
            scan_type='internet_nl_%s_overall_score' % internet_nl_scan_type,
            endpoint=endpoint,
            rating=domain['score'],
            message='ok',
            evidence=domain['link']
        )

        # startls, dane etc.
        for category in domain['categories']:
            scan_type = 'internet_nl_%s_%s' % (internet_nl_scan_type, category['category'])
            store_endpoint_scan_result(
                scan_type=scan_type,
                endpoint=endpoint,
                rating=category['passed'],
                message='',
                evidence=domain['link']
            )

        # don't overwrite domain['views'] here, as that somehow does not work.
        views = inject_legacy_views(internet_nl_scan_type, domain['views'])

        # icons: https://github.com/NLnetLabs/Internet.nl/tree/cece8255ac7f39bded137f67c94a10748970c3c7/checks/static
        # Is not testable: icon-not-tested-question-mark.svg
        # Not applicable: icon-not-tested.svg
        # will be changed from true, false to passed, info, warning, failed.
        # main chart: score divide by domain names (don't need to calculate yourself)

        # Requirement levels: Required, Recommended, Optional,  Not Applicable
        # Resultaten: Pass, Fail, Not Testable,                 Not Applicable
        #
        # Pass = Pass on any (Required, Recommended, Optional)
        # Warning = Fail, Recommended
        # Info = Fail, Optional
        # Fail = Fail, Required
        # Not Applicable = Not Applicable, Not Applicable (something made it not applicable)
        # Not Tested = (Required, Recommended, Optional),
        #               Not Testable... Can be any requirement: (Required, Recommended, Optional)
        #
        # DKIM is dan: Required maar kan Not Applicable zijn als bepaalde andere velden dat aangeven.
        # https://www.internet.nl/faqs/report/

        views = upgrade_api_response(internet_nl_scan_type, domain['views'])

        # tons of specific views and scan values that might be valuable to report on. Save all of them.
        for view in views:
            scan_type = 'internet_nl_%s' % view['name']
            store_endpoint_scan_result(
                scan_type=scan_type,
                endpoint=endpoint,
                rating=view['result'],
                message='',
                evidence=domain['link']
            )


def upgrade_api_response(internet_nl_scan_type, views):
    return views


def inject_legacy_views(scan_type, views):

    # If a number of conditions are positive, then another 'view' is set to True. Otherwise to false.
    # These views are backwards compatible with previous reports. (column j)
    # todo: have to verify if these are the correct colums
    if scan_type in ["web"]:
        web_legacy_prefix = 'web_legacy_'

        # forum standardisatie magazine = DNSSEC
        # todo: new value, add this to report
        views.append({
            'name': web_legacy_prefix + 'dnssec',
            'result': true_when_all_match(
                views,
                ['web_dnssec_exist', 'web_dnssec_valid']
            )
        })

        # forum standardisatie magazine = TLS
        views.append({
            'name': web_legacy_prefix + 'tls_available',
            'result': true_when_all_match(
                views,
                ['web_https_http_available']
            )
        })

        # forum standardisatie magazine = TLS_NCSC
        # todo: not in report yet
        views.append({
            'name': web_legacy_prefix + 'tls_ncsc_web',
            'result': true_when_all_match(
                views,
                ['web_https_tls_version', 'web_https_tls_ciphers', 'web_https_tls_keyexchange',
                 'web_https_tls_compress', 'web_https_tls_secreneg', 'web_https_tls_clientreneg',
                 'web_https_cert_chain', 'web_https_cert_pubkey', 'web_https_cert_sig', 'web_https_cert_domain']
            )
        })

        # forum standardisatie magazine = HTTPS
        views.append({
            'name': web_legacy_prefix + 'https_enforced',
            'result': true_when_all_match(
                views,
                ['web_https_http_redirect']
            )
        })

        # forum standardisatie magazine = HSTS
        views.append({
            'name': web_legacy_prefix + 'hsts',
            'result': true_when_all_match(
                views,
                ['web_https_http_hsts']
            )
        })

        # Not in forum standardisatie magazine, but used internally
        views.append({
            'name': web_legacy_prefix + 'ipv6_nameserver',
            'result': true_when_all_match(
                views,
                ['web_ipv6_ns_address', 'web_ipv6_ns_reach']
            )
        })

        # Not in forum standardisatie magazine, but used internally
        views.append({
            'name': web_legacy_prefix + 'ipv6_webserver',
            'result': true_when_all_match(
                views,
                ['web_ipv6_ws_address', 'web_ipv6_ws_reach', 'web_ipv6_ws_similar']
            )
        })

        # Not in forum standardisatie magazine, but used internally
        views.append({
            'name': web_legacy_prefix + 'dane',
            'result': true_when_all_match(
                views,
                ['web_https_dane_exist', 'web_https_dane_valid']
            )
        })

    # Also add a bunch of legacy fields for mail, on the condition that all are true.
    if scan_type in ["mail", "mail_dashboard"]:
        mail_legacy_prefix = "mail_legacy_"

        # forum standardisatie magazine = DMARC
        views.append({
            'name': mail_legacy_prefix + 'dmarc',
            'result': true_when_all_match(
                views,
                ['mail_auth_dmarc_exist']
            )
        })

        # forum standardisatie magazine = DKIM
        views.append({
            'name': mail_legacy_prefix + 'dkim',
            'result': true_when_all_match(
                views,
                ['mail_auth_dkim_exist']
            )
        })

        # forum standardisatie magazine = SPF
        views.append({
            'name': mail_legacy_prefix + 'spf',
            'result': true_when_all_match(
                views,
                ['mail_auth_spf_exist']
            )
        })

        # forum standardisatie magazine = DMARC Policy
        views.append({
            'name': mail_legacy_prefix + 'dmarc_policy',
            'result': true_when_all_match(
                views,
                ['mail_auth_dmarc_policy_only']
            )
        })

        # forum standardisatie magazine = SPF Policy
        views.append({
            'name': mail_legacy_prefix + 'spf_policy',
            'result': true_when_all_match(
                views,
                ['mail_auth_spf_policy']
            )
        })

        # forum standardisatie magazine = START TLS
        views.append({
            'name': mail_legacy_prefix + 'start_tls',
            'result': true_when_all_match(
                views,
                ['mail_starttls_tls_available']
            )
        })

        # forum standardisatie magazine = START TLS NCSC
        # mail_starttls_cert_domain is mandatory ONLY when mail_starttls_dane_ta is True.
        # And only then it should be in the view.
        start_tls_ncsc_fields = \
            ['mail_starttls_tls_available', 'mail_starttls_tls_version', 'mail_starttls_tls_ciphers',
             'mail_starttls_tls_keyexchange', 'mail_starttls_tls_compress', 'mail_starttls_tls_secreneg',
             'mail_starttls_cert_pubkey', 'mail_starttls_cert_sig']

        for view in views:
            if view['name'] == 'mail_starttls_dane_ta' and view['result'] is True:
                start_tls_ncsc_fields.append('mail_starttls_cert_domain')

        views.append({
            'name': mail_legacy_prefix + 'start_tls_ncsc',
            'result': true_when_all_match(
                views,
                start_tls_ncsc_fields
            )
        })

        # Not in forum standardisatie magazine, but used internally
        views.append({
            'name': mail_legacy_prefix + 'dnssec_email_domain',
            'result': true_when_all_match(
                views,
                ['mail_dnssec_mailto_exist', 'mail_dnssec_mailto_valid']
            )
        })

        # forum standardisatie magazine = DNSSEC MX
        views.append({
            'name': mail_legacy_prefix + 'dnssec_mx',
            'result': true_when_all_match(
                views,
                ['mail_dnssec_mx_exist', 'mail_dnssec_mx_valid']
            )
        })

        # forum standardisatie magazine = DANE
        views.append({
            'name': mail_legacy_prefix + 'dane',
            'result': true_when_all_match(
                views,
                ['mail_starttls_dane_exist', 'mail_starttls_dane_valid']
            )
        })

        # Not in forum standardisatie magazine, but used internally
        views.append({
            'name': mail_legacy_prefix + 'ipv6_nameserver',
            'result': true_when_all_match(
                views,
                ['mail_ipv6_ns_adddress', 'mail_ipv6_ns_reach']
            )
        })

        # Not in forum standardisatie magazine, but used internally
        views.append({
            'name': mail_legacy_prefix + 'ipv6_mailserver',
            'result': true_when_all_match(
                views,
                ['mail_ipv6_mx_address', 'mail_ipv6_mx_reach']
            )
        })

        # todo: remove / change in translations:
        # dnsssec_mailserver_domain is now dnssec_mx
        # tls_available is now start_tls

    return views


def true_when_all_match(views, values) -> {}:

    if not views:
        raise ValueError('No views provided. Something went wrong in the API response?')

    if not values:
        raise ValueError('No values provided. Would always result in True, which could be risky.')

    for view in views:
        if view['name'] in values:
            if not view['result']:
                return False

    return True
