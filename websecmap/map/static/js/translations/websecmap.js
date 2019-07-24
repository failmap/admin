// Contains fallback messages which will slowly be moved to components. In the end this contains app messages
// and things that are used in many components (which are vulnerabilities etc, which are also in app).

const messages = {
    en: {
        // new translations
        back_to_map: "Back to the map",

        // layers
        municipality: 'Municipalities',
        cyber: 'Cyber',
        unknown: 'Unknown',
        water_board: 'Water boards',
        province: 'Provinces',
        country: 'Country',
        region: 'Region',
        county: 'County',
        district: 'District',
        government: 'Government',
        healthcare: 'Healthcare',
        finance: 'Finance',
        state: 'State',
        education: 'Education',

        // german layers... sigh... :)
        bundesland: '',
        regierungsbezirk: '',
        landkreis_kreis_kreisfreie_stadt: '',
        samtgemeinde_verwaltungsgemeinschaft: '',
        stadt_gemeinde: '',
        stadtbezirk_gemeindeteil_mit_selbstverwaltung: '',
        stadtteil_gemeindeteil_ohne_selbstverwaltung: '',

        // categories:
        confidentiality: "Confidentiality",
        integrity: "Integrity",
        website: "Website",

        // issues, are used at various places, the original value comes from the database stored as scan results.
        // this is an issue with a spelling error :)
        "Site does not redirect to secure url, and has nosecure alternative on a standard port.": "--test--",

        "Site does not redirect to secure url, and has no secure alternative on a standard port.": "--test--",
        "Has a secure equivalent, which wasn't so in the past.": "--test--",
        "Redirects to a secure site, while a secure counterpart on the standard port is missing.": "--test--",
        "Broken Transport Security, rated F": "--test--",
        "Certificate not valid for domain name.": "--test--",
        "Less than optimal Transport Security, rated C.": "--test--",
        "Less than optimal Transport Security, rated B.": "--test--",
        "Good Transport Security, rated A-.": "--test--",
        "Good Transport Security, rated A.": "--test--",
        "Perfect Transport Security, rated A+.": "--test--",
        "X-Content-Type-Options header present.": "--test--",
        "Missing X-Content-Type-Options header.": "--test--",
        "X-XSS-Protection header present.": "--test--",
        "Missing X-XSS-Protection header.": "--test--",
        "X-Frame-Options header present.": "--test--",
        "Missing X-Frame-Options header.": "--test--",
        "Strict-Transport-Security header present.": "--test--",
        "Missing Strict-Transport-Security header.": "--test--",
        "Missing Strict-Transport-Security header. Offers no insecure alternative service.": "--test--",
        "DNSSEC is incorrectly or not configured (errors found).": "--test--",
        "DNSSEC seems to be implemented sufficiently.": "--test--",
        "FTP Server only supports insecure SSL protocol.": "--test--",
        "FTP Server does not configured to show if encryption is available.": "--test--",
        "FTP Server supports TLS encryption protocol.": "--test--",
        "FTP Server does not support encrypted transport or has protocol issues.": "--test--",
        "An FTP connection could not be established properly. Not possible to verify encryption.": "--test--",
        "not trusted": "--test--",
        "trusted": "--test--",
        "Certificate is not trusted.": "--test--",
        "Certificate is trusted.": "--test--",
        "Content-Security-Policy header found, which covers the security aspect of the X-Frame-Options header.": "--test--",
        "Content-Security-Policy header found, which covers the security aspect of the X-XSS-Protection header.": "--test--",
        "STARTTLS Available": "--test--",
        "STARTTLS Missing": "--test--",
        "SPF Available": "--test--",
        "SPF Missing": "--test--",
        "DKIM Available": "--test--",
        "DKIM Missing": "--test--",
        "DMARC Available": "--test--",
        "DMARC Missing": "--test--",
        "DANE Available": "--test--",
        "DANE Missing": "--test--",
        "Strict-Transport-Security": "--test--",
        "X-Content-Type-Options": "--test--",
        "X-Frame-Options": "--test--",
        "X-XSS-Protection": "--test--",
        "plain_https": "Missing transport encryption (HTTP only)",
        "tls_qualys": "--test--",
        "DNSSEC": "--test--",
        "ftp": "--test--",
        "tls_qualys_encryption_quality": "--test--",
        "tls_qualys_certificate_trusted": "--test--",
        "http_security_header_strict_transport_security": "--test--",
        "http_security_header_x_frame_options": "--test--",
        "http_security_header_x_content_type_options": "--test--",
        "http_security_header_x_xss_protection": "--test--",
        "internet_nl_mail_starttls_tls_available": "--test--",
        "internet_nl_mail_auth_spf_exist": "--test--",
        "internet_nl_mail_auth_dkim_exist": "--test--",
        "internet_nl_mail_auth_dmarc_exist": "--test--",
        "Stats hasn\'t": "--test--",
        "Stats has": "--test--",
        "Broken": "--test--",
        "TLS rated C": "--test--",
        "TLS rated B": "--test--",
        "TLS rated A": "--test--",
        "TLS rated A-": "--test--",
        "TLS rated A+": "--test--",
        "Not at all": "--test--",
        "Redirect from unsafe address": "--test--",
        "FTP Insecure": "--test--",
        "FTP": "--test--",
    },
    nl: {


    }
};
