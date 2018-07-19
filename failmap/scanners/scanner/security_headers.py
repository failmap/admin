"""
Check if the https site uses HSTS to tell the browser the site should only be reached over HTTPS.
(useful until browsers do https by default, instead of by choice)
"""
import logging
from datetime import datetime

import pytz
import requests
import urllib3
from celery import Task, group
from constance import config
from requests import ConnectionError, ConnectTimeout, HTTPError, ReadTimeout, Timeout

from failmap.celery import IP_VERSION_QUEUE, ParentFailed, app
from failmap.organizations.models import Organization, Url
from failmap.scanners.models import Endpoint, EndpointGenericScanScratchpad
from failmap.scanners.scanmanager.endpoint_scan_manager import EndpointScanManager
from failmap.scanners.scanner.scanner import allowed_to_scan, q_configurations_to_scan

log = logging.getLogger(__name__)


@app.task(queue="storage")
def compose_task(
    organizations_filter: dict = dict(),
    urls_filter: dict = dict(),
    endpoints_filter: dict = dict(),
) -> Task:
    """Compose taskset to scan specified endpoints.
    """

    if not allowed_to_scan("scanner_security_headers"):
        return group()

    # apply filter to organizations (or if no filter, all organizations)
    # apply filter to urls in organizations (or if no filter, all urls)
    organizations = []
    if organizations_filter:
        organizations = Organization.objects.filter(**organizations_filter)
        urls = Url.objects.filter(q_configurations_to_scan(), organization__in=organizations, **urls_filter)
        log.info('Creating header scan task for %s urls for %s organizations.', len(urls), len(organizations))
    else:
        urls = Url.objects.filter(q_configurations_to_scan(), **urls_filter)
        log.info('Creating header scan task for %s urls.', len(urls))

    # select endpoints to scan based on filters
    endpoints = Endpoint.objects.filter(
        # apply filter to endpoints (or if no filter, all endpoints)
        url__in=urls, **endpoints_filter,
        # also apply mandatory filters to only select valid endpoints for this action
        is_dead=False, protocol__in=['http', 'https'])

    if not endpoints:
        log.warning('Security headers: Applied filters resulted in no tasks! organisations_filter %s, '
                    'URL Filter: %s, endpoints_filter: %s', organizations_filter, urls_filter, endpoints_filter)
        return group()

    log.info('Creating security headers scan task for %s endpoints for %s urls for %s organizations.',
             len(endpoints), len(urls), len(organizations))

    # create tasks for scanning all selected endpoints as a single managable group
    """
    It's incredibly annoying to work with options...

    TypeError: get_headers() takes 2 positional arguments but 24 were given
    signature('failmap.scanners.scanner.security_headers.get_headers', args=(endpoint.uri_url()),
                  options={'queue': IP_VERSION_QUEUE[endpoint.ip_version],
                           'immutable': True})

    TypeError: get_headers() takes 1 positional argument but 2 were given
    get_headers.signature(
            (endpoint.uri_url(),),
            options={'queue': IP_VERSION_QUEUE[endpoint.ip_version], 'immutable': True}
        ) | analyze_headers.s(endpoint) for endpoint in endpoints


    I'm done with this nonsense, and writing two explicit functions...
    """

    tasks = []
    for endpoint in endpoints:
        if endpoint.ip_version == 4:
            tasks.append(get_headers_v4.si(endpoint.uri_url()) | analyze_headers.s(endpoint))
        if endpoint.ip_version == 6:
            tasks.append(get_headers_v6.si(endpoint.uri_url()) | analyze_headers.s(endpoint))

    return group(tasks)


@app.task(queue="storage")
def analyze_headers(result: requests.Response, endpoint):
    # todo: Content-Security-Policy, Referrer-Policy

    # if scan task failed, ignore the result (exception) and report failed status
    if isinstance(result, Exception):
        return ParentFailed('skipping result parsing because scan failed.', cause=result)

    response = result

    # scratch it, for debugging.
    egss = EndpointGenericScanScratchpad()
    egss.when = datetime.now(pytz.utc)
    egss.data = "Status: %s, Headers: %s, Redirects: %s" % (response.status_code, response.headers, response.history)
    egss.type = "security headers"
    egss.domain = endpoint.uri_url()
    egss.save()

    if config.SCAN_HTTP_HEADERS_X_XSS:
        generic_check(endpoint, response.headers, 'X-XSS-Protection')

    if config.SCAN_HTTP_HEADERS_XFO:
        generic_check(endpoint, response.headers, 'X-Frame-Options')

    if config.SCAN_HTTP_HEADERS_X_CONTENT:
        generic_check(endpoint, response.headers, 'X-Content-Type-Options')

    """
    https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Strict-Transport-Security
    Note: The Strict-Transport-Security header is ignored by the browser when your site is accessed using HTTP;
    this is because an attacker may intercept HTTP connections and inject the header or remove it.  When your
    site is accessed over HTTPS with no certificate errors, the browser knows your site is HTTPS capable and will
    honor the Strict-Transport-Security header.

    7 march 2018
    After a series of complaints of products designed specifically to run on port 443 (without any non-secured port)
    we've decided that HSTS is only required if there are no unsecured (http) endpoints on this url.
    This means: if you still run (another) service on an unsecured http port, we're still demanding hsts. We're not
    able to see what product runs on what port (and it should be like that).

    The HSTS header is a sloppy patch job anyway, it will be phased out after browsers require sites to run on 443 and
    just start blocking port 80 for websites alltogether. On that day preloading also goes out the window.

    It basically works like this:
    A downgrade attack is not dependent on missing hsts. It's depending on who operates the network and if they employ
    DNS cache poisoning and use sslstrip etc. Then it comes down to your browser not accepting http at all either via
    preloading or the HSTS header (or design). The user may also trust your injected certificate given HPKP is removed
    everywhere and users will certainly click OK if they can.

    If you think it works differently, just file an issue or make a pull request. We want to get it right.
    """
    if endpoint.protocol == "https" and config.SCAN_HTTP_HEADERS_HSTS:

        # runs any unsecured http service? (on ANY port).
        unsecure_services = Endpoint.objects.all().filter(url=endpoint.url, protocol="http", is_dead=False).exists()
        if unsecure_services:
            generic_check(endpoint, response.headers, 'Strict-Transport-Security')
        else:
            if 'Strict-Transport-Security' in response.headers:
                log.debug('Has Strict-Transport-Security')
                EndpointScanManager.add_scan('Strict-Transport-Security',
                                             endpoint,
                                             'True',
                                             response.headers['Strict-Transport-Security'])
            else:
                log.debug('Has no Strict-Transport-Security, yet offers no insecure http service.')
                EndpointScanManager.add_scan('Strict-Transport-Security',
                                             endpoint,
                                             'False',
                                             "Security Header not present: Strict-Transport-Security, "
                                             "yet offers no insecure http service.")

    return {'status': 'success'}


def generic_check(endpoint: Endpoint, headers, header):
    # this is case insensitive
    if header in headers.keys():
        log.debug('Has %s' % header)
        EndpointScanManager.add_scan(header,
                                     endpoint,
                                     'True',
                                     headers[header])
    else:
        log.debug('Has no %s' % header)
        EndpointScanManager.add_scan(header,
                                     endpoint,
                                     'False',
                                     "Security Header not present: %s" % header)


def error_response_400_500(endpoint):
    # Set all headers for this endpoint to 400_500, which are not shown in the report.
    # These are not shown in the report anymore. Not using this
    EndpointScanManager.add_scan('X-XSS-Protection', endpoint, '400_500', "")
    EndpointScanManager.add_scan('X-Frame-Options', endpoint, '400_500', "")
    EndpointScanManager.add_scan('X-Content-Type-Options', endpoint, '400_500', "")

    if endpoint.protocol == "https":
        EndpointScanManager.add_scan('Strict-Transport-Security', endpoint, '400_500', "")


# Has been made explicity due to errors with the latest version of celery not allowing signature kwargs.
@app.task(bind=True, default_retry_delay=1, retry_kwargs={'max_retries': 3}, kwargs={'queue': IP_VERSION_QUEUE[4]})
def get_headers_v4(self, uri_uri):
    try:
        return get_headers(uri_uri)

    # The amount of possible return states is overwhelming :)

    # Solving https://sentry.io/internet-cleanup-foundation/faalkaart/issues/460895712/
    #         https://sentry.io/internet-cleanup-foundation/faalkaart/issues/460895699/
    # ValueError, really don't know how to further handle it.
    #
    # Solving https://sentry.io/internet-cleanup-foundation/faalkaart/issues/425503689/
    # requests.TooManyRedirects
    #
    # Solving https://sentry.io/internet-cleanup-foundation/faalkaart/issues/425507209/
    # LocationValueError - No host specified.
    # it redirects to something like https:/// (with three slashes) and then somewhere it crashes
    # possibly an error in requests.
    #
    # Possibly tooManyRedirects could be plotted on the map, given this is a configuration error
    except (ConnectTimeout, HTTPError, ReadTimeout, Timeout, ConnectionError, ValueError,
            requests.TooManyRedirects, urllib3.exceptions.LocationValueError) as e:
        # If an expected error is encountered put this task back on the queue to be retried.
        # This will keep the chained logic in place (saving result after successful scan).
        # Retry delay and total number of attempts is configured in the task decorator.
        try:
            # Since this action raises an exception itself, any code after this won't be executed.
            raise self.retry(exc=e)
        except BaseException:
            # If this task still fails after maximum retries the last
            # error will be passed as result to the next task.
            return e


@app.task(bind=True, default_retry_delay=1, retry_kwargs={'max_retries': 3}, kwargs={'queue': IP_VERSION_QUEUE[6]})
def get_headers_v6(self, uri_uri):
    try:
        return get_headers(uri_uri)

    # The amount of possible return states is overwhelming :)

    # Solving https://sentry.io/internet-cleanup-foundation/faalkaart/issues/460895712/
    #         https://sentry.io/internet-cleanup-foundation/faalkaart/issues/460895699/
    # ValueError, really don't know how to further handle it.
    #
    # Solving https://sentry.io/internet-cleanup-foundation/faalkaart/issues/425503689/
    # requests.TooManyRedirects
    #
    # Solving https://sentry.io/internet-cleanup-foundation/faalkaart/issues/425507209/
    # LocationValueError - No host specified.
    # it redirects to something like https:/// (with three slashes) and then somewhere it crashes
    # possibly an error in requests.
    #
    # Possibly tooManyRedirects could be plotted on the map, given this is a configuration error
    except (ConnectTimeout, HTTPError, ReadTimeout, Timeout, ConnectionError, ValueError,
            requests.TooManyRedirects, urllib3.exceptions.LocationValueError) as e:
        # If an expected error is encountered put this task back on the queue to be retried.
        # This will keep the chained logic in place (saving result after successful scan).
        # Retry delay and total number of attempts is configured in the task decorator.
        try:
            # Since this action raises an exception itself, any code after this won't be executed.
            raise self.retry(exc=e)
        except BaseException:
            # If this task still fails after maximum retries the last
            # error will be passed as result to the next task.
            return e


def get_headers(uri_url):
    """
    Issue #94:
    TL;DR: The fix is to follow all redirects.

    Citing: https://stackoverflow.com/questions/22077618/respect-x-frame-options-with-http-redirect
    Source: https://tools.ietf.org/html/rfc7034
    Thanks to: antoinet.

    From the terminology used in RFC 7034,

    The use of "X-Frame-Options" allows a web page from host B to declare that its content (for example, a
    button, links, text, etc.) must not be displayed in a frame (<frame> or <iframe>) of another page (e.g.,
    from host A). This is done by a policy declared in the HTTP header and enforced by browser implementations
    as documented here.

    The X-Frame-Options HTTP header field indicates a policy that specifies whether the browser should render
    the transmitted resource within a <frame> or an <iframe>. Servers can declare this policy in the header of
    their HTTP responses to prevent clickjacking attacks, which ensures that their content is not embedded
    into other pages or frames.


    Similarly, since a redirect is a flag not to render the content, the content can't be manipulated.
    This also means no X-XSS-Protection or X-Content-Type-Options are needed. So just follow all redirects.

    :return: requests.response
    """

    # ignore wrong certificates, those are handled in a different scan.
    # 10 seconds for network delay, 10 seconds for the site to respond.
    response = requests.get(uri_url, timeout=(10, 10), allow_redirects=True, verify=False)

    # Removed: only continue for valid responses (eg: 200)
    # Error pages, such as 404 are super fancy, with forms and all kinds of content.
    # it's obvious that such pages (with content) follow the same security rules as any 2XX response.
    # if 400 <= response.status_code <= 600:
    #     error_response_400_500(endpoint)
    # response.raise_for_status()

    for header in response.headers:
        log.debug('Received header: %s' % header)
    return response