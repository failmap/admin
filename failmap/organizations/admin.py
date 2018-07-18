import logging
from datetime import datetime

import nested_admin
import pytz
import tldextract
from django import forms
from django.contrib import admin
from django.contrib.humanize.templatetags.humanize import naturaltime
from django.core.exceptions import ValidationError
from django.urls import reverse
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from import_export.admin import ImportExportModelAdmin
from jet.admin import CompactInline
from leaflet.admin import LeafletGeoAdminMixin

import failmap.scanners.scanner_http as scanner_http
from failmap import types
from failmap.map.rating import OrganizationRating, UrlRating
from failmap.scanners import (onboard, scanner_dns, scanner_dnssec, scanner_plain_http,
                              scanner_security_headers, scanner_tls_qualys)
from failmap.scanners.admin import UrlIp
from failmap.scanners.models import Endpoint, EndpointGenericScan, TlsQualysScan, UrlGenericScan

from ..app.models import Job
from ..celery import PRIO_HIGH
from .models import Coordinate, Organization, OrganizationType, Promise, Url

logger = logging.getLogger(__name__)


PROMISE_DESCRIPTION = """
<p>A 'promise' is an indication by an organisation representitive that an improvement
has been made which will alter the organizations score. A generic message will be
displayed on the organization report with the creation and expiry date of the promise
until it expires.</p>
<p>This indication is to overcome the problem of a negative score even though improvement
are made, but the score cannot reflect them yet due to technical or bureaucratic reasons.</p>
<p>It is not intended for long term promises of improvement that have not been applied or
put in to progress. The promised improvement must be verifiable by Faalkaart within a
handfull of days.</p>
"""


# todo: the through solution has two challenges:
# 1: the name of the objects listed
# 2: cannot auto-complete these with django-jet it seems, so an enormous amount of data
# it might be solved using an explicit relation?
# perhaps ask the django jet forum
class UrlAdminInline(CompactInline):
    model = Url.organization.through
    extra = 0
    show_change_link = True


# A highly limiting feature of the django admin interface is that inlines only
# go one level deep. Instead of N levels, and that nested inlines are not supported
# by default and all other support is experimental (or provides a severely reduced interface.
# https://github.com/theatlantic/django-nested-admin/ solves this, but misses support for the awesome compactinline
# a bug is that three empty values are added in the list below.
# perhaps the inline is fixable with some days of engineering, and might be worth while, but for now...
# and for some reason that
class EndpointGenericScanInline(nested_admin.NestedTabularInline):
    model = EndpointGenericScan

    can_delete = False

    exclude = ['domain', 'evidence']

    # this is purely informational, to save clicks when debugging.
    readonly_fields = ('endpoint', 'type', 'rating', 'explanation', 'rating_determined_on', 'last_scan_moment')

    ordering = ['-rating_determined_on']

    verbose_name = "Generic scan"
    verbose_name_plural = "Generic scans"

    # @staticmethod
    # def rating_determined_on_date(obj):
    #     # todo: should be formatted in humanized form.
    #     return obj.rating_determined_on

    # @staticmethod
    # def last_scan_moment_date(obj):
    #     return obj.last_scan_moment

    def has_add_permission(self, request):
        return False


class TlsQualysScanInline(nested_admin.NestedTabularInline):
    model = TlsQualysScan

    can_delete = False

    exclude = ['scan_date', 'scan_time']

    # this is purely informational, to save clicks when debugging.
    readonly_fields = ('qualys_rating', 'qualys_rating_no_trust', 'qualys_message', 'rating_determined_on',
                       'last_scan_moment')

    ordering = ['-rating_determined_on']

    verbose_name = "Qualys TLS scan"
    verbose_name_plural = "Qualys TLS scans"

    def has_add_permission(self, request):
        return False


class EndpointAdminInline(nested_admin.NestedStackedInline):
    model = Endpoint
    extra = 0
    show_change_link = True
    ordering = ["is_dead"]
    inlines = [EndpointGenericScanInline, TlsQualysScanInline]


class UrlGenericScanAdminInline(CompactInline):
    model = UrlGenericScan
    extra = 0
    show_change_link = True
    ordering = ["-rating_determined_on"]


class CoordinateAdminInline(CompactInline):
    model = Coordinate
    extra = 0


class OrganizationRatingAdminInline(CompactInline):
    model = OrganizationRating
    extra = 0
    readonly_fields = ('organization', 'rating', 'high', 'medium', 'low', 'when', 'calculation')
    can_delete = False
    ordering = ["-when"]


class UrlRatingAdminInline(CompactInline):
    model = UrlRating
    extra = 0
    readonly_fields = ('url', 'rating', 'high', 'medium', 'low', 'when', 'calculation')
    can_delete = False
    ordering = ["-when"]


class UrlIpInline(CompactInline):
    model = UrlIp
    extra = 0
    readonly_fields = ('url', 'ip', 'rdns_name', 'discovered_on', 'is_unused', 'is_unused_since', 'is_unused_reason')
    show_change_link = True
    ordering = ["-discovered_on"]


class PromiseAdminInline(CompactInline):
    model = Promise
    extra = 0
    ordering = ["-created_on"]

    fieldsets = (
        (None, {
            'fields': ('organization', 'created_on', 'expires_on', 'notes'),
            'description': PROMISE_DESCRIPTION,
        }),
    )


class ActionMixin:
    """Generic Mixin to add Admin Button for Organization/Url/Endpoint Actions.

    This class is intended to be added to ModelAdmin classes so all Actions are available without duplicating code.

    Action methods as described in:
      https://docs.djangoproject.com/en/2.0/ref/contrib/admin/actions/#actions-as-modeladmin-methods

    Most actions work on the same primary models (organization,url,endpoint). The Actions don't do any actual work but
    rather compose a task with the provided Queryset. After which this task is scheduled using a Job. This generic
    principle has been implemented in `generic_action` and the specific action implementations (eg; `scan_plain_http`)
    just provide the correct metadata (name, icon) and task composer to call.

    """

    actions = []

    def scan_plain_http(self, *args, **kwargs):
        return self.generic_action(scanner_plain_http.compose_task, 'Scan Plain Http', *args, **kwargs)
    scan_plain_http.short_description = '🔬  Missing TLS'
    actions.append(scan_plain_http)

    def scan_security_headers(self, *args, **kwargs):
        return self.generic_action(scanner_security_headers.compose_task, 'Scan Security Headers', *args, **kwargs)
    scan_security_headers.short_description = '🔬  Security Headers'
    actions.append(scan_security_headers)

    def scan_tls_qualys(self, *args, **kwargs):
        return self.generic_action(scanner_tls_qualys.compose_task, 'Scan TLS Qualys', *args, **kwargs)
    scan_tls_qualys.short_description = '🔬  TLS (Qualys)'
    actions.append(scan_tls_qualys)

    def dnssec(self, *args, **kwargs):
        return self.generic_action(scanner_dnssec.compose_task, 'DNSSEC', *args, **kwargs)
    dnssec.short_description = "🔬 DNSSEC"
    actions.append(dnssec)

    def dns_certificate_transparency(self, *args, **kwargs):
        return self.generic_action(scanner_dns.certificate_transparency_compose_task,
                                   'DNS Certificate transparency', *args, **kwargs)
    dns_certificate_transparency.short_description = "🗺  DNS (certificate transparency)"
    actions.append(dns_certificate_transparency)

    def dns_nsec(self, *args, **kwargs):
        return self.generic_action(scanner_dns.nsec_compose_task, 'DNS nsec1', *args, **kwargs)
    dns_nsec.short_description = "🗺  DNS (nsec1)"
    actions.append(dns_nsec)

    def dns_known_subdomains(self, *args, **kwargs):
        return self.generic_action(scanner_dns.brute_known_subdomains_compose_task, 'DNS Nsec', *args, **kwargs)
    dns_known_subdomains.short_description = "🗺  + DNS (known subdomains)"
    actions.append(dns_known_subdomains)

    def disover_endpoints(self, *args, **kwargs):
        return self.generic_action(scanner_http.compose_task, 'Discover endpoints', *args, **kwargs)
    disover_endpoints.short_description = "🗺  Discover endpoints"
    actions.append(disover_endpoints)

    def onboard(self, *args, **kwargs):
        return self.generic_action(onboard.compose_task, 'Onboard', *args, **kwargs)
    onboard.short_description = '🔮  Onboard'
    actions.append(onboard)

    def generic_action(self, task_composer: types.compose_task, name: str, request, queryset):
        """Admin action that will create a Job of tasks."""

        filters = {'x_filter': {'id__in': queryset.values_list('id')}}
        if queryset.model == Organization:
            filters['organizations_filter'] = filters.pop('x_filter')
        elif queryset.model == Url:
            filters['urls_filter'] = filters.pop('x_filter')
        elif queryset.model == Endpoint:
            filters['endpoints_filter'] = filters.pop('x_filter')

        task = task_composer(**filters)
        task_name = "%s (%s) " % (name, ','.join(map(str, list(queryset))))
        job = Job.create(task, task_name, request, priority=PRIO_HIGH)
        link = reverse('admin:app_job_change', args=(job.id,))
        self.message_user(request, 'Job created, <a href="%s">%s</a>' % (link, task_name))


# http://jet.readthedocs.io/en/latest/autocomplete.html?highlight=many
# for many values in the admin interface... for example endpoints.
class OrganizationAdmin(ActionMixin, ImportExportModelAdmin, admin.ModelAdmin):
    list_display = ('name_details', 'type', 'country', 'wikidata_', 'wikipedia_', 'created_on', 'is_dead')
    search_fields = (['name', 'country', 'type__name'])
    list_filter = ('type__name', 'country', 'created_on', 'is_dead', 'is_dead_since')

    fields = ('name', 'type', 'country', 'twitter_handle', 'created_on', 'wikidata', 'wikipedia',
              'is_dead', 'is_dead_since', 'is_dead_reason')

    inlines = [CoordinateAdminInline, OrganizationRatingAdminInline, PromiseAdminInline]  #

    @staticmethod
    def name_details(self):
        if self.is_dead:
            return "✝ %s, %s (%s - %s)" % (self.name, self.country,
                                           self.created_on.strftime("%b %Y") if self.created_on else "",
                                           self.is_dead_since.strftime("%b %Y") if self.is_dead_since else "")
        else:
            return "%s, %s (%s)" % (self.name, self.country, self.created_on.strftime("%b %Y"))

    @staticmethod
    def wikidata_(self):
        return format_html("<a href='https://www.wikidata.org/wiki/%s' target='_blank'>🔍 %s</a>" %
                           (self.wikidata, self.wikidata))

    @staticmethod
    def wikipedia_(self):
        return format_html("<a href='https://www.wikipedia.org/wiki/%s' target='_blank'>🔍 %s</a>" %
                           (self.wikipedia, self.wikipedia))


# https://docs.djangoproject.com/en/2.0/ref/forms/validation/
class MyUrlAdminForm(forms.ModelForm):

    def clean_url(self):

        url_string = self.data.get("url")

        # urls must be lowercase
        url_string = url_string.lower()

        # todo: remove invalid characters
        # Currently assume that there is some sense in adding this data.

        # see if the url is complete, and remove the http(s):// and paths parts:
        result = tldextract.extract(url_string)

        if result.subdomain:
            clean_url_string = "%s.%s.%s" % (result.subdomain, result.domain, result.suffix)
        else:
            clean_url_string = "%s.%s" % (result.domain, result.suffix)

        # also place the cleaned data back into the form, in case of errors.
        # this does not work this way it seems.
        # self.data.url = clean_url_string

        if not result.suffix:
            raise ValidationError("Url is missing suffix (.com, .net, ...)")

        return clean_url_string

    def clean(self):
        organizations = self.cleaned_data.get("organization")

        # mandatoryness error will already be triggered, don't interfere with that.
        if not organizations:
            return

        # make sure the URL is not added if it is already alive and matched to the selected organization.
        for organization in organizations:
            if Url.objects.all().filter(
                    url=self.cleaned_data.get("url"), is_dead=False, organization=organization).count():

                # format_html = XSS :)
                raise ValidationError(format_html(_(
                    'Url %s is already matched to "%s", and is alive. '
                    'Please add any remaining organizations to the existing version of this url. '
                    'Search for <a href="../?url=%s&is_dead=False">🔍 %s</a>.'
                    % (self.cleaned_data.get("url"), organization,
                       self.cleaned_data.get("url"), self.cleaned_data.get("url")))))

        # make sure the Url is not added if it is still alive: the existing url should be edited and the
        # organization should be added. (we might be able to do this automatically since we know the url is not
        # already matched to an organization) - In that case all other fields have to be ignored and
        # this form still closes succesfully.
        # This url already exists and the selected organization(s) have been added to it.

        if Url.objects.all().filter(
                url=self.data.get("url"), is_dead=False).count():

            # format_html = XSS :)
            raise ValidationError(format_html(_(
                'This url %s already exists and is alive. Please add the desired organizations to the existing url. '
                'This was not done automatically because it might be possible specific other data was entered in this '
                'form that cannot blindly be copied (as it might interfere with the existing url). '
                'Search for <a href="../?url=%s&is_dead=False">🔍 %s</a>.'
                % (self.data.get("url"), self.data.get("url"), self.data.get("url")))))


class HasEndpointScansListFilter(admin.SimpleListFilter):
    # Human-readable title which will be displayed in the
    # right admin sidebar just above the filter options.
    title = _('Has endpoint scans (todo)')

    # Parameter for the filter that will be used in the URL query.
    parameter_name = 'endpoint_scans'

    def lookups(self, request, model_admin):
        """
        Returns a list of tuples. The first element in each
        tuple is the coded value for the option that will
        appear in the URL query. The second element is the
        human-readable name for the option that will appear
        in the right sidebar.
        """
        return (
            ('yes', _('Yes')),
            ('no', _('No')),
        )

    def queryset(self, request, queryset):
        """
        Returns the filtered queryset based on the value
        provided in the query string and retrievable via
        `self.value()`.
        """
        # todo: make this filter work
        if self.value() == 'yes':
            return queryset
        if self.value() == 'no':
            return queryset


class UrlAdmin(ActionMixin, ImportExportModelAdmin, nested_admin.NestedModelAdmin):
    form = MyUrlAdminForm

    list_display = ('url', 'visit', 'current_rating', 'onboarded', 'onboarding_stage', 'uses_dns_wildcard',
                    'dead_for', 'unresolvable_for', 'created_on')

    search_fields = ('url', )
    list_filter = ('url', 'is_dead', 'is_dead_since', 'is_dead_reason',
                   'not_resolvable', 'not_resolvable_since', 'not_resolvable_reason',
                   'uses_dns_wildcard', 'organization', 'onboarded', 'organization__type__name',
                   'organization__country',
                   HasEndpointScansListFilter)

    fieldsets = (
        (None, {
            'fields': ('url', 'organization', 'created_on', 'onboarded')
        }),
        ('DNS', {
            'fields': ('uses_dns_wildcard', ),
        }),
        ('Resolvability', {
            'description': 'Non resolving urls cannot be reached anymore.',
            'fields': ('not_resolvable', 'not_resolvable_since', 'not_resolvable_reason'),
        }),
        ('dead URL management', {
            'description': "Dead urls are not show on the map. They can be dead on layer 8 (for example when a "
                           "wildcard DNS is used, but not a matching TLS certificate as wildcard certificates "
                           "are rarely used due to drawbacks).",
            'fields': ('is_dead', 'is_dead_since', 'is_dead_reason'),
        }),
    )
    readonly_fields = ['created_on', 'onboarded']

    def visit(self, obj: Url):
        if not obj.endpoint_set.count():
            return

        str = format_html("%s <a href='/admin/scanners/endpoint/?q=%s' target='_blank'>🔍</a>" %
                          (obj.endpoint_set.count(), obj.url))

        for endpoint in obj.endpoint_set.all():

            if endpoint.is_dead is False:
                str += " - <a href='%(protocol)s://%(url)s:%(port)s' target='_blank'>%(protocol)s/%(port)s</a>" % {
                    'url': obj.url,
                    'port': endpoint.port,
                    'protocol': endpoint.protocol
                }
        return format_html(str)

    @staticmethod
    def unresolvable_for(self):
        if self.not_resolvable and self.not_resolvable_since:
            return naturaltime(self.not_resolvable_since)
        else:
            return "-"

    # todo: further humanize this.
    @staticmethod
    def dead_for(self):
        if self.is_dead and self.is_dead_since:
            return naturaltime(self.is_dead_since)
        else:
            return "-"

    @staticmethod
    def current_rating(obj):
        x = UrlRating.objects.filter(url=obj).latest('when')

        if not any([x.high, x.medium, x.low]):
            return "✅ Perfect"

        label = "🔴" if x.high else "🔶" if x.medium else "🍋"

        return format_html("%s <span style='color: red'>%s</span> <span style='color: orange'>%s</span> "
                           "<span style='color: yellow'>%s</span>" % (label, x.high, x.medium, x.low))

    inlines = [UrlGenericScanAdminInline, EndpointAdminInline, UrlRatingAdminInline, UrlIpInline]

    actions = []

    # saved here in case we want to go back.
    # def onboard(self, request, queryset):
    #     onboard_urls(urls=list(queryset))
    #     self.message_user(request,
    #         "Onboarding task has been added. Onboarding can take a while depending on server load.")
    # actions.append('onboard')
    # onboard.short_description = "🔮  Onboard"

    def declare_dead(self, request, queryset):
        for url in queryset:
            url.is_dead = True
            url.is_dead_reason = "Killed via admin interface"
            url.is_dead_since = datetime.now(pytz.utc)
            url.save()
        self.message_user(request, "Declare dead: Done")
    declare_dead.short_description = "🔪  Declare dead"
    actions.append('declare_dead')

    def timeline_debug(self, request, queryset):
        from failmap.map.rating import create_timeline, show_timeline_console
        from django.http import HttpResponse

        content = "<pre>"
        for url in queryset:
            content += show_timeline_console(create_timeline(url), url)

        content += "</pre>"

        return HttpResponse(content)
    timeline_debug.short_description = "🐞  Timeline"
    actions.append('timeline_debug')


class OrganizationTypeAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    list_display = ('name', )
    search_fields = ('name', )
    list_filter = ('name', )
    fields = ('name', )


class CoordinateAdmin(LeafletGeoAdminMixin, ImportExportModelAdmin):

    # show Europe as default. Will probably change over time.
    # http://django-leaflet.readthedocs.io/en/latest/advanced.html
    # If you copy this setting from a point, be sure to switch x and y when pasting in default center.
    settings_overrides = {
        'DEFAULT_CENTER': (51.376378068613406, 13.223944902420046),
        'DEFAULT_ZOOM': 4
    }

    list_display = ('organization', 'geojsontype', 'created_on', 'is_dead', 'is_dead_since')
    search_fields = ('organization__name', 'geojsontype')
    list_filter = ('organization', 'geojsontype')

    # We wanted to place these on another tab, otherwise leaflet blocks mouse scrolling (which is annoying).
    # But then leaflet doesn't initialize properly, making the map unworkable. So they're on the first tab anyway.
    fieldsets = (
        (None, {
            'description': "The Edit area makes it easier to manipulate the Area and Geojsontype. Yet: when both are "
                           "changed, the Area/GeoJsontype takes precedence."
                           ""
                           "If you want to move the coordinate, preferably do so by creating a new one and setting the"
                           " current one as dead (+date etc). Then the map will show coordinates over time, which is "
                           "pretty neat.",
            'fields': ('organization', 'geojsontype', 'area', 'edit_area')
        }),

        ('Life cycle', {
            'fields': ('created_on', 'is_dead', 'is_dead_since', 'is_dead_reason'),
        }),
    )

    def save_model(self, request, obj, form, change):

        # log.info(form.changed_data)
        # grrr, both area and edit_area are ALWAYS changed... even if you didn't change the values in these
        # fields... this is obviously a bug or "optimization". We now have to resort to queries to figure out
        # if anything changed at all. Evil bugs.

        if obj.pk:
            # we're changing the object
            current = Coordinate.objects.get(pk=obj.pk)

            if current.area != obj.area or current.geojsontype != obj.geojsontype:
                # if 'area' in form.changed_data or 'geojsontype' in form.changed_data: doesn't work.
                logger.info("area changed")
                edit_area = {"type": form.cleaned_data['geojsontype'],
                             "coordinates": form.cleaned_data['area']}
                obj.edit_area = edit_area

            elif current.edit_area != obj.edit_area:
                logger.info("edit area changed")
                logger.info(form.cleaned_data["edit_area"])
                obj.geojsontype = form.cleaned_data["edit_area"]["type"]
                obj.area = form.cleaned_data["edit_area"]["coordinates"]
        else:
            # new object... see if there are empty fields we can ammend:
            if (not obj.area or not obj.geojsontype) and obj.edit_area:
                obj.geojsontype = form.cleaned_data["edit_area"]["type"]
                obj.area = form.cleaned_data["edit_area"]["coordinates"]
            elif not obj.edit_area:
                edit_area = {"type": form.cleaned_data['geojsontype'],
                             "coordinates": form.cleaned_data['area']}
                obj.edit_area = edit_area

        super().save_model(request, obj, form, change)


class PromiseAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    list_display = ('organization', 'created_on', 'expires_on')
    search_fields = ('organization',)
    list_filter = ('organization',)

    fieldsets = (
        (None, {
            'fields': ('organization', 'created_on', 'expires_on', 'notes'),
            'description': PROMISE_DESCRIPTION,
        }),
    )


admin.site.register(Organization, OrganizationAdmin)
admin.site.register(Url, UrlAdmin)
admin.site.register(Coordinate, CoordinateAdmin)
admin.site.register(OrganizationType, OrganizationTypeAdmin)
admin.site.register(Promise, PromiseAdmin)
