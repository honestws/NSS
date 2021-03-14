from django.conf.urls import url

from .views import roomadd, roomedit, roomremove, filercv, downloadfile, doorreverse, parseconfig, roomrestart

urlpatterns = [
    url(r'^roomadd/$', roomadd, name='roomadd'),
    url(r'^roomedit/$', roomedit, name='roomedit'),
    url(r'^roomremove/$', roomremove, name='roomremove'),
    url(r'^roomrestart/$', roomrestart, name='roomrestart'),
    url(r'^filercv/$', filercv, name='filercv'),
    url(r'^downloadfile/$', downloadfile, name='downloadfile'),
    url(r'^doorreverse/$', doorreverse, name='doorreverse'),
    url(r'^parseconfig/$', parseconfig, name='parseconfig'),
]
