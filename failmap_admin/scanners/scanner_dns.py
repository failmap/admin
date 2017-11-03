"""
Performs a range of DNS scans:
- Using Search engines
- Using Wordlists
- Using Certificate Transparency

This library deserves a cleanup.

"""
# todo: if ScannerHttp.has_internet_connection():

import logging
import subprocess

import untangle
from django.conf import settings

from failmap_admin.organizations.models import Url
from failmap_admin.scanners.scanner_http import resolves

logger = logging.getLogger(__package__)

harvester_path = settings.TOOLS['theHarvester']['executable']
dnsrecon_path = settings.TOOLS['dnsrecon']['executable']

# the length is used for checking wildcards, dnsrecon doesn't always does that right.
# if the returned list of domains is about as long as the wordlist... then it's a wildcard
# except if the wordlist is very small.
wordlists = {
    'dutch_basic': {
        'path': settings.TOOLS['dnsrecon']['wordlist_dir'] + "OpenTaal-210G-basis-gekeurd.txt",
        'length': 180000
    },
    # organizations _LOVE_ three letter acronyms! I mean TLA's! :)
    # Let's call the Anti Acronym Association of America.
    'three_letters': {
        'path': settings.TOOLS['dnsrecon']['wordlist_dir'] + "threeletterwordlist.txt",
        'length': 18000
    },
    'known_subdomains': {
        'path': settings.TOOLS['dnsrecon']['wordlist_dir'] + "knownsubdomains.txt",
        'length': 200
    },
    # We want to know if a domain uses wildcards, and also store it. So dnsrecon might be suited
    # for this, it doesn't output if a url has wildcard support.
    'nonsense': {
        'path': settings.TOOLS['dnsrecon']['wordlist_dir'] + "nonsense.txt",
        'length': 2
    }
}


# todo: move this to url logic / url manager. The resolves bit is somewhat in the way. Refactor
def add_subdomain(subdomain, url):
    fulldomain = subdomain + "." + url.url
    logger.debug("Trying to add subdomain to database: %s" % fulldomain)
    if resolves(fulldomain):
        # this doesn't add the subdomain to "missing" subsets of items (where one organization
        # misses, for example).
        if not Url.objects.all().filter(url=fulldomain,
                                        organization__in=url.organization.all()).exists():
            logger.info("Added domain to database: %s" % fulldomain)
            u = Url()
            # "<Url: >" needs to have a value for field "id" before this many-to-many
            # relationship can be used.
            u.save()
            u.organization = url.organization.all()
            u.url = fulldomain
            u.save()
            return u
        else:
            logger.debug("Subdomain already in the database: %s" % fulldomain)
    else:
        logger.debug("Subdomain did not resolve: %s" % fulldomain)
    return


def organization_search_engines_scan(organization):
    urls = Url.objects.all().filter(organization=organization,
                                    url__iregex="^[^.]*\.[^.]*$")
    # todo: what if the tld is dead / not resolvable cause the organization doesn't use it?
    # is_dead = False, not_resolvable = False

    if not urls:
        logger.info("Organization %s has no urls to investigate." % organization)

    addedlist = []
    for url in urls:
        addedlist = addedlist + search_engines_scan(url)
    return addedlist


def organization_certificate_transparency(organization):
    urls = Url.objects.all().filter(organization=organization,
                                    url__iregex="^[^.]*\.[^.]*$")

    if not urls:
        logger.info("Organization %s has no urls to investigate." % organization)

    addedlist = []
    for url in urls:
        addedlist = addedlist + certificate_transparency([url])
    return addedlist


def search_engines_scan(url):
    # Todo: sometimes the report contains subdomains for other organizations at top level domain
    # Searching the internet for subdomains might result in overly long and incorrect lists.
    # The only correct way is to curate domains by hand.
    # So, we should also try to import those. So we have maximum result from our scan.
    logger.info("Harvesting DNS of toplevel domain: %s" % url.url)
    logger.warning("Search engines have strict rate limiting, do not use this function in an "
                   "automated scan.")
    # a bug in the harvester breaks the file at the first dot and uses that as the xml file,
    # and the full filename as the html file.
    file = ("%s_harvester_all" % url.url).replace(".", "_") + ".xml"
    path = settings.TOOLS['theHarvester']['output_dir'] + file

    logger.debug("DNS results will be stored in file: %s" % path)
    engine = "all"
    subprocess.call(['python', harvester_path,
                     '-d', url.url,
                     '-b', engine,
                     '-s', '0',
                     '-l', '100',
                     '-f', path])

    # read XML file, extract hosts + vhosts (both can contain the url).
    # explicitly search for .toplevel.nl (with leading dot) to not find .blatoplevel.nl
    subdomains = []
    obj = untangle.parse(path)
    if hasattr(obj.theHarvester, 'host'):
        for host in obj.theHarvester.host:
            hostname = host.hostname.cdata
            logger.debug("Hostname: %s" % hostname)
            if hostname.endswith("." + url.url):
                subdomains.append(hostname[0:len(hostname) - len(url.url) - 1])
                logger.debug("Subdomain: %s" % hostname[0:len(hostname) - len(url.url) - 1])

    if hasattr(obj.theHarvester, 'vhost'):
        for host in obj.theHarvester.vhost:
            hostname = host.hostname.cdata
            logger.debug("Hostname: %s" % hostname)
            if hostname.endswith("." + url.url):
                subdomains.append(hostname[0:len(hostname) - len(url.url) - 1])
                logger.debug("Subdomain: %s" % hostname[0:len(hostname) - len(url.url) - 1])

    subdomains = [x.lower() for x in subdomains]
    subdomains = set(subdomains)  # only unique

    logger.debug("Found subdomains: %s" % subdomains)

    addedlist = []
    for subdomain in subdomains:
        added = add_subdomain(subdomain, url)
        if added:
            addedlist.append(added)
    return addedlist


def certificate_transparency(urls):
    """
    Checks the certificate transparency database for subdomains. Using a regex the subdomains
    are extracted. This method is extremely fast and reliable: these certificates all exist.

    Hooray for transparency :)

    :param urls: List of Url objects
    :return:
    """
    import requests
    import re

    for url in urls:

        # https://crt.sh/?q=%25.zutphen.nl
        crt_sh_url = "https://crt.sh/?q=%25." + str(url.url)
        pattern = r"[^\s%>]*\." + str(url.url.replace(".", "\."))  # harder string formatting :)

        response = requests.get(crt_sh_url, timeout=(10, 10), allow_redirects=False)
        matches = re.findall(pattern, response.text)

        subdomains = []
        for match in matches:
            # handle wildcards, sometimes subdomains have nice features.
            # examples: *.apps.domain.tld.
            # todo: perhaps store that it was a wildcard cert, for further inspection?
            match = match.replace("*.", "")
            if match != url.url:
                subdomains.append(match[0:len(match) - len(url.url) - 1])  # wraps around

        subdomains = [x.lower() for x in subdomains]  # do lowercase normalization elsewhere
        subdomains = set(subdomains)

        # 25 and '' are created due to the percentage and empty subdomains. Remove them
        # wildcards (*) are also not allowed.
        if '' in subdomains:
            subdomains.remove('')
        if '25' in subdomains:
            subdomains.remove('25')

        logger.debug("Found subdomains: %s" % subdomains)

        addedlist = []
        for subdomain in subdomains:
            added = add_subdomain(subdomain, url)
            if added:
                addedlist.append(added)
        return addedlist


# todo: very ugly parsing, should be just reading the XML output.
def subdomains_harvester(url):
    # deprecated
    # python theHarvester.py -d zutphen.nl -b google -l 100
    engine = "google"
    process = subprocess.Popen(['python', harvester_path,
                                '-d', url,
                                '-b', engine,
                                '-s', '0',
                                '-l', '100'], stdout=subprocess.PIPE)

    output = str(process.stdout.read())
    # we only care about the stuff after "[-] Resolving hostnames IPs... "
    hostnames = output[output.find("[-] Resolving hostnames IPs... ") + 32:len(output)]
    hostname_list = hostnames.split("\\n")
    subdomains = []
    for hostname in hostname_list:
        # print("Found hostname: %s" % hostname)
        if "." + url in hostname:
            subdomain_with_ip = hostname[0:hostname.find("." + url)]
            subdomain = subdomain_with_ip[subdomain_with_ip.find(
                ':') + 1:len(subdomain_with_ip)]
            subdomains.append(subdomain)
            logger.info("Found subdomain %s" % subdomain)

    return subdomains


def update_wordlist_known_subdomains():
    # todo: per branche wordlists, more to the point
    prefixes = []
    urls = Url.objects.all()
    for url in urls:
        positions = [pos for pos, char in enumerate(url.url) if char == '.']
        if len(positions) > 1:
            prefixes.append(url.url[0:positions[len(positions) - 2]])
    # print(set(prefixes))
    unique_prefixes = set(prefixes)

    with open(wordlists["known_subdomains"]["path"], "w") as text_file:
        for unique_prefix in unique_prefixes:
            text_file.write(unique_prefix + '\n')

    return unique_prefixes


def make_threeletterwordlist():
    import itertools
    alphabets = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p',
                 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z']
    threeletters = [''.join(i) for i in itertools.product(alphabets, repeat=3)]
    twoletters = [''.join(i) for i in itertools.product(alphabets, repeat=2)]

    with open("threeletterwordlist.txt", "w") as text_file:

        for x in alphabets:
            text_file.write(x + '\n')
        for x in threeletters:
            text_file.write(x + '\n')
        for x in twoletters:
            text_file.write(x + '\n')

# the chance of getting one or both domains back as existing is one in gazillions.
# but for the astronomically small chance there is another factor of gazillions.


def create_nonsense():
    import random
    import string
    letters = string.ascii_lowercase
    words = [''.join(random.choice(letters) for i in range(10)),
             ''.join(random.choice(letters) for i in range(10))]

    with open(wordlists["nonsense"]["path"], "w") as text_file:
        for word in words:
            text_file.write(word + '\n')


def organization_brute_dutch(organization):
    urls = topleveldomains(organization)
    wordlist = wordlists["dutch_basic"]["path"]
    return dnsrecon_brute(urls, wordlist)


def organization_brute_threeletters(organization):
    urls = topleveldomains(organization)
    wordlist = wordlists["three_letters"]["path"]
    return dnsrecon_brute(urls, wordlist)


# hundreds of words
# todo: language matters, many of the NL subdomains don't make sense in other countries.
# todo: don't use the subdomains that are already known to exist.
def organization_brute_knownsubdomains(organization):
    update_wordlist_known_subdomains()
    urls = topleveldomains(organization)
    wordlist = wordlists["known_subdomains"]["path"]
    return dnsrecon_brute(urls, wordlist)


def brute_known_subdomains(urls):
    update_wordlist_known_subdomains()
    wordlist = wordlists["known_subdomains"]["path"]
    return dnsrecon_brute(urls, wordlist)


def organization_standard_scan(organization):
    urls = Url.objects.all().filter(organization=organization,
                                    url__iregex="^[^.]*\.[^.]*$")
    return dnsrecon_default(urls)


def dnsrecon_brute(urls, wordlist):
    imported_urls = []
    for url in urls:
        logger.info("Bruting DNS of toplevel domain: %s" % url.url)
        logger.debug("Using wordlist: %s" % wordlist)
        file = "%s_data_brute.json" % url.url
        path = settings.TOOLS['dnsrecon']['output_dir'] + file

        logger.debug("DNS results will be stored in file: %s" % path)

        # never continue with wildcard domains
        p = subprocess.Popen(['python', dnsrecon_path,
                              '--domain', url.url,
                              '-t', 'brt',
                              '-D', wordlist,
                              '-j', path], stdin=subprocess.PIPE)
        p.stdin.write('n'.encode(encoding='utf-8'))
        p.stdin.write('n'.encode(encoding='utf-8'))
        p.stdin.write('n'.encode(encoding='utf-8'))
        p.stdin.write('n'.encode(encoding='utf-8'))
        p.stdin.write('n'.encode(encoding='utf-8'))
        p.stdin.write('n'.encode(encoding='utf-8'))  # never brute a wildcard,
        # The above input doens't always work it seems...
        p.communicate()

        imported_urls = imported_urls + import_dnsrecon_report(url, path)

    return imported_urls


def dnsrecon_default(urls):
    # todo: Expanding IP ranges found in DNS and TXT records for Reverse Look-up takes ages.
    # This is due to expansion of IPv6 addresses, which is extreme and sometimes impossible
    # Since dnsrecon doesn't give the option to time-out or skip this expansion...
    # so no std for us :'( - or timeout this method (and skipping meaningful results) or patch
    # dnsrecon.
    # This doesn't ask google, the harvester is a bit more smarter / advanced.
    imported_urls = []
    for url in urls:
        logger.info("Scanning DNS of toplevel domain: %s" % url.url)
        file = "%s_data_default.json" % url.url
        path = settings.TOOLS['dnsrecon']['output_dir'] + file

        logger.debug("DNS results will be stored in file: %s" % path)

        # never continue with wildcard domains
        p = subprocess.Popen(['python', dnsrecon_path,
                              '--type', '"rvl,srv,axfr,snoop,zonewalk"'
                              '--domain', url.url,
                              '-j', path], stdin=subprocess.PIPE)
        p.stdin.write('n'.encode(encoding='utf-8'))
        p.stdin.write('n'.encode(encoding='utf-8'))
        p.stdin.write('n'.encode(encoding='utf-8'))
        p.stdin.write('n'.encode(encoding='utf-8'))
        p.stdin.write('n'.encode(encoding='utf-8'))
        p.stdin.write('n'.encode(encoding='utf-8'))  # never brute a wildcard,
        # The above input doens't always work it seems...
        p.communicate()

        imported_urls = imported_urls + import_dnsrecon_report(url, path)

    return imported_urls


# This helps to determine at database level if the DNS uses wildcards, so it can be dealt
# with in another way.
def topleveldomains(organization):
    # todo: move to manager, expand the queryset with the uses dns wildcard.
    topleveldomains = Url.objects.all().filter(organization=organization,
                                               url__iregex="^[^.]*\.[^.]*$",
                                               uses_dns_wildcard=False)

    non_wildcard_toplevel_domains = []
    # inspect if the url employs wildcards. If so, register it and make it a point of
    # interest for people to test this by hand (or more advanced scanners)

    for url in topleveldomains:
        if url_uses_wildcards(url):
            logger.info("Domain %s uses wildcards, DNS brute force not possible" % url.url)
            url.uses_dns_wildcard = True
            url.save()
        else:
            non_wildcard_toplevel_domains.append(url)

    if not non_wildcard_toplevel_domains:
        logger.info("No top level domain available without wildcards.")

    return non_wildcard_toplevel_domains


def url_uses_wildcards(url):
    """
    We need to perform a check ourselves, since we cannot get from the DNSRecon report if the url
    uses wildcards. We store this ourselves so we can better filter domains.

    In some cases DNSrecon makes a wrong assumption about wildcard usage. This is hopefully a bit better.
    """
    logger.debug("Checking for DNS wildcards on domain: %s" % url.url)
    file = "%s_data_wildcards.json" % url.url
    path = settings.TOOLS['dnsrecon']['output_dir'] + file

    logger.debug("DNS results will be stored in file: %s" % path)

    # never continue with wildcard domains
    create_nonsense()
    p = subprocess.Popen(['python', dnsrecon_path,
                          '--domain', url.url,
                          '-t', 'brt',
                          '--iw',  # always try wild card domains.
                          '-D', wordlists["nonsense"]["path"],
                          '-j', path], stdin=subprocess.PIPE)
    p.communicate()

    import json
    wildcard = False
    with open(path) as data_file:
        data = json.load(data_file)
        for record in data:
            if "arguments" in record.keys():
                continue

            if record["name"].endswith(url.url):
                wildcard = True

    return wildcard


def dnsrecon_google():
    raise NotImplemented
    # todo: make this new manual scan.
    # requires: netaddr, dnspython
    # Dictionaries of the local language are available on wiktionary.
    # https://nl.wiktionary.org/wiki/WikiWoordenboek:OpenTaal
    # https://www.opentaal.org/

    # Brute force op DNS:
    # python dnsrecon.py --domain amsterdam.nl -j output_brt.json


def import_dnsrecon_report(url, path):
    # note: the order of the records in the report matters(!)

    import json
    with open(path) as data_file:
        data = json.load(data_file)
        addedlist = []
        for record in data:
            # brutally ignore all kinds of info from other structures.
            logger.debug("Record: %s" % record)
            # https://stackoverflow.com/questions/11328940/check-if-list-item-contains-items-fro
            bad = ["arguments", "ns_server", "mname", "Version", "exchange"]
            my_list = list(record.keys())
            if [e for e in bad if e in '\n'.join(my_list)]:
                continue

            if record["name"].endswith(url.url):
                subdomain = record["name"][0:len(record["name"]) - len(url.url) - 1]
                # print(subdomain.lower())
                added = add_subdomain(subdomain.lower(), url)
                if added:
                    addedlist.append(added)
    return addedlist
