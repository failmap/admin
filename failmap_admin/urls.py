"""admin URL Configuration.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.9/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf import settings
from django.conf.urls import include, url
from django.contrib import admin

# Django 1.10 http://stackoverflow.com/questions/38744285/
# django-urls-error-view-must-be-a-callable-or-a-list-tuple-in-the-case-of-includ#38744286

admin_urls = [
    url(r'^jet/', include('jet.urls', 'jet')),  # Django JET URLS
    url(r'^jet/dashboard/', include('jet.dashboard.urls',
                                    'jet-dashboard')),  # Django JET dashboard URLS
    url(r'^admin/', admin.site.urls),
    url(r'^admin/doc/', include('django.contrib.admindocs.urls')),
]
frontend_urls = [
    url(r'^', include('failmap_admin.map.urls')),
]

urlpatterns = frontend_urls.copy()

if settings.APPNAME == 'failmap-admin':
    urlpatterns += admin_urls

if settings.DEBUG:
    try:
        import debug_toolbar
        urlpatterns = [
            url(r'^__debug__/', include(debug_toolbar.urls)),
        ] + urlpatterns
    except ImportError:
        pass

# debugging
# urlpatterns += [url(r'^silk/', include('silk.urls', namespace='silk'))]

# Nested inlines don't work with Django Jet (yet).
# urlpatterns += [url(r'^_nested_admin/', include('nested_admin.urls'))]
