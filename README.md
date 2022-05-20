# idle_buster
Backend for using steps in idle games

## Quickstart

1. Add "idle_buster" to your INSTALLED_APPS setting like this::

    INSTALLED_APPS = [
        ...
        'idle_buster',
    ]

2. Add the following environment variables to your system
 -  ib_fb_client_id (Fitbit Client ID)
 -  ib_fb_secret_key (Fitbit Secret Key)

3. Update your settings.py file with the idle_buster settings::
```python
    IB_VARS = {
        'fb_client_id': os.environ.get('ib_fb_client_id', ""),
        'fb_secret_key': os.environ.get('ib_fb_secret_key', ""),    
    }

    from base64 import b64encode
    basic_key_auth = b64encode(f"{IB_VARS['fb_client_id']}:{IB_VARS['fb_secret_key']}".encode("ascii"))
    IB_VARS["fb_basic"] = f"Basic {basic_key_auth}"
```
4. Include the idle_buster URLconf in your project urls.py like this::

    path('idle_buster/', include('idle_buster.urls')),

5. Run ``python manage.py migrate`` to create the idle_buster models.

6. Visit http://127.0.0.1:8000/idle_buster/ to tie a user to fitbit
