# urls for scanners, maybe in their own url files
from django.conf.urls import url

from failmap_admin.map.views import history, index, map_data, organization_report, stats, topfail

urlpatterns = [
    url(r'^admin/history', history, name='history'),
    url(r'^data/map/(?P<weeks_back>[0-9]{0,2})', map_data, name='map data'),
    url(r'^data/stats/', stats, name='stats'),
    url(r'^data/topfail/(?P<weeks_back>[0-9]{0,2})', topfail, name='top fail'),
    url(r'^data/report/(?P<organization_id>[0-9]{0,200})/$', organization_report,
        name='organization report'),
    url(r'^$', index, name='failmap'),
]
