from django.shortcuts import render, redirect
from django.http import HttpResponse
from requests.auth import HTTPBasicAuth
import requests
from django.conf import settings
from django.db import transaction
import zoneinfo
from django.db.models import Sum


import json
from datetime import datetime, timedelta, date
from pytz import timezone
import os

from .models import ib_user

# Helper Methods
def get_redirect_uri():
    if os.environ.get("JS_DJANGO_ENV","") == "DEV":
        return "http://localhost:8000/idle_buster/auth"
    else:
        return "https://www.imjs.dev/idle_buster/auth"

def get_user(ext_id):
    return ib_user.objects.get(ext_id = ext_id)

def round_forward(dt, minutes,tzinfo):
    return dt + (datetime.min.replace(tzinfo=tzinfo) - dt) % timedelta(minutes = minutes)

def round_back(dt, minutes,tzinfo):
    return dt - (dt - datetime.min.replace(tzinfo=tzinfo)) % timedelta(minutes = minutes)


# View Methods
def main_view(request):
    return redirect(f"https://www.fitbit.com/oauth2/authorize?response_type=code&client_id={settings.IB_VARS['fb_client_id']}&redirect_uri={get_redirect_uri()}&scope=activity%20profile")

def get_multiplier(request, ext_id):
    obj = get_user(ext_id)

    dt_now = datetime.now(timezone('America/Boise')).date()    


    yesterday = dt_now - timedelta(days = 1)

    obj_yesterday = obj.yesterday
    if obj_yesterday == None:
        obj_yesterday = dt_now - timedelta(days = 99)

    if yesterday > obj_yesterday:
        yesterday_date = yesterday.strftime("%Y-%m-%d")

        url = "https://api.fitbit.com/1/user/{}/activities/date/{}.json".format(obj.fb_id, yesterday_date)
        headers = {}
        headers["authorization"] = "Bearer %s" % obj.access_token

        r = requests.get(url, headers=headers)
        if(r.status_code == 401):
            obj.get_refresh_token()
            headers = {}
            headers["authorization"] = "Bearer %s" % obj.access_token

            r = requests.get(url, headers=headers)

        activity_dict = json.loads(r.text)      
        actual_steps = activity_dict["summary"]["steps"]
        goal_steps = activity_dict["goals"]["steps"]
        multiplier = actual_steps/goal_steps

        obj.yesterday = yesterday
        obj.yesterday_mult = multiplier
        obj.save()
    else:
        multiplier = obj.yesterday_mult
    resp = HttpResponse(multiplier)
    resp['Access-Control-Allow-Origin'] = '*'
    return resp

def get_steps(request, ext_id):
    obj = get_user(ext_id)


    dt_now = datetime.now(timezone(obj.timezone))
    
    dt_delta = dt_now - obj.last_reading
    print(dt_delta.seconds)
    if dt_delta.seconds / 60.0 > 2.0:
        today_date = dt_now.strftime("%Y-%m-%d")

        url = "https://api.fitbit.com/1/user/{}/activities/date/{}.json".format(obj.fb_id, today_date)
        print(url)

        headers = {}
        headers["authorization"] = "Bearer %s" % obj.access_token

        r = requests.get(url, headers=headers)
        if(r.status_code == 401):
            obj.get_refresh_token()
            headers = {}
            headers["authorization"] = "Bearer %s" % obj.access_token

            r = requests.get(url, headers=headers)

        activity_dict = json.loads(r.text)
        

        steps = activity_dict["summary"]["steps"]
        obj.steps = steps
        obj.last_reading = dt_now
        obj.save()
    else:
        steps = obj.steps
    resp = HttpResponse(steps)
    resp['Access-Control-Allow-Origin'] = '*'
    return resp

def auth(request):
    client_id = settings.IB_VARS['fb_client_id']
    client_secret = settings.IB_VARS['fb_secret_key']

    auth_url = "https://www.fitbit.com/oauth2/authorize"
    redirect_uri = get_redirect_uri()
    refresh_url = "https://api.fitbit.com/oauth2/token"

    code = request.GET["code"]

    headers = {}
    headers["authorization"] = settings.IB_VARS['fb_basic']

    payload={}
    payload["code"] = code
    payload["grant_type"] = "authorization_code"
    payload["client_id"] = client_id
    payload["redirect_uri"] = redirect_uri

    r = requests.post("https://api.fitbit.com/oauth2/token", data = payload, auth= HTTPBasicAuth(client_id, client_secret), headers = headers)
    if r.status_code == 200:
        resp_dict = json.loads(r.text)
        print(resp_dict)

        access_token = resp_dict["access_token"]
        refresh_token = resp_dict["refresh_token"]
        user_id = resp_dict["user_id"]

        obj, created = ib_user.objects.get_or_create(fb_id=user_id)

        obj.access_token = access_token
        obj.refresh_token = refresh_token
        obj.save()

    else:
        return HttpResponse("Error in authorization, please go to main page")

    headers = {}
    headers["authorization"] = f"Bearer {obj.access_token}"


    r = requests.get(f"https://api.fitbit.com/1/user/{obj.fb_id}/profile.json", headers = headers)
    if r.status_code == 200:
        resp_dict = json.loads(r.text)
        obj.timezone = resp_dict["user"]["timezone"]
        obj.save()
    else:
        return HttpResponse("Error in authorization, please go to main page")

    return render(request, template_name = "post_auth.html", context = {"ib_user": obj})

@transaction.atomic
def get_steps_since(request, ext_id, date_since, time_since):
    from .models import step_cache
    obj = get_user(ext_id)

    tzinfo=zoneinfo.ZoneInfo(obj.timezone)

    year, month, day = date_since.split("-")
    hour, minute = time_since[0:2], time_since[2:]

    datetime_since = datetime(int(year), int(month), int(day), int(hour), int(minute))
    
    deletion_point = round_back(datetime.now(tzinfo),15, tzinfo) - timedelta(hours=72)

    step_cache.objects.filter(ibuser=obj).filter(timestamp__lte=deletion_point).delete()

    latest = step_cache.objects.filter(ibuser=obj).order_by('-timestamp').first()

    if latest == None:
        fill_since = round_back(datetime.now(tzinfo),15, tzinfo) - timedelta(hours=72) - timedelta(minutes=1)
    else:
        fill_since = latest.timestamp

    global_stop_point = round_back(datetime.now(tzinfo),15, tzinfo) - timedelta(minutes=1)
    skip_first = False

    resource = "steps"
    granularity = "15min"
    last_zero_ts = None
    while global_stop_point > fill_since:
        range_size = global_stop_point - fill_since
        
        if range_size.total_seconds() // 60 >= 24*60:
            stop_point = fill_since + timedelta(minutes=(24*60-15))
        else:
            stop_point = global_stop_point
        
        if skip_first:
            fill_since = fill_since+timedelta(minutes=15)
        else:
            skip_first = True

        print(f"Fill Since: {fill_since:%Y-%m-%d}")
        print(f"Fill Since: {fill_since:%H:%M}")
        
        print(f"Stop Point: {stop_point}")

        url = f"https://api.fitbit.com/1/user/{obj.fb_id}/activities/{resource}/date/{fill_since:%Y-%m-%d}/{stop_point:%Y-%m-%d}/{granularity}/time/{fill_since:%H:%M}/{stop_point:%H:%M}.json"
        print(url)
        fill_since = stop_point 
        headers = {}
        headers["authorization"] = "Bearer %s" % obj.access_token

        r = requests.get(url, headers=headers)
        if(r.status_code == 401):
            obj.get_refresh_token()
            headers = {}
            headers["authorization"] = "Bearer %s" % obj.access_token

            r = requests.get(url, headers=headers)
            obj.save()

        step_log = json.loads(r.text)
        year, month, day = fill_since.year, fill_since.month, fill_since.day
        start_date = date(year = year, month = month, day = day)
        date_border = False
        for ii in step_log["activities-steps-intraday"]["dataset"]:
            hour, minute, second = list(map(int, ii["time"].split(":")))
            record_time = time(hour = int(hour), minute = int(minute))
            print(record_time)
            if date_border == False and record_time < start_time:
                start_date = start_date + timedelta(days=1)
                date_border = True
            
            ts = datetime(year = year, month = month, day = day, hour = hour, minute = minute, second = second, tzinfo = tzinfo)
            if ii["value"] == 0:
                last_zero_ts = ts
            else:
                sl_obj = step_cache()
                sl_obj.steps = ii["value"]
                sl_obj.timestamp = datetime(year = year, month = month, day = day, hour = hour, minute = minute, second = second, tzinfo = tzinfo)
                sl_obj.ibuser = obj
                sl_obj.save()
    if last_zero_ts is not None:
        sl_obj = step_cache()
        sl_obj.steps = 0
        sl_obj.timestamp = datetime(year = year, month = month, day = day, hour = hour, minute = minute, second = second, tzinfo = tzinfo)
        sl_obj.ibuser = obj
        sl_obj.save()
    
    total = step_cache.objects.filter(ibuser=obj).filter(timestamp__gte=datetime_since).aggregate(Sum('steps'))

    resp = HttpResponse(total['steps__sum'])
    resp['Access-Control-Allow-Origin'] = '*'
    return resp