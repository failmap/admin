# urls for scanners, maybe in their own url files
from django.conf.urls import url

from failmap_admin.map.views import (index, map_data, organization_report, stats, topfail,
                                     wanted_urls, topwin)

urlpatterns = [
    url(r'^data/map/(?P<weeks_back>[0-9]{0,2})', map_data, name='map data'),
    url(r'^data/stats/(?P<weeks_back>[0-9]{0,2})', stats, name='stats'),
    url(r'^data/topfail/(?P<weeks_back>[0-9]{0,2})', topfail, name='top fail'),
    url(r'^data/topwin/(?P<weeks_back>[0-9]{0,2})', topwin, name='top win'),
    url(r'^data/wanted/', wanted_urls, name='wanted urls'),
    url(r'^data/report/(?P<organization_id>[0-9]{0,200})/(?P<weeks_back>[0-9]{0,2})$',
        organization_report, name='organization report'),
    url(r'^$', index, name='failmap'),
]
