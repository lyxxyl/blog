"""blog URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.11/topics/http/urls/
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
from django.conf.urls import url
from django.contrib import admin
from app01 import views
from django.views.static import serve
from django.conf.urls import include
from blog import settings
from app01 import urls as app01_urls
urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'^login/', views.login),
    url(r'^index/', views.index),
    url(r'^logout/',views.logout),
    url(r'^pc-geetest/register/', views.pcgetcaptcha),



    url(r'upload/',views.upload),
    url(r'^register/', views.register),
    url(r'^media/(?P<path>.*)$',serve,{"document_root":settings.MEDIA_ROOT}),

    url(r'blog/',include(app01_urls)),

]
