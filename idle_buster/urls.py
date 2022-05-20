from django.urls import path, re_path
from .views import auth, main_view, get_multiplier,get_steps,get_steps_since

urlpatterns = [
    re_path(r'auth', auth),
 	re_path(r'^$', main_view),
    path('<uuid:ext_id>/get_multiplier', get_multiplier, name = 'get_multiplier'),
    path('<uuid:ext_id>/get_steps', get_steps, name='get_steps'),
    path('<uuid:ext_id>/get_steps_since/<slug:date_since>/<slug:time_since>/', get_steps_since, name='get_steps_since'),
]