# coding=UTF-8
# from __future__ import unicode_literals

import logging
from datetime import datetime, timedelta

import pytz
import tldextract
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _
from django_countries.fields import CountryField
from djgeojson.fields import GeoJSONField
from jsonfield import JSONField

log = logging.getLogger(__package__)


class OrganizationType(models.Model):
    name = models.CharField(max_length=255, verbose_name=_("organization type"))

    class Meta:
        managed = True
        verbose_name = _('organization_type')
        verbose_name_plural = _('organization_types')

    def __str__(self):
        return self.name


def validate_twitter(value):
    if value[0:1] != "@":
        raise ValidationError('Twitter handle needs to start with an @ symbol.')


class Organization(models.Model):
    country = CountryField(db_index=True)

    type = models.ForeignKey(
        OrganizationType,
        on_delete=models.PROTECT,
        default=1)
    name = models.CharField(max_length=250, db_index=True)

    internal_notes = models.TextField(
        max_length=2500,
        help_text="These notes can contain information on WHY this organization was added. Can be handy if it's not "
                  "straightforward. This helps with answering questions why the organization was added lateron. "
                  "These notes will not be published, but are also not secret.",
        blank=True,
        null=True,
    )

    twitter_handle = models.CharField(
        max_length=150,
        help_text="Include the @ symbol. Used in the top lists to let visitors tweet to the"
                  "organization to wake them up.",
        null=True,
        blank=True,
        validators=[validate_twitter]
    )

    # stacking is_dead pattern
    # postpone migration on production.
    created_on = models.DateTimeField(
        blank=True,
        null=True,
        default=datetime(year=2016, month=1, day=1, hour=0, minute=0, second=0, microsecond=0, tzinfo=pytz.utc),
        db_index=True
    )

    is_dead_since = models.DateTimeField(
        blank=True,
        null=True,
        db_index=True
    )

    is_dead = models.BooleanField(
        default=False,
        help_text="A dead organization is not shown on the map, depending on the dead_date."
    )

    is_dead_reason = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )

    wikidata = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="Reference to the wikidata project. Example:Q9928"
    )

    wikipedia = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="Reference to the wikipedia article, including the correct wiki. "
                  "Example: nl:Heemstede (Noord-Holland)"
    )

    class Meta:
        managed = True
        db_table = 'organization'
        verbose_name = _('organization')
        verbose_name_plural = _('organizations')

    # todo: find a smarter way to get the organization type name, instead of a related query... cached enums?
    # this list resets per restart. So if you do complex changes in these layers / types...
    organization_name_cache = {}

    def __str__(self):

        if self.type_id not in self.organization_name_cache:
            # log.debug("caching...")
            self.organization_name_cache[self.type_id] = self.type.name

        type_label = self.organization_name_cache[self.type_id]

        if self.is_dead:
            return "✝ %s, %s/%s (%s)" % (self.name, self.country, type_label, self.created_on.strftime("%b %Y"))
        else:
            return "%s, %s/%s (%s)" % (self.name, self.country, type_label, self.created_on.strftime("%b %Y"))


GEOJSON_TYPES = (
    ('MultiPolygon', 'MultiPolygon'),
    ('MultiLineString', 'MultiLineString'),
    ('MultiPoint', 'MultiPoint'),
    ('Polygon', 'Polygon'),
    ('LineString', 'LineString'),
    ('Point', 'Point'),
)


class Coordinate(models.Model):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE)
    geojsontype = models.CharField(
        db_column='geoJsonType',
        max_length=20,
        blank=True,
        null=True,
        choices=GEOJSON_TYPES)

    area = JSONField(
        max_length=10000,
        blank=True,
        help_text="GeoJson using the WGS84 (EPSG 4326) projection. Use simplified geometries to "
                  "reduce the amount of data to transfer. Editing both this and the edit_area, this will take "
                  "preference."
    )

    edit_area = GeoJSONField(
        max_length=10000,
        null=True,
        blank=True,
        help_text="The results of this field are saved in the area and geojsontype. It's possible to edit the area"
                  " field directly, which overwrites this field. Changing both the manual option takes preference."
    )

    # stacking pattern for coordinates.
    created_on = models.DateTimeField(
        blank=True,
        null=True,
        db_index=True,
        default=datetime(year=2016, month=1, day=1, hour=0, minute=0, second=0, microsecond=0, tzinfo=pytz.utc)
    )
    creation_metadata = models.CharField(
        max_length=255,
        blank=True,
        null=True)
    is_dead = models.BooleanField(
        default=False,
        help_text="Dead url's will not be rendered on the map. Scanners can set this check "
                  "automatically (which might change in the future)")
    is_dead_since = models.DateTimeField(
        blank=True,
        null=True,
        db_index=True
    )
    is_dead_reason = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )

    class Meta:
        managed = True
        db_table = 'coordinate'
        verbose_name = _('coordinate')
        verbose_name_plural = _('coordinates')


class Url(models.Model):
    organization_old = models.ForeignKey(
        Organization,
        null=True,
        on_delete=models.PROTECT
    )

    organization = models.ManyToManyField(
        Organization,
        related_name="u_many_o_upgrade"
    )

    url = models.CharField(
        max_length=255,
        help_text="Lowercase url name. For example: mydomain.tld or subdomain.domain.tld"
    )

    internal_notes = models.TextField(
        max_length=500,
        help_text="These notes can contain information on WHY this URL was added. Can be handy if it's not "
                  "straightforward. This helps with answering questions why the URL was added lateron. For example: "
                  "some urls are owned via a 100% shareholder construction by a state company / municipality "
                  "while the company itself is private. These notes will not be published, but are also not secret.",
        blank=True,
        null=True,
    )

    created_on = models.DateTimeField(
        auto_now_add=True,
        blank=True,
        null=True
    )

    not_resolvable = models.BooleanField(
        default=False,
        help_text="Url is not resolvable (anymore) and will not be picked up by scanners anymore."
                  "When the url is not resolvable, ratings from the past will still be shown(?)#")

    not_resolvable_since = models.DateTimeField(
        blank=True,
        null=True
    )

    not_resolvable_reason = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="A scanner might find this not resolvable, "
                  "some details about that are placed here."
    )

    is_dead = models.BooleanField(
        default=False,
        help_text="Dead url's will not be rendered on the map. Scanners can set this check "
                  "automatically (which might change in the future)"
    )

    is_dead_since = models.DateTimeField(
        blank=True, null=True
    )

    is_dead_reason = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )

    uses_dns_wildcard = models.BooleanField(
        default=False,
        help_text="When true, this domain uses a DNS wildcard and any subdomain will resolve to "
                  "something on this host.")

    dns_supports_mx = models.BooleanField(
        default=False,
        help_text="If there is at least one MX record available, so we can perform mail generic mail scans. (for these"
                  "scans we don't need to know what mail-ports and protocols/endpoints are available).")

    onboarding_stage = models.CharField(
        max_length=150,
        blank=True,
        null=True,
        help_text="Because of complexity of onboarding, not working with Celery properly, onboarding is done in "
                  "multiple steps. The last completed step is saved in this value. Empty: nothing. endpoints: endpoints"
                  " have been found. completed: onboarding is done, also onboarded flag is set."
    )

    computed_subdomain = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="Automatically computed by tldextract on save. Data entered manually will be overwritten.",
        db_index=True
    )

    computed_domain = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="Automatically computed by tldextract on save. Data entered manually will be overwritten."
    )

    computed_suffix = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="Automatically computed by tldextract on save. Data entered manually will be overwritten."
    )

    onboarding_stage_set_on = models.DateTimeField(
        blank=True,
        null=True,
        help_text="When the onboarding stage was hit. Helps with time-outs."
    )

    onboarded = models.BooleanField(
        default=False,
        help_text="After adding a url, there is an onboarding process that runs a set of tests."
                  "These tests are usually run very quickly to get a first glimpse of the url."
                  "This test is run once.")

    onboarded_on = models.DateTimeField(
        auto_now_add=True,
        blank=True,
        null=True,
        help_text="The moment the onboard process finished."
    )

    class Meta:
        managed = True
        db_table = 'url'
        unique_together = (('organization_old', 'url'),)

    def __str__(self):
        if self.is_dead:
            return "✝ %s" % self.url
        else:
            return self.url

    def make_unresolvable(self, message, date):
        self.not_resolvable = True
        self.not_resolvable_reason = message
        self.not_resolvable_since = date
        self.save()

    def clean(self):

        if self.is_dead and (not self.is_dead_since or not self.is_dead_reason):
            raise ValidationError(_('When telling this is dead, also enter the date and reason for it.'))

        if Url.objects.all().filter(url=self.url, is_dead=False, not_resolvable=False).exclude(pk=self.pk).exists():
            raise ValidationError(_('Url already exists, existing url is alive and resolvable.'))

        # urls must be lowercase
        self.url = self.url.lower()

        # !!!! below validation was placed in the admin interface.
        # We're adding the URL before we know it's allowed. This due to the missing docs on how to clean
        # many to many relationships. The URL needs to have an ID when querying a many to many for it, otherwise
        # you'll get an exception.
        # If it already exists, the url will be deleted still.
        # https://code.djangoproject.com/ticket/12938 - NOPE, not going to happen...
        # so we use plain old SQL and then it works fine :)
        # And that also won't work because organization is empty. Which is a total bummer. You'd expect
        # this field to be here somehow, but it isn't.
        # a warning might be possible after the insert, but then you've got two urls already.
        # this is really a shortcoming of Django.

    def save(self, *args, **kwarg):

        # handle computed values

        result = tldextract.extract(self.url)
        self.computed_subdomain = result.subdomain
        self.computed_domain = result.domain
        self.computed_suffix = result.suffix

        super(Url, self).save(*args, **kwarg)

    def is_top_level(self):
        # count the number of dots. Should be one.
        # allows your own extension on a lan. there are thousands of extensions today.
        # so do the stupid thing: trust user input :)
        if self.url.count(".") == 1:
            return True
        return False

    def add_subdomain(self, subdomain):
        # import here to prevent circular/cyclic imports, this module imports Url.
        from failmap.scanners.scanner.http import resolves

        new_url = (subdomain + "." + self.url).lower()

        if Url.objects.all().filter(url=new_url, organization__in=self.organization.all()).exists():
            log.debug("Subdomain already in the database: %s" % new_url)
            return

        if not resolves(new_url):
            log.debug("New subdomain did not resolve on either ipv4 and ipv6: %s" % new_url)
            return

        u = Url()
        # A Url needs to have a value for field "id" before a many-to-many relationship can be used.
        u.url = new_url
        u.save()
        for organization in self.organization.all():
            u.organization.add(organization)
            u.save()
            log.info("Added url: %s to organization: %s" % (new_url, organization))

        # run standard checks, so you know the
        # discover_wildcards([u])

        return u

# are open ports based on IP adresses.
# adresses might change (and thus an endpoint changes).
# for the list of endpoints, you want to know what endpoints don't exist
# so they are not used anymore.
# class Port(models.Model):
#    url = models.ForeignKey(Url, on_delete=models.PROTECT)


def seven_days_in_the_future():
    return datetime.now(pytz.utc) + timedelta(days=7)


def today():
    return datetime.now(pytz.utc).today()


class Promise(models.Model):
    """Allow recording of organisation promises for improvement."""

    organization = models.ForeignKey(Organization, on_delete=models.PROTECT)

    notes = models.TextField(
        blank=True,
        null=True,
        help_text="Context information about the promise (eg: ticket reference).")

    # https://stackoverflow.com/questions/29549611/fixed-default-value-provided-after-upgrading-to-django-1-8#29549675
    created_on = models.DateTimeField(
        default=today, blank=True, null=True)

    expires_on = models.DateTimeField(
        default=seven_days_in_the_future,
        blank=True,
        null=True,
        help_text="When in the future this promise is expected to be fulfilled.")

    def __str__(self):
        return '%s - %s' % (self.organization.name, self.created_on)

    class Meta:
        verbose_name = _('promise')
        verbose_name_plural = _('promises')


class Dataset(models.Model):
    """
    Allows you to define URL datasources to download and import into the system. This acts as a memory of what you
    have imported. You can even re-import the things listed here. It will use the generic/excel importer.
    """
    source = models.URLField()
    is_imported = models.BooleanField(default=False,)
    imported_on = models.DateTimeField(blank=True, null=True)
    type = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="To determine what importer is needed: xls, xlsx, json, dutch_government."
    )
    kwargs = models.TextField(
        max_length=5000,
        blank=True,
        null=True,
        help_text="A JSON / dictionary with extra options for the parser to handle the dataset. "
                  "This is different per parser. This field is highly coupled with the code of the parser.",
        default='{}'
    )
