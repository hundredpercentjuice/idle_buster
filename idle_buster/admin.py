from django.contrib import admin
from django import forms

from . import models


class ib_userAdminForm(forms.ModelForm):

    class Meta:
        model = models.ib_user
        fields = "__all__"


class ib_userAdmin(admin.ModelAdmin):
    form = ib_userAdminForm
    list_display = [
        "fb_id",
        "yesterday",
        "ext_id",
        "created",
        "timezone",
        "yesterday_mult",
        "last_updated",
    ]
    readonly_fields = [
        "fb_id",
        "yesterday",
        "ext_id",
        "created",
        "timezone",
        "yesterday_mult",
        "last_updated",
    ]


class step_cacheAdminForm(forms.ModelForm):

    class Meta:
        model = models.step_cache
        fields = "__all__"


class step_cacheAdmin(admin.ModelAdmin):
    form = step_cacheAdminForm
    list_display = [
        "timestamp",
        "steps",
    ]
    readonly_fields = [
        "timestamp",
        "steps",
    ]


admin.site.register(models.ib_user, ib_userAdmin)
admin.site.register(models.step_cache, step_cacheAdmin)