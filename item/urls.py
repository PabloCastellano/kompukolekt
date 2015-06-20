from django.conf.urls import include, url
from django.contrib import admin

from .views import HomeView, ItemDetail

urlpatterns = [
    url(r'^$', HomeView.as_view(), name='home'),
    url(r'^item/(?P<pk>\d+)$', ItemDetail.as_view(), name='item-detail'),
]
