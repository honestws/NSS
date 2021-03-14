from django.conf.urls import url
from .views import datasetrcv, downloaddataset

urlpatterns = [
    url(r'^downloaddataset/$', downloaddataset, name='downloaddataset'),
    url(r'^datasetrcv/$', datasetrcv, name='datasetrcv'),
]
