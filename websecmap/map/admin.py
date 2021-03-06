import logging
from copy import deepcopy
from datetime import datetime
from typing import Dict, Any

import pytz
from adminsortable2.admin import SortableAdminMixin
from celery import group
from django.contrib import admin
from django.db import transaction
from django.urls import reverse
from django.utils.html import format_html
from import_export.admin import ImportExportModelAdmin

from websecmap.app.models import Job
from websecmap.celery import PRIO_HIGH, app
from websecmap.map import models
from websecmap.map.logic.openstreetmap import import_from_scratch, update_coordinates
from websecmap.map.models import HighLevelStatistic, MapDataCache, VulnerabilityStatistic
from websecmap.map.report import compose_task

log = logging.getLogger(__package__)


@admin.register(models.AdministrativeRegion)
class AdministrativeRegionAdmin(ImportExportModelAdmin, admin.ModelAdmin):

    list_display = (
        "country",
        "organization_type",
        "admin_level",
        "import_start_date",
        "imported",
        "import_message",
        "resampling_resolution",
    )
    search_fields = ["country", "organization_type__name", "admin_level"]
    list_filter = ["country", "organization_type", "admin_level", "imported"][::-1]
    fields = (
        "country",
        "organization_type",
        "admin_level",
        "import_start_date",
        "imported",
        "import_message",
        "resampling_resolution",
    )

    readonly_fields = ["import_start_date", "imported", "import_message"]

    actions = []

    def import_region(self, request, queryset):
        tasks = []

        for region in queryset:
            organization_filter = {"country": region.country, "type": region.organization_type.pk}

            # you can't add tasks for reporting, as the data is not in the database to create the tasks yet.
            tasks.append(
                start_import.si(region.pk)
                | import_from_scratch.si([str(region.country)], [region.organization_type.name])
                | add_configuration.si(str(region.country), region.organization_type.pk)
                | set_imported.si(region.pk)
                | report_country.si(organization_filter)
                | prepare_map.si(str(region.country), region.organization_type.pk)
            )

        task_name = "%s (%s) " % ("Import region", ",".join(map(str, list(queryset))))
        task = group(tasks)

        job = Job.create(task, task_name, request, priority=PRIO_HIGH)
        link = reverse("admin:app_job_change", args=(job.id,))
        self.message_user(request, 'Job created, <a href="%s">%s</a>' % (link, task_name))

    import_region.short_description = "🛃  Import region"
    actions.append(import_region)

    # ah, hmm... abstractions...
    # something something abstractions
    def update_coordinates(self, request, queryset):
        tasks = []

        for region in queryset:
            organization_filter = {"country": region.country, "type": region.organization_type.pk}
            tasks.append(
                start_import.si(region.pk)
                | update_coordinates.si([str(region.country)], [region.organization_type.name])
                | set_imported.si(region.pk)
                | report_country.si(organization_filter)
                | prepare_map.si(str(region.country), region.organization_type.pk)
            )

        task_name = "%s (%s) " % ("Update region", ",".join(map(str, list(queryset))))
        task = group(tasks)

        job = Job.create(task, task_name, request, priority=PRIO_HIGH)
        link = reverse("admin:app_job_change", args=(job.id,))
        self.message_user(request, 'Job created, <a href="%s">%s</a>' % (link, task_name))

    update_coordinates.short_description = "🛂  Update region"
    actions.append(update_coordinates)


@app.task(queue="storage")
def start_import(region_id: int):
    region = models.AdministrativeRegion.objects.all().filter(pk=region_id).first()
    if not region:
        return

    region.import_start_date = datetime.now(pytz.utc)
    region.save(update_fields=["import_start_date"])


@app.task(queue="storage")
def set_imported(region_id: int):
    region = models.AdministrativeRegion.objects.all().filter(pk=region_id).first()
    if not region:
        return
    region.imported = True
    region.save(update_fields=["imported"])


@app.task(queue="storage")
def prepare_map(country: str, organization_type: int):
    # when the reports are created, we still probably have some map cache, as the admin probably looked
    # at that page before...
    MapDataCache.objects.all().filter(organization_type__name=organization_type, country=country).delete()


@app.task(queue="storage")
def report_country(organization_filter: Dict[str, Any]):
    tasks = compose_task(organizations_filter=organization_filter)
    tasks.apply_async()


@app.task(queue="storage")
def add_configuration(country: str, organization_type: int):

    if models.Configuration.objects.all().filter(country=country, organization_type=organization_type).exists():
        log.debug("This configuration already exists, skipping.")
        return

    # has earlier configuration of this country? Then add it after that country.
    tmp = models.Configuration.objects.all().filter(country=country).order_by("-display_order").first()
    if tmp:
        new_number = tmp.display_order + 1

        moveup = models.Configuration.objects.all().filter(display_order__gte=new_number).order_by("-display_order")
        for config in moveup:
            config.display_order += 1
            config.save()
    else:
        # otherwise add it to the end of the list.
        tmp = models.Configuration.objects.all().order_by("-display_order").first()

        if tmp:
            new_number = tmp.display_order + 1
        else:
            new_number = 1

    a = models.Configuration(
        country=country,
        organization_type=organization_type,
        is_the_default_option=False,
        is_displayed=False,
        is_scanned=False,
        is_reported=True,
        display_order=new_number,
    )
    a.save()


@admin.register(models.Configuration)
# ImportExportModelAdmin and SortableAdminMixin don't work together.
# as sortableadmin contains a bug causing double ID's, we're prefering importexportmodeladmin. Makes ordering
# awful to handle. But we can manage by changing that to buttons that sort of work.
class ConfigurationAdmin(
    ImportExportModelAdmin,
    admin.ModelAdmin,
    SortableAdminMixin,
):

    list_display = (
        "display_order",
        "country",
        "organization_type",
        "is_displayed",
        "is_the_default_option",
        "is_scanned",
        "is_reported",
    )
    search_fields = [
        "country",
        "organization_type",
    ]
    list_filter = [
        "country",
        "organization_type",
        "is_displayed",
        "is_the_default_option",
        "is_scanned",
        "is_reported",
    ][::-1]
    fields = (
        "display_order",
        "country",
        "organization_type",
        "is_displayed",
        "is_the_default_option",
        "is_scanned",
        "is_reported",
    )

    def save_model(self, request, obj, form, change):
        # allows to place a new item at the right position, moving certain items up.
        # if the display_order is zero, autoplace the item.

        if obj.display_order:
            super().save_model(request, obj, form, change)

        else:
            country_exists = (
                models.Configuration.objects.all().filter(country=obj.country).order_by("-display_order").first()
            )

            if country_exists:
                # if there is something form this country, place it where it belongs and move the rest +=1
                new_number = country_exists.display_order + 1

                moveup = (
                    models.Configuration.objects.all().filter(display_order__gte=new_number).order_by("-display_order")
                )
                for config in moveup:
                    config.display_order += 1
                    config.save()

                obj.display_order = country_exists.display_order + 1
                super().save_model(request, obj, form, change)

            else:
                # if there is nothing from this country, then add it at the end.
                tmp = models.Configuration.objects.all().order_by("-display_order").first()

                if tmp:
                    obj.display_order = tmp.display_order + 1
                else:
                    obj.display_order = 1

                super().save_model(request, obj, form, change)

    actions = []

    def display(self, request, queryset):

        for configuration in queryset:
            configuration.is_displayed = True
            configuration.save()

    display.short_description = "☀️ Display"
    actions.append(display)

    def hide(self, request, queryset):

        for configuration in queryset:
            configuration.is_displayed = False
            configuration.save()

    hide.short_description = "🌑 Hide"
    actions.append(hide)

    def allow_scanning(self, request, queryset):

        for configuration in queryset:
            configuration.is_scanned = True
            configuration.save()

    allow_scanning.short_description = "❤️  Allow scanning"
    actions.append(allow_scanning)

    def stop_scanning(self, request, queryset):

        for configuration in queryset:
            configuration.is_scanned = False
            configuration.save()

    stop_scanning.short_description = "💔  Stop scanning"
    actions.append(stop_scanning)

    def allow_reporting(self, request, queryset):

        for configuration in queryset:
            configuration.is_reported = True
            configuration.save()

    allow_reporting.short_description = "📄️  Allow Reporting"
    actions.append(allow_reporting)

    def stop_reporting(self, request, queryset):

        for configuration in queryset:
            configuration.is_reported = False
            configuration.save()

    stop_reporting.short_description = "📄  Stop Reporting"
    actions.append(stop_reporting)

    def create_report(self, request, queryset):

        for configuration in queryset:

            organization_filter = {"country": configuration.country, "type": configuration.organization_type}

            log.debug(organization_filter)
            task = compose_task(organizations_filter=organization_filter)
            task.apply_async()

        self.message_user(request, "Reports are being generated in the background.")

    create_report.short_description = "📄  Report"
    actions.append(create_report)

    def set_default(self, request, queryset):

        for configuration in queryset:

            models.Configuration.objects.all().update(is_the_default_option=False)

            configuration.is_the_default_option = True
            configuration.save()

    set_default.short_description = "😀  Set default"
    actions.append(set_default)

    def remove_default(self, request, queryset):

        for configuration in queryset:
            configuration.is_the_default_option = False
            configuration.save()

    remove_default.short_description = "😭  Remove default"
    actions.append(remove_default)

    def reorder(self, request, queryset):

        first_order = None

        for configuration in queryset:

            # set the first order, and keep counting from that.
            if not first_order:
                if not int(configuration.display_order):
                    first_order = 0
                    configuration.display_order = 0
                else:
                    first_order = configuration.display_order
            else:
                # second and more
                first_order += 1
                configuration.display_order = first_order

            configuration.save()

    reorder.short_description = "Reorder"
    actions.append(reorder)

    @transaction.atomic
    def move_up(self, request, queryset):

        for configuration in queryset:
            next_config = (
                models.Configuration.objects.all()
                .order_by("-display_order")
                .filter(display_order__lt=configuration.display_order)
                .first()
            )
            if not next_config:
                log.debug("No next one")
                continue

            log.debug("Moving up: %s to %s" % (configuration.display_order, next_config.display_order))
            tmp = deepcopy(next_config.display_order)
            next_config.display_order = configuration.display_order
            configuration.display_order = tmp

            next_config.save(update_fields=["display_order"])
            configuration.save(update_fields=["display_order"])

    move_up.short_description = "Move Up"
    actions.append(move_up)

    @transaction.atomic
    def move_down(self, request, queryset):

        for configuration in reversed(queryset):
            previous_config = (
                models.Configuration.objects.all()
                .order_by("display_order")
                .filter(display_order__gt=configuration.display_order)
                .first()
            )
            if not previous_config:
                log.debug("No previous one")
                continue

            log.debug("Moving down: %s to %s" % (configuration.display_order, previous_config.display_order))
            tmp = deepcopy(previous_config.display_order)
            previous_config.display_order = configuration.display_order
            configuration.display_order = tmp

            previous_config.save(update_fields=["display_order"])
            configuration.save(update_fields=["display_order"])

    move_down.short_description = "Move Down"
    actions.append(move_down)


@admin.register(models.MapHealthReport)
class MapHealthReportAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    list_display = (
        "map_configuration",
        "at_when",
        "percentage_up_to_date",
        "percentage_out_of_date",
        "outdate_period_in_hours",
    )

    search_fields = [
        "map_configuration__country",
        "map_configuration__organization_type__name",
    ]

    list_filter = [
        "percentage_up_to_date",
        "percentage_out_of_date",
        "outdate_period_in_hours",
        "map_configuration__country",
        "map_configuration__organization_type__name",
        "at_when",
    ][::-1]
    fields = (
        "map_configuration",
        "at_when",
        "percentage_up_to_date",
        "percentage_out_of_date",
        "outdate_period_in_hours",
        "detailed_report",
    )


@admin.register(models.MapDataCache)
class MapDataCacheAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    def get_queryset(self, request):
        # textfields are extremely slow in mysql. Prevent the text field.
        qs = super(MapDataCacheAdmin, self).get_queryset(request)
        qs = qs.defer("dataset")
        return qs

    list_display = ("pk", "country", "organization_type", "filters", "at_when")
    list_filter = ["country", "organization_type", "filters", "at_when"][::-1]
    search_fields = ["country", "organization_type", "filters"]

    readonly_fields = ["cached_on"]

    actions = []

    def instant_cache_clear(self, request, queryset):
        MapDataCache.objects.all().delete()

    instant_cache_clear.short_description = "Clear all caches (select 1)"
    actions.append(instant_cache_clear)


@admin.register(models.VulnerabilityStatistic)
class VulnerabilityStatisticAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    list_display = (
        "country",
        "organization_type",
        "scan_type",
        "at_when",
        "high",
        "medium",
        "low",
        "urls",
        "ok_urls",
        "endpoints",
        "ok_endpoints",
        "ok",
    )
    list_filter = ["country", "organization_type", "scan_type", "at_when", "high", "medium", "low"][::-1]
    search_fields = ["country", "organization_type", "scan_type"]

    actions = []

    def instant_cache_clear(self, request, queryset):
        VulnerabilityStatistic.objects.all().delete()

    instant_cache_clear.short_description = "Clear all caches (select 1)"
    actions.append(instant_cache_clear)


@admin.register(models.HighLevelStatistic)
class HighLevelStatisticAdmin(ImportExportModelAdmin, admin.ModelAdmin):

    list_display = (
        "country",
        "organization_type",
        "at_when",
    )
    list_filter = ["country", "organization_type", "at_when"][::-1]
    search_fields = ["country", "organization_type"]

    actions = []

    def instant_cache_clear(self, request, queryset):
        HighLevelStatistic.objects.all().delete()

    instant_cache_clear.short_description = "Clear all caches (select 1)"
    actions.append(instant_cache_clear)


@admin.register(models.LandingPage)
class LandingPageAdmin(ImportExportModelAdmin, admin.ModelAdmin):

    list_display = ("map_configuration", "directory", "enabled")
    list_filter = ["map_configuration", "directory", "enabled"][::-1]
    search_fields = ["map_configuration", "directory", "enabled"]


@admin.register(models.OrganizationReport)
class OrganizationReportAdmin(ImportExportModelAdmin, admin.ModelAdmin):

    # do NOT load the calculation field, as that will be slow.
    # https://stackoverflow.com/questions/34774028/how-to-ignore-loading-huge-fields-in-django-admin-list-display
    def get_queryset(self, request):
        qs = super(OrganizationReportAdmin, self).get_queryset(request)

        # tell Django to not retrieve mpoly field from DB
        qs = qs.defer("calculation")
        return qs

    def inspect_organization(self, obj):
        return format_html(
            '<a href="../../organizations/organization/{id}/change">inspect organization</a>',
            id=format(obj.organization_id),
        )

    list_display = (
        "organization",
        "total_urls",
        "ok_urls",
        "total_endpoints",
        "ok_endpoints",
        "high",
        "medium",
        "low",
        "ok",
        "explained_high",
        "explained_medium",
        "explained_low",
        "at_when",
        "inspect_organization",
    )
    search_fields = ["organization__name", "at_when"]
    list_filter = ["organization", "organization__country", "organization__type__name", "at_when"][::-1]
    # fields = [field.name for field in OrganizationRating._meta.get_fields() if field.name != "id"][::-1]

    fields = (
        "organization",
        "total_urls",
        "total_endpoints",
        "high",
        "medium",
        "low",
        "ok",
        "high_urls",
        "medium_urls",
        "low_urls",
        "ok_urls",
        "high_endpoints",
        "medium_endpoints",
        "low_endpoints",
        "ok_endpoints",
        "total_url_issues",
        "url_issues_high",
        "url_issues_medium",
        "url_issues_low",
        "url_ok",
        "total_endpoint_issues",
        "endpoint_issues_high",
        "endpoint_issues_medium",
        "endpoint_issues_low",
        "endpoint_ok",
        "explained_high",
        "explained_medium",
        "explained_low",
        "explained_high_urls",
        "explained_medium_urls",
        "explained_low_urls",
        "explained_high_endpoints",
        "explained_medium_endpoints",
        "explained_low_endpoints",
        "explained_total_url_issues",
        "explained_url_issues_high",
        "explained_url_issues_medium",
        "explained_url_issues_low",
        "explained_total_endpoint_issues",
        "explained_endpoint_issues_high",
        "explained_endpoint_issues_medium",
        "explained_endpoint_issues_low",
        "at_when",
        "calculation",
    )

    ordering = ["-at_when"]

    save_as = True
