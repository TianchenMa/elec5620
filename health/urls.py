from django.conf.urls import url
from django.contrib.auth import views as auth_views
from .views import *

app_name = 'health'
urlpatterns = [
    url(r'^$', WelcomeView.as_view(), name='welcome'),

    url(r'^homepage/$', HomepageView.as_view(), name='homepage'),
    url(r'^homepage/(?P<slug>\w+)$', OperationView.as_view(), name='operations'),

    url(r'^healthdata/(?P<user_id>[0-9]+)/$', HealthDataView.as_view(), name='healthdata_page'),
    url(r'^healthdata/(?P<user_id>[0-9]+)/(?P<slug>\w+)/$', HealthDataOperationView.as_view(),
        name='healthdata_operations'),

    url(r'^task/(?P<user_id>[0-9]+)/$', TaskView.as_view(), name='task_page'),

    url(r'^calendar/(?P<user_id>[0-9]+)/$', CalendarView.as_view(), name='calendar_page'),
    url(r'^calendar/(?P<user_id>[0-9]+)/(?P<slug>\w+)/$', CalendarOperationView.as_view(), name='calendar_operations'),

    url(r'^user/(?P<slug>\w+)$', UserControlView.as_view(), name='user_control'),

    url(r'^(?P<user_id>[0-9]+)/$', PatientHomepageView.as_view(), name='patient_homepage'),
    url(r'^(?P<user_id>[0-9]+)/(?P<slug>\w+)$', DoctorOperationView.as_view(), name='doctor_operations')
]
