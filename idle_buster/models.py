from django.db import models
from django.urls import reverse
import uuid
from django.conf import settings
from requests.auth import HTTPBasicAuth

class ib_user(models.Model):
    def get_refresh_token(self):
        import requests
        import json
        refresh_url = "https://api.fitbit.com/oauth2/token"
        refresh_body = {}
        refresh_body["grant_type"] = "refresh_token"
        refresh_body["refresh_token"] = self.refresh_token
        refresh_body["expires_in"] = 28800

        r = requests.post(refresh_url, data=refresh_body, auth = HTTPBasicAuth(settings.IB_VARS['fb_client_id'], settings.IB_VARS['fb_secret_key']) )
        resp_dict = json.loads(r.text)
        print(resp_dict)

        self.access_token = resp_dict["access_token"]
        self.refresh_token = resp_dict["refresh_token"]
        self.save()

    # Fields
    fb_id = models.CharField(max_length=12)
    yesterday = models.DateField(null=True)
    ext_id = models.UUIDField(default = uuid.uuid4)
    created = models.DateTimeField(auto_now_add=True, editable=False)
    timezone = models.CharField(max_length=30, null=True)
    yesterday_mult = models.FloatField(null=True)
    last_updated = models.DateTimeField(auto_now=True, editable=False)
    access_token = models.CharField(max_length=512, null=True)
    refresh_token = models.CharField(max_length=512, null=True)

    class Meta:
        pass

    def __str__(self):
        return str(self.pk)

    #def get_absolute_url(self):
    #    return reverse("idle_b_ib_user_detail", args=(self.pk,))

    #def get_update_url(self):
    #    return reverse("idle_b_ib_user_update", args=(self.pk,))



class step_cache(models.Model):

    # Relationships
    ibuser = models.ForeignKey("idle_buster.ib_user", on_delete=models.CASCADE)

    # Fields
    timestamp = models.DateTimeField(editable=False)
    steps = models.IntegerField()

    class Meta:
        pass

    def __str__(self):
        return str(self.pk)

    #def get_absolute_url(self):
    #    return reverse("idle_b_step_cache_detail", args=(self.pk,))

    #def get_update_url(self):
    #    return reverse("idle_b_step_cache_update", args=(self.pk,))
