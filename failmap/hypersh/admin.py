import logging

from django.contrib import admin
from django_fsm_log.admin import StateLogInline

from .models import ContainerConfiguration, ContainerGroup, Credential

log = logging.getLogger(__name__)


@admin.register(Credential)
class CredentialAdmin(admin.ModelAdmin):
    list_display = ('name', 'enabled', 'valid', 'last_validated', 'used_by')
    readonly_fields = ('valid',)

    actions = ('validate',)

    def used_by(self, obj):
        return "{0.__class__.__name__}({0.name})".format(obj.containergroup_set.get())

    def validate(modeladmin, request, queryset):
        """Run validate command on model."""
        for m in queryset:
            m.validate()
    validate.short_description = "Validate against Hyper.sh API."


@admin.register(ContainerGroup)
class ContainerGroupAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'credential',
        'configuration',
        'enabled',
        'minimum',
        'maximum',
        'desired',
        'current',
        'state',
        'last_update',
    )
    readonly_fields = ('current', 'last_update', 'state')
    actions = ('min1', 'plus1', 'maximum', 'minimum', 'update', 'scale', 'reset')

    inlines = [StateLogInline]

    def plus1(modeladmin, request, queryset):
        for m in queryset:
            m.desired += 1
            m.save(update_fields=['desired'])
    plus1.short_description = '+1'

    def maximum(modeladmin, request, queryset):
        for m in queryset:
            m.desired = m.maximum
            m.save(update_fields=['desired'])
    maximum.short_description = 'maximum'

    def min1(modeladmin, request, queryset):
        for m in queryset:
            m.desired -= 1
            m.save(update_fields=['desired'])
    min1.short_description = '-1'

    def minimum(modeladmin, request, queryset):
        for m in queryset:
            m.desired = m.minimum
            m.save(update_fields=['desired'])
    minimum.short_description = 'minimum'

    # these actions should not be required as the engine should take care of thi

    def scale(modeladmin, request, queryset):
        """Perform scale operation."""
        for m in queryset:
            # save implicitly triggers scale action
            m.save()
    scale.short_description = '(scale)'

    def update(modeladmin, request, queryset):
        """Perform update operation."""
        for m in queryset:
            m.update()
    update.short_description = '(update)'

    def reset(modeladmin, request, queryset):
        """Reset scaling state."""
        for m in queryset:
            m.reset_state()
    reset.short_description = '(reset)'


@admin.register(ContainerConfiguration)
class ContainerConfigurationAdmin(admin.ModelAdmin):
    list_display = ('name', 'image', 'command', 'used_by')

    def used_by(self, obj):
        return "{0.__class__.__name__}({0.name})".format(obj.containergroup_set.get())
