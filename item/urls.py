from django.conf.urls import include, url
from django.contrib import admin

from .views import HomeView, ItemDetail, submit_item, new_item, edit_item, delete_item, ItemDashboardView

urlpatterns = [
    url(r'^$', HomeView.as_view(), name='home'),
    url(r'^dashboard$', ItemDashboardView.as_view(), name='item-dashboard'),
    url(r'^item/new$', new_item, name='item-new'),
    url(r'^item/submit$', submit_item, name='item-submit'),
    url(r'^item/(?P<pk>\d+)$', ItemDetail.as_view(), name='item-detail'),
    url(r'^item/(?P<pk>\d+)/edit$', edit_item, name='item-edit'),
    url(r'^item/(?P<pk>\d+)/delete$', delete_item, name='item-delete'),
]
