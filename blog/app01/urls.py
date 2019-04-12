from django.conf.urls import url
from app01 import views


urlpatterns = [

    url(r'article_add/', views.article_add),
    url(r'updown/',views.up_down),
    url(r'comment/', views.comment),
    url(r'article/(\d+)/(\w+)/$', views.articledetail),
    url(r'(\w+)', views.home),

]
